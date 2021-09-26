import io
import os
import json
import time
import shutil
import zipfile
import tarfile
import hashlib
import pathlib
import platform
import subprocess
import urllib.request

# Experimental
import concurrent.futures

# Local imports
from .common import DependencyError
from .common import HOME_DIR, PARTICLE_DEPS, CACHE_DIR, ARM_GCC_ARM, NEOPO_PARALLEL
from .common import extensionFiles, vscodeFiles, jsonFiles
from .common import particle_cli, running_on_windows
from .utility import write_file, write_executable
from .manifest import write_manifest, create_manifest, get_manifest_value

INSTALL_RECEIPT=".particle-install-receipt"
WORKBENCH_EXTENSION="particle.particle-vscode-core"

# Find the Workbench extension URL from the Visual Studio Marketplace
def get_extension_url(extension_name=WORKBENCH_EXTENSION):
    if extension_name == WORKBENCH_EXTENSION:
        print("Finding Workbench extension URL...")
    payload = '{"assetTypes":null,"filters":[{"criteria":[{"filterType":7,"value":"%s"}],"direction":2,"pageSize":100,"pageNumber":1,"sortBy":0,"sortOrder":0,"pagingToken":null}],"flags":103}' % extension_name

    request = urllib.request.Request(
        "https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery",
        method="POST",
        headers={
            "content-type": "application/json",
            "accept": "application/json;api-version=6.0-preview.1;excludeUrls=true",
        }, data=payload.encode("utf-8"))

    try:
        with urllib.request.urlopen(request) as response:
            content = response.read()
    except urllib.error.URLError as error:
        raise DependencyError("Failed to get extension URL!") from error

    # Parse response and extract the URL of the VSIX
    data = json.loads(content.decode("utf-8"))
    return data["results"][0]["extensions"][0]["versions"][0]["files"][-1]["source"]

# Download the the Workbench extension from the URL and return it in ZIP format
def get_extension(url):
    print("Downloading Workbench extension...")
    try:
        with urllib.request.urlopen(url) as response:
            content = response.read()
    except urllib.error.URLError as error:
        raise DependencyError("Failed to download extension!") from error
    return zipfile.ZipFile(io.BytesIO(content), "r")

# Load a file from a ZIP
def get_file(file, path):
    return file.read(path)

# Experimental
def parallel_handler(deps, update_manifest=True):
    if not deps or not isinstance(deps, list):
        return

    # Ensure that installation directory exists
    pathlib.Path(PARTICLE_DEPS).mkdir(parents=True, exist_ok=True)

    # Download dependencies in parallel
    with concurrent.futures.ThreadPoolExecutor() as exector:
        exector.map(parallel_download_dep, deps)

    # Update dependency manifest
    if update_manifest:
        create_manifest()
        for dep in deps:
            write_manifest(dep)

# Experimental
def parallel_download_dep(dep):
    try:
        with urllib.request.urlopen(dep["url"]) as response:
                content = response.read()
    except urllib.error.URLError as error:
        print("%s@%s: failed to download!" % (dep["name"], dep["version"]))
        return
    print("%s@%s: downloaded" % (dep["name"], dep["version"]))
    matched = hashlib.sha256(content).hexdigest() == dep["sha256"]
    if not matched:
        print("%s@%s: sha256 failed!" % (dep["name"], dep["version"]))
        return
    tarball = tarfile.open(fileobj=io.BytesIO(content), mode="r:gz")
    path = os.path.join(PARTICLE_DEPS, dep["name"], dep["version"])
    try:
        tarball.extractall(path)
        tarball.close()
        install_receipt(dep)
        # write_manifest(dep) #?
        print("%s@%s: extracted" % (dep["name"], dep["version"]))
    except PermissionError:
        print("%s@%s: failed to extract!" % (dep["name"], dep["version"]))

# Download the specified dependency
def download_dep(dep, update_manifest, check_hash):
    if not dep:
        return False
    if update_manifest:
        write_manifest(dep)

    name, version, url, sha256 = dep["name"], dep["version"], dep["url"], dep["sha256"]
    print("Downloading dependency %s@%s..." % (name, version))

    try:
        with urllib.request.urlopen(url) as response:
            content = response.read()
    except urllib.error.URLError as error:
        raise DependencyError("Failed to download dependency!") from error

    # Verify that the sha256 matches
    if check_hash:
        content_sha256 = hashlib.sha256(content).hexdigest()
        if content_sha256 != sha256:
            print("SHA256 mismatch!")
            print("Expected: %s" % sha256)
            print("Actual: %s" % content_sha256)
            print()
            print("Would you like to proceed anyway?")
            if input("(Y/N): ").lower() != "y":
                return False

    # Ensure that installation directory exists
    path = os.path.join(PARTICLE_DEPS, name, version)
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)

    # Write the archive to a file to save RAM
    archive = os.path.join(path, "%s-v%s.tar.gz" % (name, version))
    with open(archive, "wb") as gz_file:
        gz_file.write(content)

    # Extract the archive
    with tarfile.open(archive, "r:gz") as file:
        file.extractall(path)

    # Create install receipt so Workbench is happy
    install_receipt(dep)

    # Delete the temporary archive
    os.remove(archive)
    return True

# Create the install receipt for a dependency
def install_receipt(dep):
    name, version = dep["name"], dep["version"]
    path = os.path.join(PARTICLE_DEPS, name, version)
    installed = int(time.time() * 1000)
    receipt = {"name": name, "version": version, "installed": installed}
    with open(os.path.join(path, INSTALL_RECEIPT), "w") as file:
        json.dump(receipt, file, indent=4)

# Download extension manifest and simple dependencies
def get_deps():
    # Ensure that cache directory exists
    pathlib.Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)

    # Download and extract VSIX, and obtain dependency manifest
    extension = get_extension(get_extension_url())
    pathlib.Path(vscodeFiles["dir"]).mkdir(parents=True, exist_ok=True)
    manifest = get_file(extension, extensionFiles["manifest"])

    # Attempt to pull particle-cli executable from VSIX
    try:
        os_platform = platform.system().lower()
        os_arch = platform.machine().lower(
        ) if running_on_windows else "amd64" if platform.machine() == "x86_64" else "arm"
        particle_bin = os.path.basename(particle_cli)
        particle = get_file(
            extension, "/".join([extensionFiles["bin"], os_platform, os_arch, particle_bin]))
        write_executable(particle, particle_cli)
    except KeyError as error:
        raise DependencyError(
            "Failed to download particle executable from extension!") from error

    # Create launch.json and settings.json project template files
    launch = get_file(extension, extensionFiles["launch"])
    settings = get_file(extension, extensionFiles["settings"])
    write_file(launch, vscodeFiles["launch"], "wb")
    write_file(settings, vscodeFiles["settings"], "wb")

    # Ensure that manifest file exists and return manifest content
    create_manifest()
    return json.loads(manifest.decode("utf-8"))

# Write an object to JSON cache file
def write_json_caches(data, keys):
    for key in keys:
        with open(jsonFiles[key], "w") as file:
            key_data = data[key]
            json.dump(key_data, file, indent=4)

# Install or update neopo dependencies (not the neopo script)
def install_or_update(install, force, skip_deps):
    print("Installing neopo..." if install else "Updating dependencies...")

    # Dependencies we wish to install and caches we will create
    dependencies = ["compilers", "tools", "scripts", "debuggers"]
    caches = ["firmware", "platforms", "toolchains", "compilers", "tools", "scripts", "debuggers"]

    # Download dependency data and create list of installables
    data = get_deps()
    dep_json = [data["firmware"][0]]

    # Append dependencies to list
    system = platform.system().lower()
    dep_json.extend([data[dep][system]["x64"][0] for dep in dependencies])

    # Use my precompiled gcc-arm for ARM
    install_platform = platform.machine()
    if install_platform != "x86_64":
        for dep in dep_json:
            if dep["name"] == "gcc-arm":
                fix_gcc_arm(dep)
                break

    # Update JSON cache files
    write_json_caches(data, caches)

    # Skip installation of dependencies (for containers)
    if skip_deps:
        for dep in dep_json:
            write_manifest(dep)
        print("Skipped installation of all dependencies.")
        return

    # Experimental (parallel downloading to save time)
    # Currently opt-in
    if NEOPO_PARALLEL:
        deps_to_install = []
        for dep in dep_json:
            install_path = os.path.join(PARTICLE_DEPS, dep["name"], dep["version"])
            installed = os.path.isdir(install_path)
            if force or not installed: deps_to_install.append(dep)
        # Download needed deps in parallel
        parallel_handler(deps_to_install)
        return

    # Either install or update
    if install:
        skipped_deps = []
        for dep in dep_json:
            # Install dependency if not currently installed, or forced, otherwise skip
            install_path = os.path.join(PARTICLE_DEPS, dep["name"], dep["version"])
            installed = os.path.isdir(install_path)
            # Check for install receipt here? (Silent fix for older neopo installs)
            receipt = os.path.isfile(os.path.join(install_path, INSTALL_RECEIPT))

            if not installed or force:
                download_dep(dep, True, True)
            else:
                skipped_deps.append(dep)
                if not receipt:
                    install_receipt(dep)

        # Fix buildtools and openocd for aarch64
        if install_platform == "aarch64":
            buildtools_version = [dep["version"] for dep in dep_json if dep["name"] == "buildtools"][0]
            fix_buildtools(buildtools_version)
            openocd_version = [dep["version"] for dep in dep_json if dep["name"] == "openocd"][0]
            fix_openocd(openocd_version)

        # Put skippedDeps in manifest.json
        for dep in skipped_deps:
            write_manifest(dep)

        # Notify user of dependencies skipped to save bandwidth and time
        if skipped_deps:
            print()
            print("Skipped previously installed dependencies:")
            print(*["%s@%s" % (dep["name"], dep["version"])
                    for dep in skipped_deps], sep=", ")
        print()

    else:
        # Only install a dependency if newer
        for dep in dep_json:
            new = int(dep["version"].split("-")[0].replace(".", ""))
            old = int(get_manifest_value(dep["name"]).split("-")[0].replace(".", ""))
            if new > old:
                download_dep(dep, True, True)
        print("Dependencies are up to date!")

# Try to download given firmware
def attempt_download(firmware):
    try:
        download_dep(firmware, False, True)
        return
    except urllib.error.URLError as error:
        raise DependencyError("DeviceOS version %s not found!" %
                              firmware["version"]) from error

# Patch gcc-arm dependency dict for armv7l and aarch64
def fix_gcc_arm(dep):
    install_platform = platform.machine()
    if not install_platform in ARM_GCC_ARM.keys():
        return
    dep["url"] = ARM_GCC_ARM[install_platform][dep["version"]]["url"]
    dep["sha256"] = ARM_GCC_ARM[install_platform][dep["version"]]["sha256"]

# Fix buildtools dependency on aarch64 so Workbench will function (requires dfu-util)
def fix_buildtools(version):
    buildtools = os.path.join(PARTICLE_DEPS, "buildtools")
    latest = os.path.join(buildtools, version)
    binaries = ["make", "dfu-util", "dfu-prefix", "dfu-suffix"]

    # Replace local binaries with ones found in path
    for command in binaries:
        file = os.path.join(latest, command)
        os.remove(file)
        real = shutil.which(command)
        shutil.copy(real, file)

# Fix openocd dependency on aarch64 so Particle Debugger will function (requires openocd-git)
def fix_openocd(version):
    openocd = os.path.join(PARTICLE_DEPS, "openocd")
    latest = os.path.join(openocd, version, "bin")
    binaries = ["_openocd", "openocd"]

    # Replace local binaries with openocd in path
    real_openocd = shutil.which("openocd")
    if real_openocd:
        for command in binaries:
            file = os.path.join(latest, command)
            os.remove(file)
            shutil.copy(real_openocd, file)

# Attempt to install Particle extensions in VSCode
def workbench_install(args):
    if shutil.which("code"):
        try:
            process = ["code", "--install-extension", "particle.particle-vscode-pack"]
            subprocess.run(process, check=True)
        except subprocess.CalledProcessError as error:
            raise DependencyError("Failed to install Workbench extensions!") from error
    else:
        raise DependencyError("The `code` command was not found.\nPlease ensure that Visual Studio Code is installed.")

    # Locate VSCode extensions
    extensions = os.path.join(HOME_DIR, ".vscode/extensions")
    _, exts, _ = next(os.walk(extensions))

    # Patch Workbench so correct particle-cli is used
    setup_workbench_arm(extensions, exts)

    # Attempt to get Debugger working in Workbench (aarch64) [openocd-git is installed in setup_command()]
    setup_debugger_arm(extensions, exts)

# Apply necessary tweaks to get Particle Workbench working on aarch64
def setup_workbench_arm(extensions, exts):
    if platform.machine() != "aarch64":
        return

    # Replace CLI used in Workbench with working CLI (aarch64)
    particle_ext = [ext for ext in exts if ext.startswith("particle.particle-vscode-core")][0]
    cli_bin = os.path.join(extensions, particle_ext, "src/cli/bin/linux/amd64/particle")
    os.remove(cli_bin)
    shutil.copy(particle_cli, cli_bin)

# Apply necessary tweaks to get Particle Debugger working on aarch64
def setup_debugger_arm(extensions, exts):
    if platform.machine() != "aarch64":
        return

    try:
        node_version = subprocess.run(["node", "-v"], stdout=subprocess.PIPE, check=True)
        node_version = node_version.stdout.decode("utf-8").rstrip()[1:]
        electron_version = "11.0.3"
    except subprocess.CalledProcessError as error:
        raise DependencyError("Failed to run `node`!\nPlease ensure that you have nodejs installed.") from error

    # Obtain serial-port-build.sh
    cortex_debug = [ext for ext in exts if ext.startswith("marus25.cortex-debug")][0]
    serial_port_build = os.path.join(extensions, cortex_debug, "serial-port-build.sh")

    # Read, modify, and write
    content = []
    with open(serial_port_build) as original:
        content = original.readlines()
    for index, line in enumerate(content):
        if line.lstrip().startswith("generate $version x64 linux"):
            content[index] = content[index].replace("x64", "arm64")
            break
    with open(serial_port_build, "w") as modified:
        modified.writelines(content)

    # Execute serial-port-build.sh
    try:
        os.chdir(os.path.join(extensions, cortex_debug))
        process = [serial_port_build, electron_version, node_version]
        subprocess.run(process, check=True)
    except subprocess.CalledProcessError as error:
        raise DependencyError("Problem with serial-port-build.sh!") from error

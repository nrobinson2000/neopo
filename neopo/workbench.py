import io
import os
import json
import shutil
import zipfile
import tarfile
import hashlib
import pathlib
import platform
import subprocess
import urllib.request

# Local imports
from .common import DependencyError
from .common import PARTICLE_DEPS, CACHE_DIR, ARM_GCC_ARM
from .common import extensionFiles, vscodeFiles, jsonFiles
from .common import particle_cli, running_on_windows
from .utility import write_file, write_executable
from .manifest import write_manifest, create_manifest, get_manifest_value

# Find the Workbench extension URL from the Visual Studio Marketplace
def get_extension_url():
    print("Finding Workbench extension URL...")
    payload = '{"assetTypes":null,"filters":[{"criteria":[{"filterType":7,"value":"particle.particle-vscode-core"}],"direction":2,"pageSize":100,"pageNumber":1,"sortBy":0,"sortOrder":0,"pagingToken":null}],"flags":103}'

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

    # Delete the temporary archive
    os.remove(archive)
    return True

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
def install_or_update(install, force):
    print("Installing neopo..." if install else "Updating dependencies...")

    # Dependencies we wish to install and caches we will create
    dependencies = ["compilers", "tools", "scripts", "debuggers"]
    caches = ["firmware", "platforms", "toolchains", "compilers"]

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
                dep["url"] = ARM_GCC_ARM[install_platform][dep["version"]]["url"]
                dep["sha256"] = ARM_GCC_ARM[install_platform][dep["version"]]["sha256"]
                break

    # Update JSON cache files
    write_json_caches(data, caches)

    # Either install or update
    if install:
        skipped_deps = []
        for dep in dep_json:
            # Install dependency if not currently installed, or forced, otherwise skip
            installed = os.path.isdir(os.path.join(
                PARTICLE_DEPS, dep["name"], dep["version"]))
            if not installed or force:
                download_dep(dep, True, True)
            else:
                skipped_deps.append(dep)

        # Fix buildtools for ARM
        if install_platform != "x86_64":
            version = [dep["version"] for dep in dep_json if dep["name"] == "buildtools"]
            fix_buildtools(version)

        # Put skippedDeps in manifest.json. Fixes: nrobinson2000/neopo/issues/8
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


# Fix buildtools dependency on aarch64 so Workbench will function
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

    # Attempt to patch Workbench so that the popup asking to reinstall dependencies never shows
    extensions = os.path.join(os.path.expanduser("~"), ".vscode/extensions")
    _, exts, _ = next(os.walk(extensions))
    particle_ext = [ext for ext in exts if ext.startswith("particle.particle-vscode-core")][0]
    env_setup = os.path.join(extensions, particle_ext, "src/env-setup.js")
    line_to_insert = "\t\treturn showWarningMessage('Particle dependencies managed by neopo.xyz.'); // Neopo fix\n"

    content = []
    with open(env_setup) as original:
        content = original.readlines()

    for index, line in enumerate(content):
        if line == line_to_insert:
            break
        line_s = line.lstrip()
        if line_s.startswith("const shouldInstall"):
            content.insert(index, line_to_insert)
            break

    with open(env_setup, "w") as modified:
        modified.writelines(content)

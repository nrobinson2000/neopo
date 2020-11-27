import io
import os
import json
import zipfile
import tarfile
import hashlib
import pathlib
import platform
import urllib.request


# Local imports
from .common import DependencyError
from .common import PARTICLE_DEPS, CACHE_DIR, ARM_GCC_ARM
from .common import extensionFiles, vscodeFiles, jsonFiles
from .common import particle_cli, running_on_windows

from .utility import writeFile, writeExecutable

from .manifest import writeManifest, createManifest, loadManifest

# Find the Workbench extension URL from the Visual Studio Marketplace
def getExtensionURL():
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
    except urllib.error.URLError as e:
        raise DependencyError("Failed to get extension URL!") from e

    # Parse response and extract the URL of the VSIX
    data = json.loads(content.decode("utf-8"))
    return data["results"][0]["extensions"][0]["versions"][0]["files"][-1]["source"]

# Download the the Workbench extension from the URL and return it in ZIP format
def getExtension(url):
    print("Downloading Workbench extension...")
    try:
        with urllib.request.urlopen(url) as response:
            content = response.read()
    except urllib.error.URLError as e:
        raise DependencyError("Failed to download extension!") from e
    return zipfile.ZipFile(io.BytesIO(content), "r")

# Load a file from a ZIP
def getFile(file, path):
    return file.read(path)

# Download the specified dependency
def downloadDep(dep, updateManifest, checkHash):
    if not dep:
        return False
    if updateManifest:
        writeManifest(dep)

    name, version, url, sha256 = dep["name"], dep["version"], dep["url"], dep["sha256"]
    print("Downloading dependency %s@%s..." % (name, version))

    try:
        with urllib.request.urlopen(url) as response:
            content = response.read()
    except urllib.error.URLError as e:
        raise DependencyError("Failed to download dependency!") from e

    # Verify that the sha256 matches
    if checkHash:
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
    fileName = os.path.join(path, "%s-v%s.tar.gz" % (name, version))
    with open(fileName, "wb") as gzFile:
        gzFile.write(content)

    # Extract the archive
    with tarfile.open(fileName, "r:gz") as file:
        file.extractall(path)

    # Delete the temporary archive
    os.remove(fileName)
    return True

# Download extension manifest and simple dependencies
def getDeps():
    # Ensure that cache directory exists
    pathlib.Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)

    # Download and extract VSIX, and obtain dependency manifest
    extension = getExtension(getExtensionURL())
    pathlib.Path(vscodeFiles["dir"]).mkdir(parents=True, exist_ok=True)
    manifest = getFile(extension, extensionFiles["manifest"])

    # Attempt to pull particle-cli executable from VSIX
    try:
        osPlatform = platform.system().lower()
        osArch = platform.machine().lower() if running_on_windows else "amd64" if platform.machine() == "x86_64" else "arm"
        particle_bin = os.path.basename(particle_cli)
        particle = getFile(extension, "/".join([extensionFiles["bin"], osPlatform, osArch, particle_bin]))
        writeExecutable(particle, particle_cli)
    except KeyError as e:
        raise DependencyError("Failed to download particle executable from extension!") from e

    # Create launch.json and settings.json project template files
    launch = getFile(extension, extensionFiles["launch"])
    settings = getFile(extension, extensionFiles["settings"])
    writeFile(launch, vscodeFiles["launch"], "wb")
    writeFile(settings, vscodeFiles["settings"], "wb")

    # Ensure that manifest file exists and return manifest content
    createManifest()
    return json.loads(manifest.decode("utf-8"))

# Write an object to JSON cache file
def writeJSONcaches(data, keys):
    for key in keys:
        with open(jsonFiles[key], "w") as file:
            keyData = data[key]
            json.dump(keyData, file, indent=4)

# Install or update neopo dependencies (not the neopo script)
def installOrUpdate(install, force):
    print("Installing neopo..." if install else "Updating dependencies...")

    # Dependencies we wish to install and caches we will create
    dependencies = ["compilers", "tools", "scripts", "debuggers"]
    caches = ["firmware", "platforms", "toolchains", "compilers"]

    # Download dependency data and create list of installables
    data = getDeps()
    depJSON = [data["firmware"][0]]

    # Append dependencies to list
    system = platform.system().lower()
    depJSON.extend([data[dep][system]["x64"][0] for dep in dependencies])

    # Use my precompiled gcc-arm for ARM
    installPlatform = platform.machine()
    if installPlatform != "x86_64":
        for dep in depJSON:
            if dep["name"] == "gcc-arm":
                dep["url"] = ARM_GCC_ARM[installPlatform][dep["version"]]["url"]
                dep["sha256"] = ARM_GCC_ARM[installPlatform][dep["version"]]["sha256"]
                break

    # Update JSON cache files
    writeJSONcaches(data, caches)

    # Either install or update
    if install:
        skippedDeps = []
        for dep in depJSON:
            # Install dependency if not currently installed, or forced, otherwise skip
            installed = os.path.isdir(os.path.join(PARTICLE_DEPS, dep["name"], dep["version"]))
            if not installed or force:
                downloadDep(dep, True, True)
            else:
                skippedDeps.append(dep)

        # Put skippedDeps in manifest.json. Fixes: nrobinson2000/neopo/issues/8
        for dep in skippedDeps:
            writeManifest(dep)

        # Notify user of dependencies skipped to save bandwidth and time
        if skippedDeps:
            print()
            print("Skipped previously installed dependencies:")
            print(*["%s@%s" % (dep["name"], dep["version"]) for dep in skippedDeps], sep=", ")
        print()

    else:
        # Load in dependency manifest, and only install a dependency if newer
        manifest = loadManifest()
        for dep in depJSON:
            new = int(dep["version"].split("-")[0].replace(".", ""))
            old = int(manifest[dep["name"]].split("-")[0].replace(".", ""))
            if new > old:
                downloadDep(dep, True, True)
        print("Dependencies are up to date!")

# Try to download given firmware
def attemptDownload(firmware):
    try:
        downloadDep(firmware, False, True)
        return
    except urllib.error.URLError as e:
        raise DependencyError("DeviceOS version %s not found!" % firmware["version"]) from e

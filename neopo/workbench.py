import io
import os
import json
import stat
import zipfile
import tarfile
import hashlib
import pathlib
import platform
import urllib.request


# Local imports
from common import DependencyError
from common import PARTICLE_DEPS, CACHE_DIR
from common import extensionFiles, vscodeFiles
from common import particle_cli, running_on_windows

# from manifest import 

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
    except urllib.error.URLError:
        raise DependencyError("Failed to get extension URL!")
    
    # Parse response and extract the URL of the VSIX
    data = json.loads(content.decode("utf-8"))
    return data["results"][0]["extensions"][0]["versions"][0]["files"][-1]["source"]

# Download the the Workbench extension from the URL and return it in ZIP format
def getExtension(url):
    print("Downloading Workbench extension...")
    try:
        with urllib.request.urlopen(url) as response:
            content = response.read()
    except urllib.error.URLError:
        raise DependencyError("Failed to download extension!")
    return zipfile.ZipFile(io.BytesIO(content), "r")




# Load a file from a ZIP
def getFile(file, path):
    return file.read(path)

# Download the specified dependency
def downloadDep(dep, updateManifest, checkHash):
    if not dep: return False
    if updateManifest: writeManifest(dep)

    name, version, url, sha256 = dep["name"], dep["version"], dep["url"], dep["sha256"]
    print("Downloading dependency %s@%s..." % (name, version))

    try:
        with urllib.request.urlopen(url) as response:
            content = response.read()
    except urllib.error.URLError:
        raise DependencyError("Failed to download dependency!")

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

# Write data to a file
def writeFile(content, path, mode):
    with open(path, mode) as file:
        file.write(content)

# Write an executable dependency to a file
def writeExecutable(content, path):
    with open(path, "wb") as file:
        file.write(content)
        st = os.stat(file.name)
        os.chmod(file.name, st.st_mode | stat.S_IEXEC)

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
    except KeyError:
        raise DependencyError("Failed to download particle executable from extension!")
    
    # Create launch.json and settings.json project template files
    launch = getFile(extension, extensionFiles["launch"])
    settings = getFile(extension, extensionFiles["settings"])
    writeFile(launch, vscodeFiles["launch"], "wb")
    writeFile(settings, vscodeFiles["settings"], "wb")

    # Ensure that manifest file exists and return manifest content
    createManifest()
    return json.loads(manifest.decode("utf-8"))
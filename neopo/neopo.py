#!/usr/bin/env python3

# neopo: A lightweight solution for local Particle development.
# Copyright (c) 2020 Nathan Robinson.

import io
import os
import sys
import json
import stat
import shutil
import zipfile
import tarfile
import hashlib
import pathlib
import platform
import traceback
import subprocess
import urllib.request

# Primary directories: dependencies, caches, scripts
PARTICLE_DEPS = os.path.join(os.path.expanduser("~"), ".particle", "toolchains")
NEOPO_DEPS = os.path.join(os.path.expanduser("~"), ".neopo")
CACHE_DIR = os.path.join(NEOPO_DEPS, "cache")
SCRIPTS_DIR = os.path.join(NEOPO_DEPS, "scripts")

# Precompiled gcc-arm for ARM platforms
ARM_GCC_ARM = {
    "aarch64": {
        "5.3.1": {
            "url": "https://github.com/nrobinson2000/neopo/releases/download/0.0.3/gcc-arm-v5.3.1-aarch64.tar.gz",
            "sha256": "06a392fb34103b0202cee65a7cae0e1a02b3e6e775c3d0d4b2111c631efbc303"
        },
        "9.2.1": {
            "url": "https://github.com/nrobinson2000/neopo/releases/download/0.0.3/gcc-arm-v9.2.1-aarch64.tar.gz",
            "sha256": "1530a1ebc43118cb81650af8621f6529df20b300e6c9d5e38aeb1ccc717c6a9e"
        }
    },
    "armv7l": {
        "5.3.1": {
            "url": "https://github.com/nrobinson2000/neopo/releases/download/0.0.1/gcc-arm-v5.3.1-raspberry-pi.tar.gz",
            "sha256": "dc5570abe2b4742a70dba06f59bf18bd1354107a879ce68029da29539113e3b0"
        },
        "9.2.1": {
            "url": "https://github.com/nrobinson2000/neopo/releases/download/0.0.2/gcc-arm-v9.2.1-raspberry-pi.tar.gz",
            "sha256": "d963b551122d57057aaacc82e61ca6a05a524df14bb9fe28ca55b67494639fce"
        }
    }
}

# Windows tricks
running_on_windows = platform.system() == "Windows"
particle_cli = os.path.join(NEOPO_DEPS, "particle.exe") if running_on_windows else os.path.join(NEOPO_DEPS, "particle")

# JSON cache files
jsonFiles = {
    "firmware": os.path.join(CACHE_DIR, "firmware.json"),
    "toolchains": os.path.join(CACHE_DIR, "toolchains.json"),
    "platforms": os.path.join(CACHE_DIR, "platforms.json"),
    "compilers": os.path.join(CACHE_DIR, "compilers.json"),
    "manifest": os.path.join(CACHE_DIR, "manifest.json")
}

# Workbench template files
vscodeFiles = {
    "dir": os.path.join(NEOPO_DEPS, "vscode"),
    "launch": os.path.join(NEOPO_DEPS, "vscode", "launch.json"),
    "settings": os.path.join(NEOPO_DEPS, "vscode", "settings.json")
}

# Files inside VSIX
extensionFiles = {
    "bin": "extension/src/cli/bin",
    "manifest": "extension/src/compiler/manifest.json",
    "launch": "extension/src/cli/vscode/launch.json",
    "settings": "extension/src/cli/vscode/settings.json"
}

# Files inside project
projectFiles = {
    "launch": os.path.join(".vscode", "launch.json"),
    "settings": os.path.join(".vscode", "settings.json"),
    "properties": "project.properties"
}

# Use this as .travis.yml when creating project repos
TRAVIS_YML = """# Build a neopo project with Travis CI
os: linux
language: shell
install:
  - bash <(curl -sL https://raw.githubusercontent.com/nrobinson2000/neopo/master/install.sh)
script:
  - neopo libs
  - neopo build
cache:
  directories:
    - $HOME/.particle
    - $HOME/.neopo
"""

# Custom errors
class UserError(RuntimeError):
    pass
class DependencyError(RuntimeError):
    pass
class ProcessError(RuntimeError):
    pass
class ProjectError(RuntimeError):
    pass

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
    # Ensure that cache and scripts directories exist
    pathlib.Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)
    pathlib.Path(SCRIPTS_DIR).mkdir(parents=True, exist_ok=True)

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

# Update the manifest JSON file
def writeManifest(dep):
    with open(jsonFiles["manifest"], "r+") as file:
        try:
            manifest = json.load(file)
        except json.decoder.JSONDecodeError:
            manifest = {}

        manifest[dep["name"]] = dep["version"]
        file.seek(0)
        json.dump(manifest, file, indent=4)
        file.truncate()

# Create the manifest file
def createManifest():
    if not os.path.isfile(jsonFiles["manifest"]):
        open(jsonFiles["manifest"], "w")

# Load settings from the dependency mainfest JSON file
def loadManifest(tupleOrDict):
    with open(jsonFiles["manifest"], "r") as file:
        try:
            data = json.load(file)
        except json.decoder.JSONDecodeError:
            return None
        if tupleOrDict:
            return (
                data["gcc-arm"],
                data["buildscripts"],
                data["buildtools"],
                data["deviceOS"]
            )
        else:
            return {
                "gcc-arm": data["gcc-arm"],
                "buildscripts": data["buildscripts"],
                "buildtools": data["buildtools"],
                "deviceOS": data["deviceOS"],
                "openocd": data["openocd"]
            }

# Write an object to JSON cache file
def writeJSONcache(data, key):
    with open(jsonFiles[key], "w") as file:
        keyData = data[key]
        json.dump(keyData, file, indent=4)

# Try to download given firmware
def attemptDownload(firmware):
    try:
        downloadDep(firmware, False, True)
        return
    except urllib.error.URLError:
        raise DependencyError("DeviceOS version %s not found!" % firmware["version"])

# Attempt to download deviceOS version not specified in manifest (experimental)
def downloadUnlisted(version):
    # Minimum information for a firmware dependency
    firmware = {"name": "deviceOS", "version": version,
        "url": "https://binaries.particle.io/device-os/v%s.tar.gz" % version}

    try:
        # Attempt to download from Particle's download mirror
        print("Trying binaries.particle.io/device-os...")
        attemptDownload(firmware)
    except DependencyError:
        # Try to download from github
        firmware["url"] = "https://github.com/particle-iot/device-os/archive/v%s.tar.gz" % version
        print("Trying github.com/particle-iot/device-os...")
        attemptDownload(firmware)
    
# Wrapper for [download-unlisted]
def downloadUnlisted_command(args):
    try:
        downloadUnlisted(args[2])
    except IndexError:
        raise UserError("You must specify a deviceOS version!")

# Download a specific deviceOS version
def downloadFirmware(version):
    if not downloadDep(getFirmwareData(version), False, True):
        print("Could not download deviceOS version %s!" % version)

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
    for dep in dependencies: depJSON.append(data[dep][system]["x64"][0])

    # Use my precompiled gcc-arm for ARM
    installPlatform = platform.machine()
    if installPlatform != "x86_64":
        for dep in depJSON:
            if dep["name"] == "gcc-arm":
                dep["url"] = ARM_GCC_ARM[installPlatform][dep["version"]]["url"]
                dep["sha256"] = ARM_GCC_ARM[installPlatform][dep["version"]]["sha256"]
                break
    
    # Update JSON cache files
    for key in caches: writeJSONcache(data, key)

    # Either install or update
    if install:
        skippedDeps = []
        for dep in depJSON:
            # Install dependency if not currently installed, or forced, otherwise skip
            installed = os.path.isdir(os.path.join(PARTICLE_DEPS, dep["name"], dep["version"]))
            downloadDep(dep, True, True) if not installed or force else skippedDeps.append(dep)

        # Put skippedDeps in manifest.json. Fixes: nrobinson2000/neopo/issues/8
        for dep in skippedDeps: writeManifest(dep)

        # Notify user of dependencies skipped to save bandwidth and time
        if skippedDeps:
            print()
            print("Skipped previously installed dependencies:")
            print(*["%s@%s" % (dep["name"], dep["version"]) for dep in skippedDeps], sep=", ")
        
        print()
        
    else:
        # Load in dependency manifest, and only install a dependency if newer
        manifest = loadManifest(False)
        for dep in depJSON:
            new = int(dep["version"].split("-")[0].replace(".", ""))
            old = int(manifest[dep["name"]].split("-")[0].replace(".", ""))
            if new > old: downloadDep(dep, True, True)
        print("Dependencies are up to date!")

# Delete the neopo script from the system
#TODO: Enforce package manager instead
def uninstall_command(args):
    execpath = args[0]
    print("Are you sure you want to uninstall neopo at %s?" % execpath)

    # Ask for confirmation
    if input("(Y/N): ").lower() != "y":
        raise UserError("Aborted.")
    try:
        #TODO: the ~/.neopo directory should get deleted too
        os.remove(execpath)
        print("Uninstalled neopo.")
        print("Note: The .particle directory may still exist (remove it with `rm -rf ~/.particle`)")
    except PermissionError:
        raise ProcessError("Could not delete %s\nTry running with sudo." % execpath)

# Create a Particle project and copy in Workbench settings
def create_project(path, name):
    projectPath = os.path.join(path, name)
    # Use particle-cli to create the project
    returncode = subprocess.run(
        [particle_cli, "project", "create", path, "--name", name],
        shell=running_on_windows).returncode
    if returncode:
        raise ProcessError("Failed with code %s" % returncode)

    # If git is installed, initialize project as git repo
    if shutil.which("git"):
        subprocess.run(["git", "init", projectPath])
        # Add .travis.yml to project
        writeFile(TRAVIS_YML, os.path.join(projectPath, ".travis.yml"), "w")
        # Add .gitignore to project
        writeFile("target", os.path.join(projectPath, ".gitignore"), "w")

    # Add buttons to README.md
    travisButton = "[![](https://api.travis-ci.org/yourUser/yourRepo.svg?branch=master)](https://travis-ci.org/yourUser/yourRepo)"
    neopoButton = "[![](https://img.shields.io/badge/built_with-neopo-informational)](https://neopo.xyz)"
    readmePath = os.path.join(projectPath, "README.md")
    with open(readmePath, "r") as file:
        readme = file.readlines()
        readme.insert(0, "\n")
        readme.insert(0, neopoButton + "\n")
        readme.insert(0, travisButton + "\n")
    with open(readmePath, "w") as file:
        file.writelines(readme)

    # Change name/src/name.ino to name/src/name.cpp
    # Add #include "Particle.h"
    include = '#include "Particle.h"\n'
    src = os.path.join(projectPath, "src", "%s.ino" % name)
    dst = os.path.join(projectPath, "src", "%s.cpp" % name)
    shutil.move(src, dst)
    with open(dst, "r") as original:
        data = original.read()
    with open(dst, "w") as modified:
        modified.write(include + data)

    #TODO: Default device in manifest.json
    device = "argon"
    version = loadManifest(False)["deviceOS"]
    configure_project(projectPath, device, version)

# Get a deviceOS dependency from a version
def getFirmwareData(version):
    with open(jsonFiles["firmware"], "r") as firmwareFile:
        for entry in json.load(firmwareFile):
            if entry["version"] == version:
                return entry
        return False

# Convert between platform IDs and device names
def platformConvert(data, key1, key2):
    with open(jsonFiles["platforms"], "r") as platformFile:
        for platform in json.load(platformFile):
            if platform[key1] == data:
                return platform[key2]
        return False

# List the supported platform IDs for a given version
def getSupportedPlatforms(version):
    with open(jsonFiles["toolchains"], "r") as toolchainsFile:
        for toolchain in json.load(toolchainsFile):
            if toolchain["firmware"] == "deviceOS@%s" % version:
                return toolchain["platforms"]
        return False

# Verify platform and deviceOS version and download deviceOS dependency if required
def checkFirmwareVersion(platform, version):
    firmware = getFirmwareData(version)
    platformID = platformConvert(platform, "name", "id")

    # Check that platform and firmware are compatible
    if not platformID:
        print("Invalid platform %s!" % platform)
        return False
    if not firmware:
        print("Invalid deviceOS version %s!" % version)
        return False
    if not platformID in getSupportedPlatforms(version):
        print("Platform %s is not supported in deviceOS version %s!" % (platform, version))
        return False

    # If required firmware is not installed, download it
    path = os.path.join(PARTICLE_DEPS, "deviceOS", version)
    os.path.isdir(path) or downloadDep(firmware, False, True)
    return True

# Modify Workbench settings in a project (platform, firmwareVersion)
def configure_project(projectPath, platform, firmwareVersion):
    # Ensure that firware is compatible with platform
    # Download requested version if required
    if not checkFirmwareVersion(platform, firmwareVersion):
        raise ProjectError("Firmware related error!")
    
    # Ensure that a valid project was selected
    if not os.path.isfile(os.path.join(projectPath, projectFiles["properties"])):
        raise ProjectError("%s is not a Particle project!" % projectPath)
    
    # Upgrade a CLI project to Workbench format if required
    if not os.path.isfile(os.path.join(projectPath, projectFiles["settings"])):
        pathlib.Path(os.path.join(projectPath, ".vscode")).mkdir(parents=True, exist_ok=True)
        shutil.copyfile(vscodeFiles["launch"], os.path.join(projectPath, projectFiles["launch"]))
        shutil.copyfile(vscodeFiles["settings"], os.path.join(projectPath, projectFiles["settings"]))

    # Apply configuration to project
    writeSettings(projectPath, platform, firmwareVersion)
    print("Configured project %s:" % projectPath)
    print("\tparticle.targetPlatform: %s" % platform)
    print("\tparticle.firmwareVersion: %s" % firmwareVersion)

# Load Workbench settings from a project
def getSettings(projectPath):
    with open(os.path.join(projectPath, projectFiles["settings"]), "r") as settings:
        data = json.loads(settings.read())
        return (data["particle.targetPlatform"], data["particle.firmwareVersion"])

# Update Workbench settings in a project
def writeSettings(projectPath, platform, version):
    with open(os.path.join(projectPath, projectFiles["settings"]), "r+") as settings:
        data = json.loads(settings.read())
        data["particle.targetPlatform"] = platform
        data["particle.firmwareVersion"] = version
        settings.seek(0)
        json.dump(data, settings, indent=4)
        settings.truncate()

# Print help information directly from Makefile
def build_help():
    build_project(None, None, True, 0)

# Create the path string for a given deviceOS version
def getFirmwarePath(version):
    deviceOSPath = os.path.join(PARTICLE_DEPS, "deviceOS", version)
    legacy = os.path.join(deviceOSPath, "firmware-%s" % version)
    github = os.path.join(deviceOSPath, "device-os-%s" % version)
    return legacy if os.path.isdir(legacy) else github if os.path.isdir(github) else deviceOSPath

# For a given firmware version return the appropriate compiler version
def getCompiler(firmwareVersion):
    with open(jsonFiles["toolchains"]) as file:
        data = json.load(file)
        for toolchain in data:
            if toolchain["firmware"] == "deviceOS@%s" % firmwareVersion:
                return toolchain["compilers"].split("@")[1]
        raise DependencyError("Invalid firmware version!")

# Get a gcc-arm dependency from a version
def getCompilerData(version):
    with open(jsonFiles["compilers"], "r") as compilersFile:
        data = json.load(compilersFile)
        system = platform.system().lower()
        compilers = data[system]["x64"]

        installPlatform = platform.machine()
        for compiler in compilers:
            if compiler["version"] == version:
                if installPlatform != "x86_64":
                    compiler["url"] = ARM_GCC_ARM[installPlatform][version]["url"]
                    compiler["sha256"] = ARM_GCC_ARM[installPlatform][version]["sha256"]
                return compiler
        return False

# Ensure that the requested compiler version is installed
def checkCompiler(compilerVersion):
    # If required compiler is not installed, download it
    path = os.path.join(PARTICLE_DEPS, "gcc-arm", compilerVersion)
    os.path.isdir(path) or downloadDep(getCompilerData(compilerVersion), False, True)
    return True

# Create a dictionary from a .properties file
def loadProperties(propertiesPath):
    properties = {}
    with open(propertiesPath, "r") as file:
        for line in file.readlines():
            tokens = line.split("=", 1)
            key = tokens[0]
            value = tokens[1].strip()
            properties[key] = value
    return properties

# Download a library using particle-cli
def downloadLibrary(library, version):
    process = [particle_cli, "library", "copy", "%s@%s" % (library, version)]
    returncode = subprocess.run(process, shell=running_on_windows).returncode
    if returncode != 0:
        raise ProcessError

# Ensure that the user is logged into particle-cli
def checkLogin():
    process = [particle_cli, "whoami"]
    returncode = subprocess.run(process, shell=running_on_windows,
            stdout= subprocess.PIPE, stderr= subprocess.PIPE).returncode
    return returncode == 0

# Ensure that specified libraries are downloaded, otherwise install them
def checkLibraries(projectPath, active):
    try:
        properties = loadProperties(os.path.join(projectPath, projectFiles["properties"]))
        libraries = [key.split(".")[1] for key in properties.keys() if key.startswith("dependencies")]
    except FileNotFoundError:
        raise ProjectError("%s is not a Particle Project!" % projectPath)
    
    # Ensure that the user is signed into particle
    if active and not checkLogin():
        raise ProcessError("Please log into Particle CLI!\n\tneopo particle login")

    # pushd like behavior
    oldCWD = os.getcwd()
    os.chdir(projectPath)

    librariesIntact = True

    for library in libraries:
        requestedVersion = properties["dependencies.%s" % library]
        try:
            libProperties = loadProperties(os.path.join("lib", library, "library.properties"))
            actualVersion = libProperties["version"]
        except FileNotFoundError:
            actualVersion = None
        try:
            if requestedVersion != actualVersion:
                if active:
                    downloadLibrary(library, requestedVersion)
                else:
                    print("WARNING: library %s@%s not found locally." % (library, requestedVersion))
                    librariesIntact = False
            else:
                if active:
                    print("Library %s@%s is already installed." % (library, requestedVersion))
        except ProcessError:
            # Restore CWD
            os.chdir(oldCWD)
            raise ProjectError("Failed to download library!")

    # Restore current working directory
    os.chdir(oldCWD)

    # Return whether all libraries were present
    return librariesIntact

# Wrapper for [libs]
def libraries_command(args):
    projectPath = args[2] if len(args) >= 3 else os.getcwd()
    checkLibraries(projectPath, True)

# Add a path to an environment
def addToPath(environment, path):
    environment["PATH"] += os.pathsep + path

# Add buildtools to PATH
def addBuildtools(environment, version=None):
    toolsVersion = version if version else loadManifest(False)['buildtools']
    toolpath = os.path.join(PARTICLE_DEPS, "buildtools", toolsVersion)
    toolpath = os.path.join(toolpath, "bin") if running_on_windows else toolpath
    addToPath(environment, toolpath)

# Use the Makefile to build the specified target
def build_project(projectPath, command, helpOnly, verbosity):
    compilerVersion, scriptVersion, toolsVersion, firmwareVersion = loadManifest(True)
    tempEnv = os.environ.copy()
    addBuildtools(tempEnv, toolsVersion)

    # Windows compatibility modifications
    particle = particle_cli
    if running_on_windows:
        particle = particle.replace("C:\\", "/cygdrive/c/")
        particle = particle.replace("\\", "/")
        projectPath = projectPath.replace("\\", "\\\\")

    # Command used to invoke the Workbench makefile
    process = [
        "make", "-f", os.path.join(PARTICLE_DEPS, "buildscripts", scriptVersion, "Makefile"),
        "PARTICLE_CLI_PATH=" + particle
    ]

    # Add [-s] flag to make to silence output
    verbosity == 0 and process.append("-s")

    if helpOnly:
        process.append("help")
    else:
        try:
            devicePlatform, firmwareVersion = getSettings(projectPath)
            compilerVersion = getCompiler(firmwareVersion)

            if not checkFirmwareVersion(devicePlatform, firmwareVersion):
                raise ProjectError("Firmware related error!")

            if not checkCompiler(compilerVersion):
                raise ProjectError("Compiler related error!")

            if not checkLibraries(projectPath, False):
                print("To install libraries run: $ neopo libs [project]")

        except (FileNotFoundError, KeyError):
            if os.path.isfile(os.path.join(projectPath, projectFiles["properties"])):
                raise ProjectError("Project not configured!\nUse: neopo configure <platform> <version> <project>")
            else:
                raise ProjectError("%s is not a Particle project!" % projectPath)
        
        # Add compiler to path
        addToPath(tempEnv, os.path.join(PARTICLE_DEPS, "gcc-arm", compilerVersion, "bin"))

        # Set additional variables for make
        deviceOSPath = getFirmwarePath(firmwareVersion)
        extraCompilerFlags = getFlags(projectPath)
        process.append("APPDIR=%s" % projectPath)
        process.append("DEVICE_OS_PATH=%s" % deviceOSPath)
        process.append("PLATFORM=%s" % devicePlatform)
        process.append("EXTRA_CFLAGS=%s" % extraCompilerFlags)
        process.append(command)

    # Run makefile with given verbosity
    returncode = subprocess.run(process, env=tempEnv,
                                shell=running_on_windows,
                                stdout= subprocess.PIPE if verbosity == -1 else None,
                                stderr= subprocess.PIPE if verbosity == -1 else None
                                ).returncode
    if returncode:
        raise ProcessError("Failed with code %s" % returncode)

# Parse the project path from the specified index and run a Makefile target
def buildCommand(command, index, args):
    verboseIndex = index
    project = None
    verbosityDict = {"": 0, "-v": 1, "-q": -1}

    try:
        # Project specified, verbosity may follow
        if not args[index].startswith("-"):
            project = os.path.abspath(args[index])
            verboseIndex += 1
        else:
            project = os.getcwd()
    except IndexError:
        # Project not specified
        project = os.getcwd()
        verboseIndex = index
    try:
        # Parse verbosity to an integer
        verbosityStr = args[verboseIndex]
        verbosity = verbosityDict[verbosityStr]
    except IndexError:
        # Verbosity not specified, use default
        verbosity = 0
    except KeyError:
        raise UserError("Invalid verbosity!")

    # Build the given project with a command and verbosity
    build_project(project, command, False, verbosity)

# Print available versions compressed (for completion)
def versions_compressed(args):
    with open(jsonFiles["firmware"], "r") as firmwareFile:
        print(*[entry["version"] for entry in json.load(firmwareFile)])

# Print available platforms (for completion)
def platforms_command(args):
    with open(jsonFiles["platforms"], "r") as platformFile:
        print(*[entry["name"] for entry in json.load(platformFile)])

# Find all valid projects in PWD (for completion)
def findValidProjects(args):
    (_, dirs, _) = next(os.walk(os.getcwd()))
    print(*[dir for dir in dirs if os.access(os.path.join(dir, projectFiles["properties"]), os.R_OK)])

# Find all makefile targets (for completion)
def getMakefileTargets(args):
    with open(jsonFiles["manifest"], "r") as manifest:
        with open(os.path.join(PARTICLE_DEPS, "buildscripts", json.load(manifest)["buildscripts"], "Makefile")) as makefile:
            sep = ".PHONY: "
            print(*[line.partition(sep)[2].strip("\n") for line in makefile.readlines() if line.startswith(sep)])

# Print available versions and platforms
def versions_command(args):
    with open(jsonFiles["firmware"], "r") as firmwareFile:
        print("Available deviceOS versions:\n")
        for entry in reversed(json.load(firmwareFile)):
            version = entry["version"]
            devicesStr = ", ".join([platformConvert(platform, "id", "name") for platform in getSupportedPlatforms(version)])
            print("   %s\t [ %s ]" % (version, devicesStr))

        print("\nTo configure a project use:")
        print("\tneopo configure <platform> <version> <project>")

# Wrapper for [config/configure]
def configure_command(args):
    try:
        projectPath = args[4] if len(args) >= 5 else os.getcwd()
        configure_project(projectPath, args[2], args[3])
    except IndexError:
        raise UserError("You must supply platform and deviceOS version!")

# Wrapper for [settings]
def settings_command(args):
    try:
        projectPath = args[2] if len(args) >= 3 else os.getcwd()
        settings = getSettings(projectPath)
        flags = getFlags(projectPath)
        print("Configuration for project %s:" % projectPath)
        print("\tparticle.targetPlatform: %s" % settings[0])
        print("\tparticle.firmwareVersion: %s"% settings[1])
        print("\tEXTRA_CFLAGS: %s" % (flags if flags else "<not set>"))
        print()
    except FileNotFoundError:
        raise UserError("%s is not a Particle project!" % projectPath)

# Wrapper for [run]
def run_command(args):
    try:
        buildCommand(args[2], 3, args)
    except IndexError:
        build_help()
        raise UserError("You must supply a Makefile target!")

# Wrapper for [create]
def create_command(args):
    try:
        projectPath = os.path.abspath(args[2])
        create_project(os.path.dirname(projectPath), os.path.basename(projectPath))
    except IndexError:
        raise UserError("You must supply a path for the project!")

# Wrapper for [get]
def get_command(args):
    try:
        downloadFirmware(args[2])
    except IndexError:
        raise UserError("You must specify a deviceOS version!")

# Wrappers for commands that build
def flash_command(args):
    buildCommand("flash-user", 2, args)
def compile_command(args):
    buildCommand("compile-user", 2, args)
def flash_all_command(args):
    buildCommand("flash-all", 2, args)
def clean_command(args):
    buildCommand("clean-user", 2, args)

# Wrapper for [install]
def install_command(args):
    try:
        force = args[2] == "-f"
    except IndexError:
        force = None
    installOrUpdate(True, force)

# Wrapper for [update]
def update_command(args):
    try:
        force = args[2] == "-f"
    except IndexError:
        force = None
    installOrUpdate(False, force)

# Wait for user to press enter [for scripting]
def script_wait(args):
    input("Press Enter to continue...")

# Print a message to the console [for scripting]
def script_print(args):
    try:
        message = args[2:]
    except IndexError:
        message = ""
    print(*message)

# List all scripts installed (for completion)
def listScripts(args):
    (_, _, files) = next(os.walk(SCRIPTS_DIR))
    print(*files)

# Copy a script file into the scripts directory
def load_command(args):
    try:
        scriptPath = args[2]
        shutil.copyfile(scriptPath, os.path.join(SCRIPTS_DIR, os.path.basename(scriptPath)))
        print("Copied %s into %s" % (scriptPath, SCRIPTS_DIR))
    except IndexError:
        raise UserError("You must specify a script file!")
    except FileNotFoundError:
        raise UserError("Could not find script %s!" % scriptPath)

# List available scripts
def listScriptsMsg():
    (_, _, scripts) = next(os.walk(SCRIPTS_DIR))
    if scripts:
        print("Available scripts:")
        print(*scripts, sep=", ")
        print()

# Wrapper for [script]
def script_command(args):
    try:
        name = args[2]
    except IndexError:
        listScriptsMsg()
        raise UserError("You must supply a script name!")

    scriptPath = os.path.join(SCRIPTS_DIR, name)

    try:
        # Open the script and execute each line
        with open(scriptPath, "r") as script:
            for line in script.readlines():
                # Skip comments
                if line.startswith("#"):
                    continue
                # Skip empty lines
                process = [args[0], *line.split()]
                if len(process) > 1:
                    print(process)
                    # Run the process just like a regular invocation
                    main(process)
    except FileNotFoundError:
        raise ProcessError("Could not find script %s!" % name)

# Print all iterable options (for completion)
def iterate_options(args):
    print(*iterable_commands)

# Available options for iterate
iterable_commands = {
    "compile": compile_command,
    "build": compile_command,
    "flash": flash_command,
    "flash-all": flash_all_command,
    "clean": clean_command,
    "run": run_command,
    "script": script_command
}

# Iterate through all connected devices and run a command
def iterate_command(args):
    # Find Particle deviceIDs connected via USB
    process = [particle_cli, "serial", "list"]
    particle = subprocess.run(process, stdout=subprocess.PIPE,
                                        shell=running_on_windows)
    devices = [line.decode("utf-8").split()[-1] for line in particle.stdout.splitlines()[1:]]

    if not devices:
        raise ProcessError("No devices found!")
    
    # Remove "iterate" from process
    del args[1]

    try:
        if not args[1] in iterable_commands.keys():
            raise UserError("Invalid command!")
    except IndexError:
        raise UserError("You must supply a command to iterate with!")

    for device in devices:
        print("DeviceID: %s" % device)
        # Put device into DFU mode
        process = [particle_cli, "usb", "dfu", device]
        subprocess.run(process, stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                shell=running_on_windows)
        # Run the iterable command
        iterable_commands[args[1]](args)

# Get EXTRA_CFLAGS for a project or return empty string
def getFlags(projectPath):
    try:
        settingsPath = os.path.join(projectPath, projectFiles["settings"])
        with open(settingsPath, "r") as file:
            settings = json.load(file)
        return settings["EXTRA_CFLAGS"]
    except:
        return ""

# Set EXTRA_CFLAGS for a project
def setFlags(projectPath, makeFlags):
    settingsPath = os.path.join(projectPath, projectFiles["settings"])
    with open(settingsPath, "r") as file:
        settings = json.load(file)
    settings["EXTRA_CFLAGS"] = makeFlags
    with open(settingsPath, "w") as file:
        json.dump(settings, file, indent=4)

# Wrapper for [flags]
def flags_command(args):
    try:
        makeFlags = args[2]
    except IndexError:
        raise UserError("You must provide the flags as one (quoted) string!")    
    try:
        project = os.path.abspath(args[3])
    except IndexError:
        project = os.getcwd()

    setFlags(project, makeFlags)

# Wrapper for [upgrade]
# TODO: Deprecate, since using pip/pacman
def upgrade_command(args):
    # This is a primitive upgrade function. Releases will be used in future.
    url = "https://raw.githubusercontent.com/nrobinson2000/neopo/master/neopo/neopo.py"
    execPath = args[0]

    # Ensure that we are calling neopo absolutely (to prevent overwriting dev)
    # execPath may be root owned!
    if execPath == os.path.abspath(execPath):
        print("Upgrading neopo...")
        try:
            with urllib.request.urlopen(url) as response, open(execPath, "w") as file:
                content = response.read().decode("utf-8")
                file.write(content)
        except urllib.error.URLError:
            raise ProcessError("Failed to download upgrade!")
        except PermissionError:
            raise ProcessError("Failed to apply upgrade!\nTry running with sudo.")
    else:
        raise ProcessError("Neopo was not run absolutely, not upgrading.")

# Wrapper for [particle]
def particle_command(args):
    # Add build tools to env
    tempEnv = os.environ.copy()
    addBuildtools(tempEnv)

    process = [particle_cli, *args[2:]]

    try:
        returncode = subprocess.run(process, env=tempEnv, shell=running_on_windows).returncode
    # Return cleanly if ^C was pressed
    except KeyboardInterrupt:
        return
    if returncode:
        raise ProcessError("Particle CLI exited with code %s" % returncode)
            
# Print help information about the program
def print_help(args):
    print_logo()
    print("""Usage: neopo [OPTIONS] [PROJECT] [-v/q]

Options:
    General Options:
        help                    # Show this help information
        install [-f]            # Install dependencies (-f to force)
        upgrade                 # Upgrade neopo
        uninstall               # Uninstall neopo
        versions                # List available versions and platforms
        create <project>        # Create a Workbench/neopo project
        particle [OPTIONS]      # Use the encapsulated Particle CLI

    Build Options:
        compile/build [project] [-v/q]  # Build a project: `compile-user`
        flash [project] [-v/q]          # Flash a project: `flash-user`
        flash-all [project] [-v/q]      # Flash a project: `flash-all`
        clean [project] [-v/q]          # Clean a project: `clean-user`

    Special Options:
        run <target> [project] [-v/q]             # Run a makefile target
        configure <platform> <version> [project]  # Configure a project
        flags <string> [project]                  # Set EXTRA_CFLAGS in project 
        settings [project]                        # View configured settings
        libs [project]                            # Install Particle libraries
        iterate <command> [OPTIONS] [-v/q]        # Put devices into DFU mode
                                                  # and run commands on them
    Script Options:
        script <script name>    # Execute a script in ~/.neopo/scripts
        load <script name>      # Copy a script into ~/.neopo/scripts

    Dependency Options:
        update                  # Update neopo dependencies
        get <version>           # Download a specific deviceOS version
        """)

def print_logo():
    print(
r"""    ____  ___  ____  ____  ____
   / __ \/ _ \/ __ \/ __ \/ __ \    A lightweight solution for
  / / / /  __/ /_/ / /_/ / /_/ /    local Particle development.
 /_/ /_/\___/\____/ ____/\____/ 
                 /_/      .xyz      Copyright (c) 2020 Nathan Robinson
    """)

# Print all commands (for completion)
def options(args):
    print(*commands)

# Available options
commands = {
    "help": print_help,
    "install": install_command,
    "uninstall": uninstall_command,
    "versions": versions_command,
    "create": create_command,
    "compile": compile_command,
    "build": compile_command,
    "flash": flash_command,
    "flash-all": flash_all_command,
    "clean": clean_command,
    "run": run_command,
    "configure": configure_command,
    "update": update_command,
    "get": get_command,
    "list-versions": versions_compressed,
    "platforms": platforms_command,
    "projects": findValidProjects,
    "targets": getMakefileTargets,
    "options": options,
    "download-unlisted": downloadUnlisted_command,
    "script": script_command,
    "list-scripts": listScripts,
    "load": load_command,
    "iterate": iterate_command,
    "options-iterable": iterate_options,
    "flags": flags_command,
    "upgrade": upgrade_command,
    "particle": particle_command,
    "wait": script_wait,
    "print": script_print,
    "settings": settings_command,
    "libs": libraries_command
}

# Evaluate command-line arguments and call necessary functions
def main(args):
    if len(args) == 1:
        help()
        # print("ayy lmao")
    elif args[1] in commands:
        try:
            commands[args[1]](args)
        except FileNotFoundError as e:
            file = e.filename
            if responsible(file):
                print("Error: file %s not found." % file)
                print("Please ensure that you have installed the dependencies:")
                print("\t$ neopo install")
            else:
                unexpectedError()
        except RuntimeError as e:
            print(e)
            exit(1)
        except Exception as e:
            unexpectedError()
            exit(2)
    else:
        print_help(args)
        print("Invalid command!")
        print()
        exit(3)

# Print traceback and message for unhandled exceptions
def unexpectedError():
    traceback.print_exc()
    print("An unexpected error occurred!")
    print("To report this error on GitHub, please open an issue:")
    print("https://github.com/nrobinson2000/neopo/issues")

# Check if neopo is responsible for given file
def responsible(file):
    dirs = [PARTICLE_DEPS, NEOPO_DEPS, CACHE_DIR, SCRIPTS_DIR]
    for dir in dirs:
        if file.startswith(dir):
            return True
    return False

### MODULE API

# Main API for using neopo as a module
def exec(args):
    if isinstance(args, str):
        args = args.split()
    try:
        # Add dummy first argument
        args = ["", *args]
        commands[args[1]](args)
    except IndexError:
        print("Expected a command!")
    except RuntimeError as e:
        print(e)

### General options

def help():
    print_help(None)

def install(force = False):
    installOrUpdate(True, force)

def upgrade():
    upgrade_command(None)

def uninstall():
    uninstall_command(None)

def versions():
    versions_command(None)

def create(projectPath = os.getcwd()):
    create_command([None, None, projectPath])

def particle(args):
    particle_command([None, None, *args])

### Build options

def build(projectPath = os.getcwd(), verbosity = ""):
    compile_command([None, None, projectPath, verbosity])

def flash(projectPath = os.getcwd(), verbosity = ""):
    flash_command([None, None, projectPath, verbosity])

def flash_all(projectPath = os.getcwd(), verbosity = ""):
    flash_all_command([None, None, projectPath, verbosity])

def clean(projectPath = os.getcwd(), verbosity = ""):
    clean_command([None, None, projectPath, verbosity])

### Special options

def run(target, projectPath = os.getcwd(), verbosity = ""):
    run_command([None, None, target, projectPath, verbosity])

def configure(platform, version, projectPath = os.getcwd()):
    configure_command([None, None, platform, version, projectPath])

def flags(flagsStr, projectPath = os.getcwd()):
    flags_command([None, None, flagsStr, projectPath])

def settings(projectPath = os.getcwd()):
    settings_command([None, None, projectPath])

def libs(projectPath = os.getcwd()):
    libraries_command([None, None, projectPath])

def iterate(args, verbosity = ""):
    iterate_command([None, None, *args, verbosity])

### Script options

def script(scriptName):
    script_command([None, None, scriptName])

def load(scriptPath):
    load_command([None, None, scriptPath])

### Dependency options

def update():
    installOrUpdate(False, False)

def get(version):
    get_command([None, None, version])

### COMMAND LINE

# Call main() with command-line arguments
if __name__ == "__main__":
    main(sys.argv)
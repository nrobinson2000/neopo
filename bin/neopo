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
import pathlib
import platform
import traceback
import subprocess
import urllib.request

class Neopo:

	# Custom errors
	class UserError(RuntimeError):
	    pass
	class DependencyError(RuntimeError):
	    pass
	class ProcessError(RuntimeError):
	    pass
	class ProjectError(RuntimeError):
	    pass
	
	# Primary directories: dependencies, caches, scripts
	_PARTICLE_DEPS = os.path.join(os.path.expanduser("~"), ".particle", "toolchains")
	_NEOPO_DEPS = os.path.join(os.path.expanduser("~"), ".neopo")
	_CACHE_DIR = os.path.join(_NEOPO_DEPS, "cache")
	_SCRIPTS_DIR = os.path.join(_NEOPO_DEPS, "scripts")
	
	# Raspberry Pi gcc-arm downloads
	_RPI_GCC_ARM = {
	    "5.3.1": "https://github.com/nrobinson2000/neopo/releases/download/0.0.1/gcc-arm-v5.3.1-raspberry-pi.tar.gz",
	    "9.2.1": "https://github.com/nrobinson2000/neopo/releases/download/0.0.2/gcc-arm-v9.2.1-raspberry-pi.tar.gz"
	}
	
	# Windows tricks
	_running_on_windows = platform.system() == "Windows"
	_particle_cli = os.path.join(_NEOPO_DEPS, "particle.exe") if _running_on_windows else os.path.join(_NEOPO_DEPS, "particle")
	
	# JSON cache files
	_jsonFiles = {
	    "firmware": os.path.join(_CACHE_DIR, "firmware.json"),
	    "toolchains": os.path.join(_CACHE_DIR, "toolchains.json"),
	    "platforms": os.path.join(_CACHE_DIR, "platforms.json"),
	    "compilers": os.path.join(_CACHE_DIR, "compilers.json"),
	    "manifest": os.path.join(_CACHE_DIR, "manifest.json")
	}
	
	# Workbench template files
	_vscodeFiles = {
	    "dir": os.path.join(_NEOPO_DEPS, "vscode"),
	    "launch": os.path.join(_NEOPO_DEPS, "vscode", "launch.json"),
	    "settings": os.path.join(_NEOPO_DEPS, "vscode", "settings.json")
	}
	
	# Files inside VSIX
	_extensionFiles = {
	    "bin": "extension/src/cli/bin",
	    "manifest": "extension/src/compiler/manifest.json",
	    "launch": "extension/src/cli/vscode/launch.json",
	    "settings": "extension/src/cli/vscode/settings.json"
	}
	
	# Files inside project
	_projectFiles = {
	    "launch": os.path.join(".vscode", "launch.json"),
	    "settings": os.path.join(".vscode", "settings.json"),
	    "properties": "project.properties"
	}
	
	# Use this as .travis.yml when creating project repos
	_TRAVIS_YML = """# Build a neopo project with Travis CI
os: linux
language: shell
install:
  - export PATH="$PATH:$PWD"
  - sudo apt update
  - sudo apt install libarchive-zip-perl libc6-i386
  - curl -LO https://raw.githubusercontent.com/nrobinson2000/neopo/master/bin/neopo
  - chmod +x neopo
  - neopo install
script:
  - neopo build
cache:
  directories:
    - $HOME/.particle
    - $HOME/.neopo
"""

	# Find the Workbench extension URL from the Visual Studio Marketplace
	def getExtensionURL(self):
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
	        raise self.DependencyError("Failed to get extension URL!")
	    
	    # Parse response and extract the URL of the VSIX
	    data = json.loads(content.decode("utf-8"))
	    return data["results"][0]["extensions"][0]["versions"][0]["files"][-1]["source"]
	
	# Download the the Workbench extension from the URL and return it in ZIP format
	def getExtension(self, url):
	    print("Downloading Workbench extension...")
	    try:
	        with urllib.request.urlopen(url) as response:
	            content = response.read()
	    except urllib.error.URLError:
	        raise self.DependencyError("Failed to download extension!")
	    return zipfile.ZipFile(io.BytesIO(content), "r")
	
	# Load a file from a ZIP
	def getFile(self, file, path):
	    return file.read(path)
	
	# Download the specified dependency
	def downloadDep(self, dep, updateManifest):
	    if not dep: return False
	    if updateManifest: self.writeManifest(dep)
	
	    name, version, url = dep["name"], dep["version"], dep["url"]
	    print("Downloading dependency", name, "version", version + "...")
	
	    try:
	        with urllib.request.urlopen(url) as response:
	            content = response.read()
	    except urllib.error.URLError:
	        raise self.DependencyError("Failed to download dependency!")
	
	    # Ensure that installation directory exists
	    path = os.path.join(self._PARTICLE_DEPS, name, version)
	    pathlib.Path(path).mkdir(parents=True, exist_ok=True)
	
	    # Write the archive to a file to save RAM
	    fileName = os.path.join(path, name + "-v" + version + ".tar.gz")
	    with open(fileName, "wb") as gzFile:
	        gzFile.write(content)
	
	    # Extract the archive
	    with tarfile.open(fileName, "r:gz") as file:
	        file.extractall(path)
	
	    # Delete the temporary archive
	    os.remove(fileName)
	    return True
	
	# Write data to a file
	def writeFile(self, content, path, mode):
	    with open(path, mode) as file:
	        file.write(content)
	
	# Write an executable dependency to a file
	def writeExecutable(self, content, path):
	    with open(path, "wb") as file:
	        file.write(content)
	        st = os.stat(file.name)
	        os.chmod(file.name, st.st_mode | stat.S_IEXEC)
	
	# Download extension manifest and simple dependencies
	def getDeps(self):
	    # Ensure that cache and scripts directories exist
	    pathlib.Path(self._CACHE_DIR).mkdir(parents=True, exist_ok=True)
	    pathlib.Path(self._SCRIPTS_DIR).mkdir(parents=True, exist_ok=True)
	
	    # Download and extract VSIX, and obtain dependency manifest
	    extension = self.getExtension(self.getExtensionURL())
	    pathlib.Path(self._vscodeFiles["dir"]).mkdir(parents=True, exist_ok=True)
	    manifest = self.getFile(extension, self._extensionFiles["manifest"])
	
	    # Attempt to pull particle-cli executable from VSIX
	    try:
	        osPlatform = platform.system().lower()
	        osArch = platform.machine().lower() if self._running_on_windows else "amd64" if platform.machine() == "x86_64" else "arm"
	        particle_bin = os.path.basename(self._particle_cli)
	        particle = self.getFile(extension, "/".join([self._extensionFiles["bin"], osPlatform, osArch, particle_bin]))
	        self.writeExecutable(particle, self._particle_cli)
	    except KeyError:
	        raise self.DependencyError("Failed to download particle executable from extension!")
	    
	    # Create launch.json and settings.json project template files
	    launch = self.getFile(extension, self._extensionFiles["launch"])
	    settings = self.getFile(extension, self._extensionFiles["settings"])
	    self.writeFile(launch, self._vscodeFiles["launch"], "wb")
	    self.writeFile(settings, self._vscodeFiles["settings"], "wb")
	
	    # Ensure that manifest file exists and return manifest content
	    self.createManifest()
	    return json.loads(manifest.decode("utf-8"))
	
	# Update the manifest JSON file
	def writeManifest(self, dep):
	    with open(self._jsonFiles["manifest"], "r+") as file:
	        try:
	            manifest = json.load(file)
	        except json.decoder.JSONDecodeError:
	            manifest = {}
	
	        manifest[dep["name"]] = dep["version"]
	        file.seek(0)
	        json.dump(manifest, file, indent=4)
	        file.truncate()
	
	# Create the manifest file
	def createManifest(self):
	    if not os.path.isfile(self._jsonFiles["manifest"]):
	        open(self._jsonFiles["manifest"], "w")
	
	# Load settings from the dependency mainfest JSON file
	def loadManifest(self, tupleOrDict):
	    with open(self._jsonFiles["manifest"], "r") as file:
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
	def writeJSONcache(self, data, key):
	    with open(self._jsonFiles[key], "w") as file:
	        keyData = data[key]
	        json.dump(keyData, file, indent=4)
	
	# Try to download given firmware
	def attemptDownload(self, firmware):
	    try:
	        self.downloadDep(firmware, False)
	        return
	    except urllib.error.URLError:
	        raise self.DependencyError("DeviceOS version " + firmware["version"] + " not found!")
	
	# Attempt to download deviceOS version not specified in manifest (experimental)
	def downloadUnlisted(self, version):
	    # Minimum information for a firmware dependency
	    firmware = {"name": "deviceOS", "version": version,
	        "url": "https://binaries.particle.io/device-os/v" + version + ".tar.gz"}
	
	    try:
	        # Attempt to download from Particle's download mirror
	        print("Trying binaries.particle.io/device-os...")
	        self.attemptDownload(firmware)
	    except self.DependencyError:
	        # Try to download from github
	        firmware["url"] = "https://github.com/particle-iot/device-os/archive/v" + version + ".tar.gz"
	        print("Trying github.com/particle-iot/device-os...")
	        self.attemptDownload(firmware)
	    
	# Wrapper for [download-unlisted]
	def downloadUnlisted_command(self, args):
	    try:
	        self.downloadUnlisted(args[2])
	    except IndexError:
	        raise self.UserError("You must specify a deviceOS version!")
	
	# Download a specific deviceOS version
	def downloadFirmware(self, version):
	    if not self.downloadDep(self.getFirmwareData(version), False):
	        print("Could not download deviceOS version", version + "!")
	
	# Install or update neopo dependencies (not the neopo script)
	def installOrUpdate(self, install, force):    
	    forceInstall = force == "-f"    
	    print("Installing neopo..." if install else "Updating dependencies...")
	
	    # Dependencies we wish to install and caches we will create
	    dependencies = ["compilers", "tools", "scripts", "debuggers"]
	    caches = ["firmware", "platforms", "toolchains", "compilers"]
	
	    # Download dependency data and create list of installables
	    data = self.getDeps()
	    depJSON = [data["firmware"][0]]
	
	    # Append dependencies to list
	    system = platform.system().lower()
	    for dep in dependencies: depJSON.append(data[dep][system]["x64"][0])
	
	    # To support Raspberry Pi use my precompiled gcc-arm toolchain
	    if platform.machine() == "armv7l":
	        for dep in depJSON:
	            if dep["name"] == "gcc-arm":
	                dep["url"] = self._RPI_GCC_ARM[dep["version"]]
	                break
	    
	    # Update JSON cache files
	    for key in caches: self.writeJSONcache(data, key)
	
	    # Either install or update
	    if install:
	        skippedDeps = []
	        for dep in depJSON:
	            # Install dependency if not currently installed, or forced, otherwise skip
	            installed = os.path.isdir(os.path.join(self._PARTICLE_DEPS, dep["name"], dep["version"]))
	            self.downloadDep(dep, True) if not installed or forceInstall else skippedDeps.append(dep)
	
	        # Put skippedDeps in manifest.json. Fixes: nrobinson2000/neopo/issues/8
	        for dep in skippedDeps: self.writeManifest(dep)
	
	        # Notify user of dependencies skipped to save bandwidth and time
	        if skippedDeps:
	            print()
	            print("Skipped previously installed dependencies:")
	            print(*[dep["name"]+"@"+dep["version"] for dep in skippedDeps], sep=", ")
	        
	        print()
	        # [neopo install] finishes here.
	        # In the [install.sh] script additional steps are done afterwards. 
	        
	    else:
	        # Load in dependency manifest, and only install a dependency if newer
	        manifest = self.loadManifest(False)
	        for dep in depJSON:
	            new = int(dep["version"].split("-")[0].replace(".", ""))
	            old = int(manifest[dep["name"]].split("-")[0].replace(".", ""))
	            if new > old: self.downloadDep(dep, True)
	        print("Dependencies are up to date!")
	
	# Delete the neopo script from the system
	def uninstall(self, args):
	    execpath = args[0]
	    print("Are you sure you want to uninstall neopo at", execpath + "?")
	
	    # Ask for confirmation
	    if input("(Y/N): ").lower() != "y":
	        raise self.UserError("Aborted.")
	    try:
	        #TODO: the ~/.neopo directory should get deleted too
	        os.remove(execpath)
	        print("Uninstalled neopo.")
	        print("Note: The .particle directory may still exist (remove it with `rm -rf ~/.particle`)")
	    except PermissionError:
	        raise self.ProcessError("Could not delete " + execpath + "\n" + "Try running with sudo.")
	
	# Create a Particle project and copy in Workbench settings
	def create(self, path, name):
	    tempEnv = os.environ.copy()
	    self.addToPath(tempEnv, self._NEOPO_DEPS)
	    projectPath = os.path.join(path, name)
	
	    # Use particle-cli to create the project
	    returncode = subprocess.run(
	        ["particle", "project", "create", path, "--name", name],
	        env=tempEnv,
	        shell=self._running_on_windows).returncode
	    if returncode:
	        raise self.ProcessError("Failed with code " + str(returncode))
	
	    # If git is installed, initialize project as git repo
	    if shutil.which("git"):
	        subprocess.run(["git", "init", projectPath])
	        # Add .travis.yml to project
	        self.writeFile(self._TRAVIS_YML, os.path.join(projectPath, ".travis.yml"), "w")
	        # Add .gitignore to project
	        self.writeFile("target", os.path.join(projectPath, ".gitignore"), "w")
	
	    # Add buttons to README.md
	    travisButton = "[![](https://api.travis-ci.org/yourUser/yourRepo.svg?branch=master)](https://travis-ci.org/yourUser/yourRepo)"
	    neopoButton = "[![](https://img.shields.io/badge/built_with-neopo-informational)](https://nrobinson2000.github.io/neopo)"
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
	    src = os.path.join(projectPath, "src", name + ".ino")
	    dst = os.path.join(projectPath, "src", name + ".cpp")
	    shutil.move(src, dst)
	    with open(dst, "r") as original:
	        data = original.read()
	    with open(dst, "w") as modified:
	        modified.write(include + data)
	
	    #TODO: Default device in manifest.json
	    device = "argon"
	    version = self.loadManifest(False)["deviceOS"]
	    self.configure(projectPath, device, version)
	
	# Get a deviceOS dependency from a version
	def getFirmwareData(self, version):
	    with open(self._jsonFiles["firmware"], "r") as firmwareFile:
	        for entry in json.load(firmwareFile):
	            if entry["version"] == version:
	                return entry
	        return False
	
	# Convert between platform IDs and device names
	def platformConvert(self, data, key1, key2):
	    with open(self._jsonFiles["platforms"], "r") as platformFile:
	        for platform in json.load(platformFile):
	            if platform[key1] == data:
	                return platform[key2]
	        return False
	
	# List the supported platform IDs for a given version
	def getSupportedPlatforms(self, version):
	    with open(self._jsonFiles["toolchains"], "r") as toolchainsFile:
	        for toolchain in json.load(toolchainsFile):
	            if toolchain["firmware"] == "deviceOS@" + version:
	                return toolchain["platforms"]
	        return False
	
	# Verify platform and deviceOS version and download deviceOS dependency if required
	def checkFirmwareVersion(self, platform, version):
	    firmware = self.getFirmwareData(version)
	    platformID = self.platformConvert(platform, "name", "id")
	
	    # Check that platform and firmware are compatible
	    if not platformID:
	        print("Invalid platform", platform + "!")
	        return False
	    if not firmware:
	        print("Invalid deviceOS version", version + "!")
	        return False
	    if not platformID in self.getSupportedPlatforms(version):
	        print("Platform", platform, " is not supported in deviceOS version", version + "!")
	        return False
	
	    # If required firmware is not installed, download it
	    path = os.path.join(self._PARTICLE_DEPS, "deviceOS", version)
	    os.path.isdir(path) or self.downloadDep(firmware, False)
	    return True
	
	# Modify Workbench settings in a project (platform, firmwareVersion)
	def configure(self, projectPath, platform, firmwareVersion):
	    # Ensure that firware is compatible with platform
	    # Download requested version if required
	    if not self.checkFirmwareVersion(platform, firmwareVersion):
	        raise self.ProjectError("Firmware related error!")
	    
	    # Ensure that a valid project was selected
	    if not os.path.isfile(os.path.join(projectPath, self._projectFiles["properties"])):
	        raise self.ProjectError(projectPath + " is not a Particle project!")
	    
	    # Upgrade a CLI project to Workbench format if required
	    if not os.path.isfile(os.path.join(projectPath, self._projectFiles["settings"])):
	        pathlib.Path(os.path.join(projectPath, ".vscode")).mkdir(parents=True, exist_ok=True)
	        shutil.copyfile(self._vscodeFiles["launch"], os.path.join(projectPath, self._projectFiles["launch"]))
	        shutil.copyfile(self._vscodeFiles["settings"], os.path.join(projectPath, self._projectFiles["settings"]))
	
	    # Apply configuration to project
	    self.writeSettings(projectPath, platform, firmwareVersion)
	    print("Configured project", projectPath + ":")
	    print("\tparticle.targetPlatform:", platform)
	    print("\tparticle.firmwareVersion:", firmwareVersion)
	
	# Load Workbench settings from a project
	def getSettings(self, projectPath):
	    with open(os.path.join(projectPath, self._projectFiles["settings"]), "r") as settings:
	        data = json.loads(settings.read())
	        return (data["particle.targetPlatform"], data["particle.firmwareVersion"])
	
	# Update Workbench settings in a project
	def writeSettings(self, projectPath, platform, version):
	    with open(os.path.join(projectPath, self._projectFiles["settings"]), "r+") as settings:
	        data = json.loads(settings.read())
	        data["particle.targetPlatform"] = platform
	        data["particle.firmwareVersion"] = version
	        settings.seek(0)
	        json.dump(data, settings, indent=4)
	        settings.truncate()
	
	# Print help information directly from Makefile
	def build_help(self):
	    self.build(None, None, True, 0)
	
	# Create the path string for a given deviceOS version
	def getFirmwarePath(self, version):
	    deviceOSPath = os.path.join(self._PARTICLE_DEPS, "deviceOS", version)
	    legacy = os.path.join(deviceOSPath, "firmware-" + version)
	    github = os.path.join(deviceOSPath, "device-os-" + version)
	    return legacy if os.path.isdir(legacy) else github if os.path.isdir(github) else deviceOSPath
	
	# For a given firmware version return the appropriate compiler version
	def getCompiler(self, firmwareVersion):
	    with open(self._jsonFiles["toolchains"]) as file:
	        data = json.load(file)
	        for toolchain in data:
	            if toolchain["firmware"] == "deviceOS@" + firmwareVersion:
	                return toolchain["compilers"].split("@")[1]
	        raise self.DependencyError("Invalid firmware version!")
	
	# Get a gcc-arm dependency from a version
	def getCompilerData(self, version):
	    with open(self._jsonFiles["compilers"], "r") as compilersFile:
	        data = json.load(compilersFile)
	        system = platform.system().lower()
	        compilers = data[system]["x64"]
	
	        for compiler in compilers:
	            if compiler["version"] == version:
	                if platform.machine() == "armv7l":
	                    compiler["url"] = self._RPI_GCC_ARM[version]
	                return compiler
	        return False
	
	# Ensure that the requested compiler version is installed
	def checkCompiler(self, compilerVersion):
	    # If required compiler is not installed, download it
	    path = os.path.join(self._PARTICLE_DEPS, "gcc-arm", compilerVersion)
	    os.path.isdir(path) or self.downloadDep(self.getCompilerData(compilerVersion), False)
	    return True
	
	# Create a dictionary from a .properties file
	def loadProperties(self, propertiesPath):
	    properties = {}
	    with open(propertiesPath, "r") as file:
	        for line in file.readlines():
	            tokens = line.split("=", 1)
	            key = tokens[0]
	            value = tokens[1].strip()
	            properties[key] = value
	    return properties
	
	# Download a library using particle-cli
	def downloadLibrary(self, library, version):
	    process = [self._particle_cli, "library", "copy", library + "@" + version]
	    returncode = subprocess.run(process, shell=self._running_on_windows).returncode
	    if returncode != 0:
	        raise self.ProcessError
	
	# Ensure that the user is logged into particle-cli
	def checkLogin(self):
	    process = [self._particle_cli, "whoami"]
	    returncode = subprocess.run(process, shell=self._running_on_windows,
	            stdout= subprocess.PIPE, stderr= subprocess.PIPE).returncode
	    return returncode == 0
	
	# Ensure that specified libraries are downloaded, otherwise install them
	def checkLibraries(self, projectPath):
	    try:
	        properties = self.loadProperties(os.path.join(projectPath, self._projectFiles["properties"]))
	        libraries = [key.split(".")[1] for key in properties.keys() if key.startswith("dependencies")]
	    except FileNotFoundError:
	        raise self.ProjectError(projectPath + " is not a Particle Project!")
	    
	    # Ensure that the user is signed into particle
	    if not self.checkLogin():
	        raise self.ProcessError("Please log into Particle CLI!\n\tneopo particle login")
	
	    # pushd like behavior
	    oldCWD = os.getcwd()
	    os.chdir(projectPath)
	
	    for library in libraries:
	        requestedVersion = properties["dependencies." + library]
	        try:
	            libProperties = self.loadProperties(os.path.join("lib", library, "library.properties"))
	            actualVersion = libProperties["version"]
	        except FileNotFoundError:
	            actualVersion = None
	        try:
	            if requestedVersion != actualVersion:
	                self.downloadLibrary(library, requestedVersion)
	            else:
	                print("Library", library, requestedVersion, "is already installed.")
	        except self.ProcessError:
	            # Restore CWD
	            os.chdir(oldCWD)
	            raise self.ProjectError("Failed to download library!")
	
	    # Restore current working directory
	    os.chdir(oldCWD)
	
	# Wrapper for [libs]
	def libraries_command(self, args):
	    projectPath = args[2] if len(args) >= 3 else os.getcwd()
	    self.checkLibraries(projectPath)
	
	# Add a path to an environment
	def addToPath(self, environment, path):
	    environment["PATH"] += os.pathsep + path
	
	# Use the Makefile to build the specified target
	def build(self, projectPath, command, helpOnly, verbosity):
	    compilerVersion, scriptVersion, toolsVersion, firmwareVersion = self.loadManifest(True)
	    tempEnv = os.environ.copy()
	
	    # Windows compatibility modifications
	    particle = self._particle_cli
	    if self._running_on_windows:
	        self.addToPath(tempEnv, os.path.join(self._PARTICLE_DEPS, "buildtools", toolsVersion, "bin"))
	        particle = particle.replace("C:\\", "/cygdrive/c/")
	        particle = particle.replace("\\", "/")
	        projectPath = projectPath.replace("\\", "\\\\")
	    else:
	        self.addToPath(tempEnv, os.path.join(self._PARTICLE_DEPS, "buildtools", toolsVersion))
	
	    # Command used to invoke the Workbench makefile
	    process = [
	        "make", "-f", os.path.join(self._PARTICLE_DEPS, "buildscripts", scriptVersion, "Makefile"),
	        "PARTICLE_CLI_PATH=" + particle
	    ]
	
	    # Add [-s] flag to make to silence output
	    verbosity == 0 and process.append("-s")
	
	    if helpOnly:
	        process.append("help")
	    else:
	        try:
	            devicePlatform, firmwareVersion = self.getSettings(projectPath)
	            compilerVersion = self.getCompiler(firmwareVersion)
	
	            if not self.checkFirmwareVersion(devicePlatform, firmwareVersion):
	                raise self.ProjectError("Firmware related error!")
	
	            if not self.checkCompiler(compilerVersion):
	                raise self.ProjectError("Compiler related error!")
	
	            # TODO: Suggest using [neopo libs] if libraries are not downloaded
	
	        except FileNotFoundError:
	            if os.path.isfile(os.path.join(projectPath, self._projectFiles["properties"])):
	                raise self.ProjectError("Project not configured!" + "\n" + "Use: neopo configure <platform> <version> <project>")
	            else:
	                raise self.ProjectError(projectPath + " is not a Particle project!")
	        
	        # Add compiler to path
	        self.addToPath(tempEnv, os.path.join(self._PARTICLE_DEPS, "gcc-arm", compilerVersion, "bin"))
	
	        # Set additional variables for make
	        deviceOSPath = self.getFirmwarePath(firmwareVersion)
	        extraCompilerFlags = self.getFlags(projectPath)
	        process.append("APPDIR=" + projectPath)
	        process.append("DEVICE_OS_PATH=" + deviceOSPath)
	        process.append("PLATFORM=" + devicePlatform)
	        process.append("EXTRA_CFLAGS=" + extraCompilerFlags)
	        process.append(command)
	
	    # DEBUG: Confirm we are using correct compiler
	    # print(shutil.which(cmd="arm-none-eabi-gcc", path=tempEnv["PATH"]))
	
	    # Run makefile with given verbosity
	    returncode = subprocess.run(process, env=tempEnv,
	                                shell=self._running_on_windows,
	                                stdout= subprocess.PIPE if verbosity == -1 else None,
	                                stderr= subprocess.PIPE if verbosity == -1 else None
	                                ).returncode
	    if returncode:
	        raise self.ProcessError("Failed with code " + str(returncode))
	
	# Parse the project path from the specified index and run a Makefile target
	def buildCommand(self, command, index, args):
	    verboseIndex = index
	    project = None
	    verbosityDict = {"-v": 1, "-q": -1}
	
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
	        raise self.UserError("Invalid verbosity!")
	
	    # Build the given project with a command and verbosity
	    self.build(project, command, False, verbosity)
	
	# Print available versions compressed (for completion)
	def versions_compressed(self, args):
	    with open(self._jsonFiles["firmware"], "r") as firmwareFile:
	        print(*[entry["version"] for entry in json.load(firmwareFile)])
	
	# Print available platforms (for completion)
	def platforms_command(self, args):
	    with open(self._jsonFiles["platforms"], "r") as platformFile:
	        print(*[entry["name"] for entry in json.load(platformFile)])
	
	# Find all valid projects in PWD (for completion)
	def findValidProjects(self, args):
	    (_, dirs, _) = next(os.walk(os.getcwd()))
	    print(*[dir for dir in dirs if os.access(os.path.join(dir, self._projectFiles["properties"]), os.R_OK)])
	
	# Find all makefile targets (for completion)
	def getMakefileTargets(self, args):
	    with open(self._jsonFiles["manifest"], "r") as manifest:
	        with open(os.path.join(self._PARTICLE_DEPS, "buildscripts", json.load(manifest)["buildscripts"], "Makefile")) as makefile:
	            sep = ".PHONY: "
	            print(*[line.partition(sep)[2].strip("\n") for line in makefile.readlines() if line.startswith(sep)])
	
	# Print available versions and platforms
	def versions(self, args):
	    print("Available deviceOS versions:\n")
	    with open(self._jsonFiles["firmware"], "r") as firmwareFile:
	        for entry in reversed(json.load(firmwareFile)):
	            version = entry["version"]
	            devicesStr = ", ".join([self.platformConvert(platform, "id", "name") for platform in self.getSupportedPlatforms(version)])
	            print("  ", version + "\t", "[", devicesStr, "]")
	
	        print("\nTo configure a project use:")
	        print("\tneopo configure <platform> <version> <project>")
	
	# Wrapper for [config/configure]
	def configure_command(self, args):
	    try:
	        projectPath = args[4] if len(args) >= 5 else os.getcwd()
	        self.configure(projectPath, args[2], args[3])
	    except IndexError:
	        raise self.UserError("You must supply platform and deviceOS version!")
	
	# Wrapper for [settings]
	def settings_command(self, args):
	    try:
	        projectPath = args[2] if len(args) >= 3 else os.getcwd()
	        settings = self.getSettings(projectPath)
	        flags = self.getFlags(projectPath)
	        print("Configuration for project", projectPath + ":")
	        print("\tparticle.targetPlatform:", settings[0])
	        print("\tparticle.firmwareVersion:", settings[1])
	        print("\tEXTRA_CFLAGS:", flags if flags else "<not set>")
	        print()
	    except FileNotFoundError:
	        raise self.UserError(projectPath + " is not a Particle project!")
	
	# Wrapper for [run]
	def run_command(self, args):
	    try:
	        self.buildCommand(args[2], 3, args)
	    except IndexError:
	        self.build_help()
	        raise self.UserError("You must supply a Makefile target!")
	
	# Wrapper for [create]
	def create_command(self, args):
	    try:
	        projectPath = os.path.abspath(args[2])
	        self.create(os.path.dirname(projectPath), os.path.basename(projectPath))
	    except IndexError:
	        raise self.UserError("You must supply a path for the project!")
	
	# Wrapper for [get]
	def get_command(self, args):
	    try:
	        self.downloadFirmware(args[2])
	    except IndexError:
	        raise self.UserError("You must specify a deviceOS version!")
	
	# Wrappers for commands that build
	def flash_command(self, args):
	    self.buildCommand("flash-user", 2, args)
	def compile_command(self, args):
	    self.buildCommand("compile-user", 2, args)
	def flash_all_command(self, args):
	    self.buildCommand("flash-all", 2, args)
	def clean_command(self, args):
	    self.buildCommand("clean-user", 2, args)
	
	# Wrapper for [install]
	def install_command(self, args):
	    try:
	        force = args[2]
	    except IndexError:
	        force = None
	    self.installOrUpdate(True, force)
	
	# Wrapper for [update]
	def update_command(self, args):
	    try:
	        force = args[2]
	    except IndexError:
	        force = None
	    self.installOrUpdate(False, force)
	
	# Wait for user to press enter [for scripting]
	def script_wait(self, args):
	    input("Press Enter to continue...")
	
	# Print a message to the console [for scripting]
	def script_print(self, args):
	    try:
	        message = args[2:]
	    except IndexError:
	        message = ""
	    print(*message)
	
	# List all scripts installed (for completion)
	def listScripts(self, args):
	    (_, _, files) = next(os.walk(self._SCRIPTS_DIR))
	    print(*files)
	
	# Copy a script file into the scripts directory
	def load(self, args):
	    try:
	        scriptPath = args[2]
	        shutil.copyfile(scriptPath, os.path.join(self._SCRIPTS_DIR, os.path.basename(scriptPath)))
	        print("Copied", scriptPath, "into", self._SCRIPTS_DIR)
	    except IndexError:
	        raise self.UserError("You must specify a script file!")
	
	# Wrapper for [script]
	def script(self, args):
	    try:
	        name = args[2]
	    except IndexError:
	        raise self.UserError("You must supply a script name!")
	
	    scriptPath = os.path.join(self._SCRIPTS_DIR, name)
	
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
	                    self.main(process)
	    except FileNotFoundError:
	        raise self.ProcessError("Could find script!")
	
	# Print all iterable options (for completion)
	def iterate_options(self, args):
	    print(*self._iterable_commands)
	
	# Available options for iterate
	_iterable_commands = {
	    "compile": compile_command,
	    "build": compile_command,
	    "flash": flash_command,
	    "flash-all": flash_all_command,
	    "clean": clean_command,
	    "run": run_command,
	    "script": script
	}
	
	# Iterate through all connected devices and run a command
	def iterate_command(self, args):
	    tempEnv = os.environ.copy()
	    self.addToPath(tempEnv, self._NEOPO_DEPS)
	
	    # Find Particle deviceIDs connected via USB
	    process = ["particle", "serial", "list"]
	    particle = subprocess.run(process, stdout=subprocess.PIPE,
	                                        env=tempEnv,
	                                        shell=self._running_on_windows)
	    devices = [line.decode("utf-8").split()[-1] for line in particle.stdout.splitlines()[1:]]
	
	    if not devices:
	        raise self.ProcessError("No devices found!")
	    
	    # Remove "iterate" from process
	    del args[1]
	
	    try:
	        if not args[1] in self._iterable_commands.keys():
	            raise self.UserError("Invalid command!")
	    except IndexError:
	        raise self.UserError("You must supply a command to iterate with!")
	
	    for device in devices:
	        print("DeviceID:", device)
	        # Put device into DFU mode
	        process = ["particle", "usb", "dfu", device]
	        subprocess.run(process, stderr=subprocess.PIPE,
	                                stdout=subprocess.PIPE,
	                                env=tempEnv,
	                                shell=self._running_on_windows)
	        # Run the iterable command
	        self._iterable_commands[args[1]](self, args)
	
	# Get EXTRA_CFLAGS for a project or return empty string
	def getFlags(self, projectPath):
	    try:
	        settingsPath = os.path.join(projectPath, self._projectFiles["settings"])
	        with open(settingsPath, "r") as file:
	            settings = json.load(file)
	        return settings["EXTRA_CFLAGS"]
	    except:
	        return ""
	
	# Set EXTRA_CFLAGS for a project
	def setFlags(self, projectPath, makeFlags):
	    settingsPath = os.path.join(projectPath, self._projectFiles["settings"])
	    with open(settingsPath, "r") as file:
	        settings = json.load(file)
	    settings["EXTRA_CFLAGS"] = makeFlags
	    with open(settingsPath, "w") as file:
	        json.dump(settings, file, indent=4)
	
	# Wrapper for [flags]
	def flags_command(self, args):
	    try:
	        makeFlags = args[2]
	    except IndexError:
	        raise self.UserError("You must provide the flags as one (quoted) string!")    
	    try:
	        project = os.path.abspath(args[3])
	    except IndexError:
	        project = os.getcwd()
	
	    self.setFlags(project, makeFlags)
	
	# Wrapper for [upgrade]
	def upgrade(self, args):
	    # This is a primitive upgrade function. Releases will be used in future.
	    url = "https://raw.githubusercontent.com/nrobinson2000/neopo/master/bin/neopo"
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
	            raise self.ProcessError("Failed to download upgrade!")
	        except PermissionError:
	            raise self.ProcessError("Failed to apply upgrade!\nTry running with sudo.")
	    else:
	        raise self.ProcessError("Neopo was not run absolutely, not upgrading.")
	
	# Wrapper for [particle]
	def particle_command(self, args):
	    process = [self._particle_cli, *args[2:]]
	    try:
	        returncode = subprocess.run(process).returncode
	    # Return cleanly if ^C was pressed
	    except KeyboardInterrupt:
	        return
	    if returncode:
	        raise self.ProcessError("Particle CLI exited with code " + str(returncode))
	            
	# Print help information about the program
	def print_help(self, args):
	    self.print_logo()
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
	
	def print_logo(self):
	    print(
r"""    ____  ___  ____  ____  ____
   / __ \/ _ \/ __ \/ __ \/ __ \    A lightweight solution for
  / / / /  __/ /_/ / /_/ / /_/ /    local Particle development.
 /_/ /_/\___/\____/ ____/\____/ 
                 /_/      .xyz      Copyright (c) 2020 Nathan Robinson
    """)
	
	def help_basic(self):
	    self.print_logo()
	    print("""Usage: neopo [OPTIONS] [PROJECT] [-v/q]
	
	Type `neopo help` to see a list of all options.
	""")
	
	# Print all commands (for completion)
	def options(self, args):
	    print(*self._commands)

	# Available options
	_commands = {
	    "help": print_help,
	    "install": install_command,
	    "uninstall": uninstall,
	    "versions": versions,
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
	    "script": script,
	    "list-scripts": listScripts,
	    "load": load,
	    "iterate": iterate_command,
	    "options-iterable": iterate_options,
	    "flags": flags_command,
	    "upgrade": upgrade,
	    "particle": particle_command,
	    "wait": script_wait,
	    "print": script_print,
	    "settings": settings_command,
	    "libs": libraries_command
	}
	
	# Evaluate command-line arguments and call necessary functions
	def main(self, args):
	    if len(args) == 1:
	        self.help_basic()
	    elif args[1] in self._commands:
	        try:
	            self._commands[args[1]](self, args)
	        except RuntimeError as e:
	            print(e)
	            exit(1)
	        except Exception as e:
	            traceback.print_exc()
	            print("An unexpected error occurred!")
	            print("To report this error on GitHub, please open an issue:")
	            print("https://github.com/nrobinson2000/neopo/issues")
	            exit(2)
	    else:
	        self.print_help(args)
	        print("Invalid command!")
	        print()
	        exit(3)
	
	# Main API for using neopo as a module
	def exec(self, args):
		if isinstance(args, str):
			args = args.split()
		try:
			# Add dummy first argument
			args = ["", *args]
			self._commands[args[1]](self, args)
		except IndexError:
			print("Expected a command!")
		except RuntimeError as e:
			print(e)
	
# Call main() with command-line arguments
if __name__ == "__main__":
	Neopo().main(sys.argv)

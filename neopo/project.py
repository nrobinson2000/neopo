import os
import json
import shutil
import pathlib
import subprocess

# Local imports
from .common import TRAVIS_YML
from .common import particle_cli, running_on_windows
from .common import ProcessError, ProjectError, UserError
from .common import projectFiles, vscodeFiles

from .utility import writeFile, checkLogin, downloadLibrary

from .manifest import loadManifest

from .toolchain import checkFirmwareVersion


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

# Wrapper for [create]
def create_command(args):
    try:
        projectPath = os.path.abspath(args[2])
        create_project(os.path.dirname(projectPath), os.path.basename(projectPath))
    except IndexError:
        raise UserError("You must supply a path for the project!")

# Wrapper for [config/configure]
def configure_command(args):
    try:
        projectPath = args[4] if len(args) >= 5 else os.getcwd()
        configure_project(projectPath, args[2], args[3])
    except IndexError:
        raise UserError("You must supply platform and deviceOS version!")

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

# Wrapper for [libs]
def libraries_command(args):
    projectPath = args[2] if len(args) >= 3 else os.getcwd()
    checkLibraries(projectPath, True)
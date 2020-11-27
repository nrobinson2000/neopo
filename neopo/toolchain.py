import os
import json
import platform

# Local imports
from .common import jsonFiles, PARTICLE_DEPS, ARM_GCC_ARM, DependencyError, UserError
from .workbench import downloadDep, attemptDownload


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
        for devicePlatform in json.load(platformFile):
            if devicePlatform[key1] == data:
                return devicePlatform[key2]
        return False

# List the supported platform IDs for a given version
def getSupportedPlatforms(version):
    with open(jsonFiles["toolchains"], "r") as toolchainsFile:
        for toolchain in json.load(toolchainsFile):
            if toolchain["firmware"] == "deviceOS@%s" % version:
                return toolchain["platforms"]
        return False

# Verify platform and deviceOS version and download deviceOS dependency if required
def checkFirmwareVersion(devicePlatform, version):
    firmware = getFirmwareData(version)
    platformID = platformConvert(devicePlatform, "name", "id")

    # Check that platform and firmware are compatible
    if not platformID:
        print("Invalid platform %s!" % devicePlatform)
        return False
    if not firmware:
        print("Invalid deviceOS version %s!" % version)
        return False
    if platformID not in getSupportedPlatforms(version):
        print("Platform %s is not supported in deviceOS version %s!" % (devicePlatform, version))
        return False

    # If required firmware is not installed, download it
    path = os.path.join(PARTICLE_DEPS, "deviceOS", version)
    if not os.path.isdir(path):
        downloadDep(firmware, False, True)
    return True

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
    if not os.path.isdir(path):
        downloadDep(getCompilerData(compilerVersion), False, True)
    return True

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

# Wrapper for [get]
def get_command(args):
    try:
        downloadFirmware(args[2])
    except IndexError as e:
        raise UserError("You must specify a deviceOS version!") from e

# Download a specific deviceOS version
def downloadFirmware(version):
    if not downloadDep(getFirmwareData(version), False, True):
        print("Could not download deviceOS version %s!" % version)

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
    except IndexError as e:
        raise UserError("You must specify a deviceOS version!") from e

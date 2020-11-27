import os
import json
import platform

# Local imports
from .common import jsonFiles, PARTICLE_DEPS, ARM_GCC_ARM, DependencyError, UserError
from .workbench import download_dep, attempt_download

# Get a deviceOS dependency from a version
def get_firmware_data(version):
    with open(jsonFiles["firmware"], "r") as firmware:
        for entry in json.load(firmware):
            if entry["version"] == version:
                return entry
        return False

# Convert between platform IDs and device names
def platform_convert(data, key1, key2):
    with open(jsonFiles["platforms"], "r") as platforms:
        for device in json.load(platforms):
            if device[key1] == data:
                return device[key2]
        return False

# List the supported platform IDs for a given version
def get_supported_platforms(version):
    with open(jsonFiles["toolchains"], "r") as toolchains:
        for toolchain in json.load(toolchains):
            if toolchain["firmware"] == "deviceOS@%s" % version:
                return toolchain["platforms"]
        return False

# Verify platform and deviceOS version and download deviceOS dependency if required
def check_firmware_version(device_platform, version):
    firmware = get_firmware_data(version)
    platform_id = platform_convert(device_platform, "name", "id")

    # Check that platform and firmware are compatible
    if not platform_id:
        print("Invalid platform %s!" % device_platform)
        return False
    if not firmware:
        print("Invalid deviceOS version %s!" % version)
        return False
    if platform_id not in get_supported_platforms(version):
        print("Platform %s is not supported in deviceOS version %s!" % (device_platform, version))
        return False

    # If required firmware is not installed, download it
    path = os.path.join(PARTICLE_DEPS, "deviceOS", version)
    if not os.path.isdir(path):
        download_dep(firmware, False, True)
    return True

# Create the path string for a given deviceOS version
def get_firmware_path(version):
    device_os_path = os.path.join(PARTICLE_DEPS, "deviceOS", version)
    legacy = os.path.join(device_os_path, "firmware-%s" % version)
    github = os.path.join(device_os_path, "device-os-%s" % version)
    return legacy if os.path.isdir(legacy) else github if os.path.isdir(github) else device_os_path

# For a given firmware version return the appropriate compiler version
def get_compiler(firmware_version):
    with open(jsonFiles["toolchains"]) as file:
        data = json.load(file)
        for toolchain in data:
            if toolchain["firmware"] == "deviceOS@%s" % firmware_version:
                return toolchain["compilers"].split("@")[1]
        raise DependencyError("Invalid firmware version!")

# Get a gcc-arm dependency from a version
def get_compiler_data(version):
    with open(jsonFiles["compilers"], "r") as compilers_file:
        data = json.load(compilers_file)
        system = platform.system().lower()
        compilers = data[system]["x64"]

        install_platform = platform.machine()
        for compiler in compilers:
            if compiler["version"] == version:
                if install_platform != "x86_64":
                    compiler["url"] = ARM_GCC_ARM[install_platform][version]["url"]
                    compiler["sha256"] = ARM_GCC_ARM[install_platform][version]["sha256"]
                return compiler
        return False

# Ensure that the requested compiler version is installed
def check_compiler(compiler_version):
    # If required compiler is not installed, download it
    path = os.path.join(PARTICLE_DEPS, "gcc-arm", compiler_version)
    if not os.path.isdir(path):
        download_dep(get_compiler_data(compiler_version), False, True)
    return True

# Print available versions and platforms
def versions_command(args):
    with open(jsonFiles["firmware"], "r") as firmware_file:
        print("Available deviceOS versions:\n")
        for entry in reversed(json.load(firmware_file)):
            version = entry["version"]
            devices = ", ".join([platform_convert(platform, "id", "name") for platform in get_supported_platforms(version)])
            print("   %s\t [ %s ]" % (version, devices))

        print("\nTo configure a project use:")
        print("\tneopo configure <platform> <version> <project>")

# Wrapper for [get]
def get_command(args):
    try:
        download_firmware(args[2])
    except IndexError as error:
        raise UserError("You must specify a deviceOS version!") from error

# Download a specific deviceOS version
def download_firmware(version):
    if not download_dep(get_firmware_data(version), False, True):
        print("Could not download deviceOS version %s!" % version)

# Attempt to download deviceOS version not specified in manifest (experimental)
def download_unlisted(version):
    # Minimum information for a firmware dependency
    firmware = {"name": "deviceOS", "version": version,
        "url": "https://binaries.particle.io/device-os/v%s.tar.gz" % version}

    try:
        # Attempt to download from Particle's download mirror
        print("Trying binaries.particle.io/device-os...")
        attempt_download(firmware)
    except DependencyError:
        # Try to download from github
        firmware["url"] = "https://github.com/particle-iot/device-os/archive/v%s.tar.gz" % version
        print("Trying github.com/particle-iot/device-os...")
        attempt_download(firmware)

# Wrapper for [download-unlisted]
def download_unlisted_command(args):
    try:
        download_unlisted(args[2])
    except IndexError as error:
        raise UserError("You must specify a deviceOS version!") from error

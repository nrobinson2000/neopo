import os
import json
import shutil
import platform
import subprocess

# Local imports
from .common import NEOPO_PARALLEL, jsonFiles, PARTICLE_DEPS, DependencyError, UserError
from .workbench import download_dep, attempt_download
from .workbench import INSTALL_RECEIPT, fix_gcc_arm, install_receipt, parallel_handler

# Attempt to get custom toolchain data from .workbench/manifest.json
def get_custom_toolchain(firmware_version, component="toolchains", all_items=False):
    firmware_path = get_firmware_path(firmware_version)
    custom_manifest = os.path.join(firmware_path, ".workbench", "manifest.json")
    if os.path.isfile(custom_manifest):
        with open(custom_manifest) as file:
            data = json.load(file)
            toolchain = data[component]
            return toolchain if all_items else toolchain[0]
    return None

# Get a deviceOS dependency from a version
def get_firmware_data(version):
    with open(jsonFiles["firmware"], "r") as firmware:
        for entry in json.load(firmware):
            if entry["version"] == version:
                return entry
        return False

# Convert between platform IDs and device names
def platform_convert(data, key1, key2, custom_version=None):
    # Custom manifest
    if custom_version:
        platforms = get_custom_toolchain(custom_version, "platforms", True)
        if platforms:
            for device in platforms:
                if device[key1] == data:
                    return device[key2]
        return False

    # Official manifest
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

    toolchain = get_custom_toolchain(version)
    return toolchain["platforms"] if toolchain else False

# Verify platform and deviceOS version and download deviceOS dependency if required
def check_firmware_version(device_platform, version):
    official = get_firmware_data(version)
    missing = check_deps_installed({"deviceOS":version})
    platform_id = platform_convert(device_platform, "name", "id",
    version if not official else None)

    # Check that platform and firmware are compatible
    if missing and not official:
        print("Invalid deviceOS version %s!" % version)
        return False
    if not platform_id:
        print("Invalid platform %s for deviceOS@%s!" % (device_platform, version))
        return False
    if platform_id not in get_supported_platforms(version):
        print("Platform %s is not supported in deviceOS version %s!" %
              (device_platform, version))
        return False

    # If required firmware is not installed, download it, along with dependencies
    download_firmware(version)
    return True

# Create the path string for a given deviceOS version
def get_firmware_path(version):
    device_os_path = os.path.join(PARTICLE_DEPS, "deviceOS", version)
    legacy = os.path.join(device_os_path, "firmware-%s" % version)
    github = os.path.join(device_os_path, "device-os-%s" % version)
    return legacy if os.path.isdir(legacy) else github if os.path.isdir(github) else device_os_path

# For a given firmware version return the appropriate compiler version
def get_compiler(firmware_version):
    return get_firmware_deps(firmware_version)["gcc-arm"]

# Print available versions and platforms
def versions_command(args):
    official_versions = set()
    with open(jsonFiles["firmware"], "r") as firmware_file:
        print("Available deviceOS versions:\n")
        for entry in reversed(json.load(firmware_file)):
            version = entry["version"]
            official_versions.add(version)
            devices = ", ".join([platform_convert(platform, "id", "name")
                                 for platform in get_supported_platforms(version)])
            print("   %s\t [ %s ]" % (version, devices))

    custom_versions = None
    device_os_path = os.path.join(PARTICLE_DEPS, "deviceOS")
    if os.path.isdir(device_os_path):
        _, installed_versions, _ = next(os.walk(device_os_path))
        custom_versions = list(set(installed_versions) - official_versions)
        custom_versions.sort()

    if custom_versions:
        print()
        print("Custom deviceOS versions:\n")
        for version in custom_versions:
            supported_platforms = get_supported_platforms(version)
            if supported_platforms:
                devices = ", ".join([platform_convert(platform, "id", "name", version)
                                     for platform in supported_platforms])
                print("   %s\t [ %s ]" % (version, devices))

    print("\nTo configure a project use:")
    print("\tneopo configure <platform> <version> [project]")

# Wrapper for [get]
def get_command(args):
    try:
        download_firmware(args[2])
    except IndexError as error:
        raise UserError("You must specify a deviceOS version!") from error

# Given a deviceOS version, get a dictionary of deps and versions
def get_firmware_deps(version):
    keys = ["compilers", "tools", "scripts", "debuggers"]
    with open(jsonFiles["toolchains"]) as toolchains:
        data = json.load(toolchains)
        for toolchain in data:
            if toolchain["firmware"] == "deviceOS@%s" % version:
                return {toolchain[key].split("@")[0]:toolchain[key].split("@")[1] for key in keys}

    toolchain = get_custom_toolchain(version)
    if toolchain:
        return {toolchain[key].split("@")[0]:toolchain[key].split("@")[1] for key in keys}
    raise DependencyError("Invalid firmware version!")

# Confirm if specified deps are installed in PARTICLE_DEPS
def check_deps_installed(deps_dict):
    missing = {}
    for (dep, version) in deps_dict.items():
        dep_path = os.path.join(PARTICLE_DEPS, dep, version)
        receipt = os.path.join(dep_path, INSTALL_RECEIPT)
        if not os.path.isdir(dep_path):
            missing.update({dep:version})
            continue
        if not os.path.isfile(receipt):
            install_receipt({"name": dep, "version": version})
    return missing

# Get the dependency data for a specified dep and version
def get_dep_data(dep, version):
    system = platform.system().lower()
    lookup = {
        "gcc-arm": jsonFiles["compilers"], "buildtools": jsonFiles["tools"],
        "buildscripts": jsonFiles["scripts"], "openocd": jsonFiles["debuggers"]}
    try:
        with open(lookup[dep]) as file:
            dep_file = json.load(file)
            section = dep_file[system]["x64"]
            dep_full = [x for x in section if x["version"] == version][0]
            if dep == "gcc-arm":
                fix_gcc_arm(dep_full)
            return dep_full
    except IndexError as error:
        raise DependencyError("Invalid dependency %s@%s!" % (dep, version)) from error

# Install specified dependencies
def install_firmware_deps(deps_dict):
    if NEOPO_PARALLEL:
        deps = [get_dep_data(dep, version) for (dep, version) in deps_dict.items()]
        parallel_handler(deps)
    else:
        for (dep, version) in deps_dict.items():
            download_dep(get_dep_data(dep, version), False, True)

# Download a specific deviceOS version (along with any of its dependencies)
def download_firmware(version):
    deps = get_firmware_deps(version)
    # deps.append(get_firmware_data(version)) #?
    missing_deps = check_deps_installed(deps)
    if missing_deps:
        install_firmware_deps(missing_deps)
    if not check_deps_installed({"deviceOS":version}):
        return
    if not download_dep(get_firmware_data(version), False, True):
        print("Could not download deviceOS version %s!" % version)

# Clone a specific tag (version) from the device-os repo
def clone_tag_from_git(version):
    repo_path = os.path.join(PARTICLE_DEPS, "deviceOS", version)
    repo_url = "https://github.com/particle-iot/device-os"
    clone_process = ["git", "clone", "--depth", "1", "-b", "v%s" % version, repo_url, repo_path]
    submodule_process = ["git", "-C", repo_path, "submodule", "update", "--init"]
    try:
        subprocess.run(clone_process, check=True)
        subprocess.run(submodule_process, check=True)
        install_receipt({"name": "deviceOS", "version": version})
        cleanup_repo(repo_path)
    except subprocess.CalledProcessError as error:
        raise DependencyError from error

# Delete uneeded files from a deviceOS release
def cleanup_repo(repo_path):
    old_pwd=os.path.abspath(os.curdir)
    os.chdir(repo_path)
    subprocess.run(["sh", "-c", "rm -rf $(find -name '.git')"], check=True)
    subprocess.run(["sh", "-c", "rm -rf $(tail +2 .bundleignore | head -n -3 | sed -e 's/^/./')"], check=True)
    os.chdir(old_pwd)

# Attempt to download deviceOS version not specified in manifest (experimental)
def download_unlisted(version, skip_mirror=False):
    # Minimum information for a firmware dependency
    firmware = {"name": "deviceOS", "version": version, "sha256": "SKIP",
                "url": "https://binaries.particle.io/device-os/v%s.tar.gz" % version}

    try:
        if skip_mirror:
            raise DependencyError()
        # Attempt to download from Particle's download mirror
        print("Trying binaries.particle.io/device-os...")
        attempt_download(firmware)
    except DependencyError:
        # Try to download from github
        print("Trying to clone v%s from GitHub..." % version)
        clone_tag_from_git(version)

# Wrapper for [download-unlisted]
def download_unlisted_command(args):
    try:
        git_flag = args[3] == "-g"
    except IndexError:
        git_flag = False

    try:
        download_unlisted(args[2], git_flag)
    except IndexError as error:
        raise UserError("You must specify a deviceOS version!") from error

# Wrapper for [remove]
def remove_command(args):
    try:
        remove_firmware(args[2])
    except IndexError as error:
        raise UserError("You must specify a deviceOS version!") from error

# Recursively delete an installed deviceOS dependency
def remove_firmware(version):
    dep_path = os.path.join(PARTICLE_DEPS, "deviceOS", version)
    if not os.path.isdir(dep_path):
        raise DependencyError("deviceOS@%s not found!" % version)

    print("Found deviceOS@%s." % version)
    try:
        answer = input("Do you want to remove this dependency? [Y/n]: ")
        if answer.lower() == "y":
            shutil.rmtree(dep_path)
            print("Removed deviceOS@%s." % version)
        else:
            print("Aborted.")
    except KeyboardInterrupt:
        print("\nInterrupt signal received.")
        return

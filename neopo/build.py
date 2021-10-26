import os
import time
import pathlib
import subprocess

# Local imports
from .common import PARTICLE_DEPS, running_on_windows, particle_cli, projectFiles
from .common import ProcessError, ProjectError, UserError, min_particle_env
from .manifest import load_manifest, get_manifest_value
from .project import get_settings, check_libraries, get_flags
from .toolchain import get_compiler, check_firmware_version, get_firmware_path, platform_convert
from .utility import write_executable

# Export a build command to a script
def export_build_process(project_path, process, environment, target):
    path = os.path.join(project_path, "bin")
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)
    script = os.path.join(path, "neopo-%s.sh" % target)

    tools = environment["PATH"].split(os.pathsep)[:-3:-1]
    path_line = 'PATH="$PATH:%s"\n' % os.pathsep.join(tools)

    # Format make line better
    temp = [" ".join(process[:3])]
    temp.extend(process[3:])
    make_lines = " \\\n".join(temp)

    content = "\n".join(["#!/bin/sh", path_line]) + "\n" + make_lines + "\n"
    write_executable(content.encode("utf-8"), script)

    print("Exported to %s" % script)

# Add a path to an environment
def add_to_path(environment, path):
    environment["PATH"] += os.pathsep + path

# Add buildtools to PATH
def add_build_tools(environment, version=None):
    tools_version = version if version else get_manifest_value("buildtools")
    toolpath = os.path.join(PARTICLE_DEPS, "buildtools", tools_version)
    toolpath = os.path.join(toolpath, "bin") if running_on_windows else toolpath
    add_to_path(environment, toolpath)

# Build and flash bootloader to connected device [WIP]
def flash_bootloader(platform, firmware_version, verbosity=1):
    bootloader_bin = build_bootloader(platform, firmware_version, verbosity)
    temp_env = min_particle_env()
    usb_listen = [particle_cli, "usb", "listen"]
    serial_flash = [particle_cli, "serial", "flash", "--yes", bootloader_bin]

    try:
        subprocess.run(usb_listen, env=temp_env, shell=running_on_windows, check=True)
        time.sleep(2) # Account for device to enter listening mode
        subprocess.run(serial_flash, env=temp_env, shell=running_on_windows, check=True)
    # Return cleanly if ^C was pressed
    except KeyboardInterrupt:
        return
    except subprocess.CalledProcessError:
        return

# Build bootloader and return path to built file [WIP]
def build_bootloader(platform, firmware_version, verbosity=1):
    compiler_version, script_version, tools_version, _ = load_manifest()

    temp_env = min_particle_env()
    add_build_tools(temp_env, tools_version)
    add_to_path(temp_env, os.path.join(
        PARTICLE_DEPS, "gcc-arm", compiler_version, "bin"))

    device_os_path = os.path.join(PARTICLE_DEPS, "deviceOS", firmware_version)
    bootloader = os.path.join(device_os_path, "bootloader")
    process = ["make", "PLATFORM=" + platform]
    verbosity != 1 and process.append("-s")

    OLDPWD = os.path.abspath(os.curdir)
    try:
        os.chdir(bootloader)
        subprocess.run(process, env=temp_env, shell=running_on_windows, check=True,
                        stdout=subprocess.PIPE if verbosity == -1 else None,
                        stderr=subprocess.PIPE if verbosity == -1 else None)
    except subprocess.CalledProcessError as error:
        pass
    finally:
        os.chdir(OLDPWD)

    platform_id = platform_convert(platform, "name", "id")

    target = os.path.join(device_os_path, "build", "target", "bootloader",
            "platform-%s-m-lto" % platform_id, "bootloader.bin")

    if os.path.isfile(target):
        return target
    else:
        raise ProcessError("%s was not built!" % target)

# Use the Makefile to build the specified target
def build_project(project_path, command, help_only, verbosity, export=False):
    compiler_version, script_version, tools_version, firmware_version = load_manifest()
    temp_env = min_particle_env()
    add_build_tools(temp_env, tools_version)

    # Windows compatibility modifications
    particle = particle_cli
    if running_on_windows:
        particle = particle.replace("C:\\", "/cygdrive/c/")
        particle = particle.replace("\\", "/")
        project_path = project_path.replace("\\", "\\\\")

    # Command used to invoke the Workbench makefile
    process = [
        "make", "-f", os.path.join(PARTICLE_DEPS,
                                   "buildscripts", script_version, "Makefile"),
        "PARTICLE_CLI_PATH=" + particle
    ]

    # Add [-s] flag to make to silence output
    if verbosity == 0:
        process[process.index("-f")] = "-sf"

    if help_only:
        process.append("help")
    else:
        try:
            device_platform, firmware_version = get_settings(project_path)
            compiler_version = get_compiler(firmware_version)

            if not check_firmware_version(device_platform, firmware_version):
                raise ProjectError("Firmware related error!")

            if not check_libraries(project_path, False):
                print("To install libraries run: $ neopo libs [project]")

        except (FileNotFoundError, KeyError) as error:
            if os.path.isfile(os.path.join(project_path, projectFiles["properties"])):
                raise ProjectError(
                    "Project not configured!\nUse: neopo configure <platform> <version> <project>") from error
            else:
                raise UserError("%s is not a Particle project!" % project_path) from error

        # Add compiler to path
        add_to_path(temp_env, os.path.join(
            PARTICLE_DEPS, "gcc-arm", compiler_version, "bin"))

        # Set additional variables for make
        device_os_path = get_firmware_path(firmware_version)
        extra_compiler_flags = get_flags(project_path)
        process.append("APPDIR=%s" % project_path)
        process.append("DEVICE_OS_PATH=%s" % device_os_path)
        process.append("PLATFORM=%s" % device_platform)
        process.append("EXTRA_CFLAGS=%s" % extra_compiler_flags)
        process.append(command)

    # Export the build process to a shell script
    if export and not help_only:
        export_build_process(project_path, process, temp_env, command)
        return

    # Run makefile with given verbosity
    try:
        subprocess.run(process, env=temp_env, shell=running_on_windows, check=True,
                        stdout=subprocess.PIPE if verbosity == -1 else None,
                        stderr=subprocess.PIPE if verbosity == -1 else None)
    except subprocess.CalledProcessError as error:
        raise ProcessError("\n*** %s FAILED ***\n" % command.upper()) from error

# Parse the project path from the specified index and run a Makefile target
def build_command(command, index, args, export=False):
    verbose_index = index
    project = None
    verbosity_dict = {"": 0, "-v": 1, "-q": -1}

    try:
        # Project specified, verbosity may follow
        if not args[index].startswith("-"):
            project = os.path.abspath(args[index])
            verbose_index += 1
        else:
            project = os.getcwd()
    except IndexError:
        # Project not specified
        project = os.getcwd()
        verbose_index = index
    try:
        # Parse verbosity to an integer
        verbosity_str = args[verbose_index]
        verbosity = verbosity_dict[verbosity_str]
    except IndexError:
        # Verbosity not specified, use default
        verbosity = 0
    except KeyError as error:
        raise UserError("Invalid verbosity!") from error

    # Build the given project with a command and verbosity
    build_project(project, command, False, verbosity, export)

# Print help information directly from Makefile
def build_help():
    build_project(None, None, True, 0)

# Wrapper for [run]
def run_command(args, export=False):
    try:
        build_command(args[2], 3, args, export)
    except IndexError as error:
        build_help()
        raise UserError("You must supply a Makefile target!") from error

# Wrappers for commands that build
def flash_command(args):
    build_command("flash-user", 2, args)

def compile_command(args):
    build_command("compile-user", 2, args)

def flash_all_command(args):
    build_command("flash-all", 2, args)

def clean_command(args):
    build_command("clean-user", 2, args)

# Wrapper for export
def export_command(args):
    run_command(args, True)

# Wrapper for flash-bootloader
def flash_bootloader_command(args):
    try:
        device_platform = args[2]
        firmware_version = args[3]
    except IndexError as error:
        raise UserError("You must specify platform and device os version!")

    verbosity_dict = {None: 0, "-v": 1, "-q": -1}
    try:
        verbosity = args[4]
    except IndexError:
        verbosity = None
    verbosity_level=verbosity_dict[verbosity]

    if not check_firmware_version(device_platform, firmware_version):
        raise ProjectError("Firmware related error!")

    flash_bootloader(device_platform, firmware_version, verbosity_level)

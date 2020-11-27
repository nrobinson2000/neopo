import os
import subprocess

# Local imports
from .common import PARTICLE_DEPS, running_on_windows, particle_cli, projectFiles
from .common import ProcessError, ProjectError, UserError
from .manifest import load_manifest, get_manifest_value
from .project import get_settings, check_libraries, get_flags
from .toolchain import get_compiler, check_firmware_version, check_compiler, get_firmware_path

# Add a path to an environment
def add_to_path(environment, path):
    environment["PATH"] += os.pathsep + path

# Add buildtools to PATH
def add_build_tools(environment, version=None):
    tools_version = version if version else get_manifest_value('buildtools')
    toolpath = os.path.join(PARTICLE_DEPS, "buildtools", tools_version)
    toolpath = os.path.join(toolpath, "bin") if running_on_windows else toolpath
    add_to_path(environment, toolpath)

# Use the Makefile to build the specified target
def build_project(project_path, command, help_only, verbosity):
    compiler_version, script_version, tools_version, firmware_version = load_manifest()
    temp_env = os.environ.copy()
    add_build_tools(temp_env, tools_version)

    # Windows compatibility modifications
    particle = particle_cli
    if running_on_windows:
        particle = particle.replace("C:\\", "/cygdrive/c/")
        particle = particle.replace("\\", "/")
        project_path = project_path.replace("\\", "\\\\")

    # Command used to invoke the Workbench makefile
    process = [
        "make", "-f", os.path.join(PARTICLE_DEPS, "buildscripts", script_version, "Makefile"),
        "PARTICLE_CLI_PATH=" + particle
    ]

    # Add [-s] flag to make to silence output
    if verbosity == 0:
        process.append("-s")

    if help_only:
        process.append("help")
    else:
        try:
            device_platform, firmware_version = get_settings(project_path)
            compiler_version = get_compiler(firmware_version)

            if not check_firmware_version(device_platform, firmware_version):
                raise ProjectError("Firmware related error!")

            if not check_compiler(compiler_version):
                raise ProjectError("Compiler related error!")

            if not check_libraries(project_path, False):
                print("To install libraries run: $ neopo libs [project]")

        except (FileNotFoundError, KeyError) as error:
            if os.path.isfile(os.path.join(project_path, projectFiles["properties"])):
                raise ProjectError("Project not configured!\nUse: neopo configure <platform> <version> <project>") from error
            else:
                raise UserError("%s is not a Particle project!" % project_path) from error

        # Add compiler to path
        add_to_path(temp_env, os.path.join(PARTICLE_DEPS, "gcc-arm", compiler_version, "bin"))

        # Set additional variables for make
        device_os_path = get_firmware_path(firmware_version)
        extra_compiler_flags = get_flags(project_path)
        process.append("APPDIR=%s" % project_path)
        process.append("DEVICE_OS_PATH=%s" % device_os_path)
        process.append("PLATFORM=%s" % device_platform)
        process.append("EXTRA_CFLAGS=%s" % extra_compiler_flags)
        process.append(command)

    # Run makefile with given verbosity
    returncode = subprocess.run(process, env=temp_env,
                                shell=running_on_windows,
                                stdout= subprocess.PIPE if verbosity == -1 else None,
                                stderr= subprocess.PIPE if verbosity == -1 else None,
                                check=True
                                ).returncode
    if returncode:
        raise ProcessError("Failed with code %s" % returncode)

# Parse the project path from the specified index and run a Makefile target
def build_command(command, index, args):
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
    build_project(project, command, False, verbosity)

# Print help information directly from Makefile
def build_help():
    build_project(None, None, True, 0)

# Wrapper for [run]
def run_command(args):
    try:
        build_command(args[2], 3, args)
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

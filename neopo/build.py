import os
import subprocess



# Local imports
from .common import PARTICLE_DEPS, running_on_windows, particle_cli, projectFiles
from .common import ProcessError, ProjectError, UserError

from .manifest import loadManifest

from .project import getSettings, checkLibraries, getFlags

from .toolchain import getCompiler, checkFirmwareVersion, checkCompiler, getFirmwarePath



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


# Available options for iterate
# iterable_commands = {
#     "compile": compile_command,
#     "build": compile_command,
#     "flash": flash_command,
#     "flash-all": flash_all_command,
#     "clean": clean_command,
#     "run": run_command,
#     "script": script_command
# }

# Print help information directly from Makefile
def build_help():
    build_project(None, None, True, 0)

# Wrapper for [run]
def run_command(args):
    try:
        buildCommand(args[2], 3, args)
    except IndexError:
        build_help()
        raise UserError("You must supply a Makefile target!")

# Wrappers for commands that build
def flash_command(args):
    buildCommand("flash-user", 2, args)
def compile_command(args):
    buildCommand("compile-user", 2, args)
def flash_all_command(args):
    buildCommand("flash-all", 2, args)
def clean_command(args):
    buildCommand("clean-user", 2, args)
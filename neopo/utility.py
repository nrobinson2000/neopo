import os
import sys
import stat
import subprocess
import traceback

# Local imports
from .common import particle_cli, running_on_windows, ProcessError
from .common import PARTICLE_DEPS, NEOPO_DEPS, CACHE_DIR, min_particle_env

from .help_info import get_help

# Write data to a file
def write_file(content, path, mode):
    with open(path, mode) as file:
        file.write(content)

# Write an executable dependency to a file
def write_executable(content, path):
    with open(path, "wb") as file:
        file.write(content)
        file_stat = os.stat(file.name)
        os.chmod(file.name, file_stat.st_mode | stat.S_IEXEC)

# Ensure that the user is logged into particle-cli
def check_login():
    process = [particle_cli, "whoami"]
    try:
        subprocess.run(process, shell=running_on_windows, env=min_particle_env(),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError:
        return False
    return True

# Download a library using particle-cli
def download_library(library, version):
    process = [particle_cli, "library", "copy", "%s@%s" % (library, version)]
    try:
        subprocess.run(process, shell=running_on_windows, env=min_particle_env(), check=True)
    except subprocess.CalledProcessError as error:
        raise ProcessError("Failed to download library %s@%s!" % (library, version)) from error

# Print help information about the program
def print_help(args):
    try:
        command = args[2]
        get_help(command)
        return
    except IndexError:
        pass
    except TypeError:
        pass

    print_logo()
    print("""Usage: neopo [OPTIONS] [PROJECT] [-v/q]
Help:  neopo help <command>
    
Refer to the manual for more detailed help: 
  $ man neopo

  General Commands:
      help | --help           # Show this help information
      install [-f/s]          # Install dependencies [force or skip]
      update                  # Update neopo dependencies
      versions                # List available versions and platforms
      get <version>           # Download a specific deviceOS version
      remove <version>        # Delete an installed deviceOS version
      particle [OPTIONS]      # Use the encapsulated Particle CLI

  Build Commands:
      compile | build [project] [-v/q]  # Compile application (local)
      flash [project] [-v/q]            # Flash application (local)
      flash-all [project] [-v/q]        # Flash application and DeviceOS
      clean [project] [-v/q]            # Clean application

  Special Commands:
      create <project> [platform] [version]     # Create a Particle project
      configure <platform> <version> [project]  # Configure a Particle project
      run <target> [project] [-v/q]             # Run a makefile target
      export <target> [project] [-v/q]          # Export target to a script
      flags <string> [project]                  # Set EXTRA_CFLAGS in a project 
      settings [project]                        # View configured settings
      libs [project]                            # Install Particle libraries
      iterate <command> [OPTIONS] [-v/q]        # Put devices into DFU mode
                                                # and run commands on them
  Script Commands:
      script [file]       # Execute a script or read a script from stdin
      print [message]     # Print a message to the console
      wait                # Wait for the user to press ENTER
""")


def print_logo():
    print(
        r"""    ____  ___  ____  ____  ____
   / __ \/ _ \/ __ \/ __ \/ __ \    A lightweight solution for
  / / / /  __/ /_/ / /_/ / /_/ /    local Particle development.
 /_/ /_/\___/\____/ ____/\____/
                 /_/      .xyz      Copyright (c) 2021 Nathan Robinson
    """)

# Print traceback and message for unhandled exceptions
def unexpected_error():
    traceback.print_exc()
    print("An unexpected error occurred!")
    print("To report this error on GitHub, please open an issue:")
    print("https://github.com/nrobinson2000/neopo/issues")
    sys.exit(1)

# Check if a missing file is managed by neopo
def handle_missing_file(file):
    dirs = [PARTICLE_DEPS, NEOPO_DEPS, CACHE_DIR]
    for directory in dirs:
        if file.startswith(directory):
            print("Error: file %s not found." % file)
            print("Please ensure that you have installed the dependencies:")
            print("\t$ neopo install")
            sys.exit(1)
    unexpected_error()

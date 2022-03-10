import os
import sys
import stat
import subprocess
import traceback

import io
import urllib.request
import tarfile
import pathlib
import xml.etree.ElementTree as ET

# Local imports
from .common import particle_cli, running_on_windows, ProcessError
from .common import PARTICLE_DEPS, NEOPO_DEPS, CACHE_DIR, min_particle_env
from .common import s3_bucket, s3_prefix

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

def search(lib_query):
    request = urllib.request.Request(
        s3_bucket + s3_prefix + lib_query)
    with urllib.request.urlopen(request) as response:
        content = response.read()
        return io.BytesIO(content)

def get_keys(byte_file):
    tree = ET.parse(byte_file)
    keys = [e.text for e in tree.iter() if e.tag.endswith('Key')]
    return keys

def get_library(name, version, keys):
    combo = "%s-%s" % (name, version)
    for key in keys:
        if combo in key:
            return key
    return None

def install_library(name, version, project_path):
    data = search(name)
    keys = get_keys(data)
    lib = get_library(name, version, keys)
    if not lib:
        raise ProcessError("Library %s@%s not found!" % (name, version))
    library_url = s3_bucket + lib
    print("Downloading library %s@%s..." % (name, version))
    download_library_archive(library_url, name, project_path)

def download_library_archive(url, name, project_path):
    base = os.path.join(project_path, "lib")
    path = os.path.join(base, name)
    archive = os.path.join(base, name + ".tar.gz")
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url)
    with urllib.request.urlopen(request) as response:
        content = response.read()
    with open(archive, "wb") as gz_file:
        gz_file.write(content)
    with tarfile.open(archive, "r:gz") as tar:
        tar.extractall(path)
    os.remove(archive)

def download_library(library, project_path):
    name, version = library
    install_library(name, version, project_path)

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

  Project Commands:
      create <project> [platform] [version]     # Create a Particle project
      configure <platform> <version> [project]  # Configure a Particle project
      run <target> [project] [-v/q]             # Run a makefile target
      export <target> [project] [-v/q]          # Export target to a script
      flags <string> [project]                  # Set EXTRA_CFLAGS in a project 
      settings [project]                        # View configured settings
      libs [project]                            # Install Particle libraries

  Special Commands:
      bootloader <platform> <version> [-v/-q]   # Flash device bootloader
      iterate <command> [OPTIONS] [-v/q]        # Put devices into DFU mode
                                                # and run commands on them
      legacy <command>                          # Put legacy devices into
                                                # serial or DFU mode
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

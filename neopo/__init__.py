# neopo: A lightweight solution for local Particle development.
# Copyright (c) 2020 Nathan Robinson.
# https://neopo.xyz


# Disable RuntimeWarning when using modules from packages
# Example:
# python3 -m neopo.particle
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

import os

# Local imports
from .utility import print_help, responsible, unexpected_error
from .workbench import install_or_update
from .toolchain import versions_command, get_command, download_unlisted_command
from .project import create_command, configure_command, flags_command, settings_command, libraries_command
from .build import compile_command, flash_command, flash_all_command, clean_command, run_command
from .completion import versions_compressed, platforms_command, find_valid_projects, get_makefile_targets
from .iterate import iterate_command, iterate_options
from .particle import particle_command
from .script import script_command
from .command import commands, upgrade_command, uninstall_command

# Main API for using neopo as a module
def main(args):
    if isinstance(args, str):
        args = args.split()
    try:
        # Add dummy first argument
        args = ["", *args]
        commands[args[1]](args)
    except IndexError:
        print("Expected a command!")
    except RuntimeError as error:
        print(error)

### General options

def info():
    print_help(None)

def install(force = False):
    install_or_update(True, force)

def upgrade():
    upgrade_command(None)

def uninstall():
    uninstall_command(None)

def versions():
    versions_command(None)

def create(project_path = os.getcwd()):
    create_command([None, None, project_path])

def particle(args = None):
    if isinstance(args, str):
        args = args.split()
    if not args:
        args = []
    particle_command([None, None, *args])

### Build options

def build(project_path = os.getcwd(), verbosity = ""):
    compile_command([None, None, project_path, verbosity])

def flash(project_path = os.getcwd(), verbosity = ""):
    flash_command([None, None, project_path, verbosity])

def flash_all(project_path = os.getcwd(), verbosity = ""):
    flash_all_command([None, None, project_path, verbosity])

def clean(project_path = os.getcwd(), verbosity = ""):
    clean_command([None, None, project_path, verbosity])

### Special options

def run(target, project_path = os.getcwd(), verbosity = ""):
    run_command([None, None, target, project_path, verbosity])

def configure(platform, version, project_path = os.getcwd()):
    configure_command([None, None, platform, version, project_path])

def flags(flags_str, project_path = os.getcwd()):
    flags_command([None, None, flags_str, project_path])

def settings(project_path = os.getcwd()):
    settings_command([None, None, project_path])

def libs(project_path = os.getcwd()):
    libraries_command([None, None, project_path])

def iterate(args, verbosity = ""):
    iterate_command([None, None, *args, verbosity])

### Script options

def script(script_name):
    script_command([None, None, script_name])

### Dependency options

def update():
    install_or_update(False, False)

def get(version):
    get_command([None, None, version])

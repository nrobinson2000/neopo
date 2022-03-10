# Driver script for neopo module

import os

# Local imports
from .command import iterate_command, script_command, get_command
from .command import configure_command, flags_command, settings_command, libraries_command
from .command import compile_command, flash_command, flash_all_command, clean_command, run_command
from .command import uninstall_command, versions_command, create_command, particle_command
from .command import commands, print_help, install_or_update, upgrade_command
from .command import legacy_command

# Main API for using neopo as a module
def main(args=None):
    if not args:
        print_help(None)
        return
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

# General options

def install(force=False, skip=False):
    install_or_update(True, force, skip)

def upgrade():
    upgrade_command(None)

def uninstall():
    uninstall_command(None)

def versions():
    versions_command(None)

def create(project_path=os.getcwd(), platform=None, version=None):
    create_command([None, None, project_path, platform, version])

def particle(args=None):
    if isinstance(args, str):
        args = args.split()
    if not args:
        args = []
    particle_command([None, None, *args])

# Build options
def build(project_path=os.getcwd(), verbosity=""):
    compile_command([None, None, project_path, verbosity])

def flash(project_path=os.getcwd(), verbosity=""):
    flash_command([None, None, project_path, verbosity])

def flash_all(project_path=os.getcwd(), verbosity=""):
    flash_all_command([None, None, project_path, verbosity])

def clean(project_path=os.getcwd(), verbosity=""):
    clean_command([None, None, project_path, verbosity])

# Special options
def run(target, project_path=os.getcwd(), verbosity=""):
    run_command([None, None, target, project_path, verbosity])

def configure(platform, version, project_path=os.getcwd()):
    configure_command([None, None, platform, version, project_path])

def flags(flags_str, project_path=os.getcwd()):
    flags_command([None, None, flags_str, project_path])

def settings(project_path=os.getcwd()):
    settings_command([None, None, project_path])

def libs(project_path=os.getcwd()):
    libraries_command([None, None, project_path])

def iterate(args, verbosity=""):
    iterate_command([None, None, *args, verbosity])

def legacy(args):
    legacy_command([None, None, *args])

# Script options
def script(script_name):
    script_command([None, None, script_name])

# Dependency options
def update():
    install_or_update(False, False, False)

def get(version):
    get_command([None, None, version])

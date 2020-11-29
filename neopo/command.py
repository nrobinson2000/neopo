import os
import sys
import subprocess

# Local imports
from .common import NEOPO_DEPS
from .common import ProcessError, UserError, particle_cli, running_on_windows
from .utility import print_help, responsible, unexpected_error
from .workbench import install_or_update, workbench_install
from .toolchain import versions_command, get_command, download_unlisted_command
from .project import create_command, configure_command, flags_command, settings_command, libraries_command
from .build import compile_command, flash_command, flash_all_command, clean_command, run_command
from .completion import versions_compressed, platforms_command, find_valid_projects, get_makefile_targets
from .particle import particle_command

# Print all commands (for completion)
def options(args):
    print(*commands)

# Wrapper for [install]
def install_command(args):
    try:
        force = args[2] == "-f"
    except IndexError:
        force = None
    install_or_update(True, force)

# Wrapper for [update]
def update_command(args):
    try:
        force = args[2] == "-f"
    except IndexError:
        force = None
    install_or_update(False, force)

# Wrapper for [upgrade]
def upgrade_command(args):
    print("This command is deprecated because neopo is now installed using pip or the AUR.")
    print("To upgrade neopo, either rerun the universal installer, or follow distribution\nspecific instructions.")

# Provide information for how to uninstall neopo
def uninstall_command(args):
    print("This command is deprecated because neopo is now installed using pip or the AUR.")
    print("To uninstall neopo from your system run:")
    print("\t$ sudo pip3 uninstall neopo")
    print()
    print("If you want to delete the neopo and particle directories you can do so with:")
    print("\t$ rm -rf ~/.neopo ~/.particle")

# Wait for user to press enter [for scripting]
def script_wait(args=None):
    input("Press Enter to continue...")

# Print a message to the console [for scripting]
def script_print(args):
    try:
        message = args[2:]
    except IndexError:
        message = ""
    print(*message)

# Wrapper for [script]
def script_command(args):
    try:
        name = args[2]
        script = open(name, "r")
    except IndexError as error:
        script = sys.stdin
        if script.isatty():
            # Correct message depending on invocation
            exec_name = args[1]
            exec_name = "neopo-script" if exec_name.endswith(
                "script.py") else "neopo script"
            raise ProcessError("Usage:\n\t$ %s <file>\n\t$ <another process> | %s" % (
                exec_name, exec_name)) from error
    except FileNotFoundError as error:
        raise ProcessError("Could not find script %s!" % name) from error

    # Open the script and execute each line
    for line in script.readlines():
        line = line.rstrip()
        # Skip comments
        if line.startswith("#"):
            continue

        # Run the process just like a regular invocation, skip empty lines
        process = [args[0], *line.split()]
        if len(process) > 1:
            main(process)

# Available options for iterate
iterable_commands = {
    "compile": compile_command,
    "build": compile_command,
    "flash": flash_command,
    "flash-all": flash_all_command,
    "clean": clean_command,
    "run": run_command,
    "script": script_command
}

# Iterate through all connected devices and run a command
def iterate_command(args):
    # Find Particle deviceIDs connected via USB
    process = [particle_cli, "serial", "list"]
    particle = subprocess.run(process, stdout=subprocess.PIPE,
                              shell=running_on_windows, check=True)
    devices = [line.decode("utf-8").split()[-1]
               for line in particle.stdout.splitlines()[1:]]

    if not devices:
        raise ProcessError("No devices found!")

    # Remove "iterate" from process
    del args[1]

    try:
        if not args[1] in iterable_commands.keys():
            raise UserError("Invalid command!")
    except IndexError as error:
        raise UserError(
            "You must supply a command to iterate with!") from error

    for device in devices:
        print("DeviceID: %s" % device)
        # Put device into DFU mode
        process = [particle_cli, "usb", "dfu", device]
        subprocess.run(process, stderr=subprocess.PIPE,
                       stdout=subprocess.PIPE,
                       shell=running_on_windows, check=True)
        # Run the iterable command
        iterable_commands[args[1]](args)

# Print all iterable options (for completion)
def iterate_options(args):
    print(*iterable_commands)

# Run POSTINSTALL setup script for Manjaro/Arch
def setup_command(args):
    # Check for lock file in ~/.neopo to discourage
    # running setup_command multiple times
    lock_file = os.path.join(NEOPO_DEPS, ".setupdone")
    if os.path.isfile(lock_file):
        print("Setup has already been performed on this system!")
        return
    if os.path.isdir(NEOPO_DEPS):
        with open(lock_file, "w") as lock:
            lock.writelines([
            "This file is used internally by neopo to recall if setup has been performed.\n",
            "If you delete this file you can reattempt setup with: neopo setup\n"])

    # Check for POSTINSTALL script
    post_install = "/usr/share/neopo/scripts/POSTINSTALL"
    if not os.path.isfile(post_install):
        print("POSTINSTALL script not found!")
        return

    # Run the POSTINSTALL script
    try:
        process = ["bash", "-x", post_install]
        subprocess.run(process, check=True)
    except subprocess.CalledProcessError as error:
        os.remove(lock_file)
        raise ProcessError("POSTINSTALL failed!") from error

# Available options
commands = {
    "help": print_help,
    "install": install_command,
    "uninstall": uninstall_command,
    "versions": versions_command,
    "create": create_command,
    "compile": compile_command,
    "build": compile_command,
    "flash": flash_command,
    "flash-all": flash_all_command,
    "clean": clean_command,
    "run": run_command,
    "configure": configure_command,
    "update": update_command,
    "get": get_command,
    "list-versions": versions_compressed,
    "platforms": platforms_command,
    "projects": find_valid_projects,
    "targets": get_makefile_targets,
    "options": options,
    "download-unlisted": download_unlisted_command,
    "script": script_command,
    "iterate": iterate_command,
    "options-iterable": iterate_options,
    "flags": flags_command,
    "upgrade": upgrade_command,
    "particle": particle_command,
    "wait": script_wait,
    "print": script_print,
    "settings": settings_command,
    "libs": libraries_command,
    "setup": setup_command,
    "setup-workbench": workbench_install
}

# Evaluate command-line arguments and call necessary functions
def main(args):
    if len(args) == 1:
        print_help(None)
    elif args[1] in commands:
        try:
            commands[args[1]](args)
        except FileNotFoundError as error:
            file = error.filename
            if responsible(file):
                print("Error: file %s not found." % file)
                print("Please ensure that you have installed the dependencies:")
                print("\t$ neopo install")
            else:
                unexpected_error()
        except RuntimeError as error:
            print(error)
            sys.exit(1)
        except Exception as error:
            unexpected_error()
            sys.exit(2)
    else:
        print_help(args)
        print("Invalid command!")
        print()
        sys.exit(3)

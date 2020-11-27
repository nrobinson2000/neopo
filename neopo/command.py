import sys

# Local imports
from .common import ProcessError
from .utility import print_help, responsible, unexpected_error
from .workbench import install_or_update
from .toolchain import versions_command, get_command, download_unlisted_command
from .project import create_command, configure_command, flags_command, settings_command, libraries_command
from .build import compile_command, flash_command, flash_all_command, clean_command, run_command
from .completion import versions_compressed, platforms_command, find_valid_projects, get_makefile_targets
from .iterate import iterate_command, iterate_options
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
    "libs": libraries_command
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

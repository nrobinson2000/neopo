
# Local imports
from .utility import print_help, responsible, unexpectedError
from .workbench import installOrUpdate
from .toolchain import versions_command, get_command, downloadUnlisted_command
from .project import create_command, configure_command, flags_command, settings_command, libraries_command
from .build import compile_command, flash_command, flash_all_command, clean_command, run_command
from .completion import versions_compressed, platforms_command, findValidProjects, getMakefileTargets

# from script import script_command, script_print, script_wait

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
    installOrUpdate(True, force)

# Wrapper for [update]
def update_command(args):
    try:
        force = args[2] == "-f"
    except IndexError:
        force = None
    installOrUpdate(False, force)

# Wrapper for [upgrade]
# TODO: Deprecate, since using pip/pacman
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
    "projects": findValidProjects,
    "targets": getMakefileTargets,
    "options": options,
    "download-unlisted": downloadUnlisted_command,
    # "script": script_command,
    "iterate": iterate_command,
    "options-iterable": iterate_options,
    "flags": flags_command,
    "upgrade": upgrade_command,
    "particle": particle_command,
    # "wait": script_wait,
    # "print": script_print,
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
        except FileNotFoundError as e:
            file = e.filename
            if responsible(file):
                print("Error: file %s not found." % file)
                print("Please ensure that you have installed the dependencies:")
                print("\t$ neopo install")
            else:
                unexpectedError()
        except RuntimeError as e:
            print(e)
            exit(1)
        except Exception as e:
            unexpectedError()
            exit(2)
    else:
        print_help(args)
        print("Invalid command!")
        print()
        exit(3)
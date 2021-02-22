help_commands = {
    # Meta commands
    "--version": "",
    "--help": "",
    "help": "",
    # General commands
    "install": (
        "Install neopo dependencies",
        None,
        [("-f", "Force installation of all"), ("-s", "Skip installation of all")],
    ),
    "update": "",
    "versions": "",
    "get": "",
    "remove": "",
    "particle": "",
    # Build commands
    "compile": "",
    "build": "",
    "flash": "",
    "flash-all": "",
    "clean": "",
    # Special commands
    "create": "",
    "configure": "",
    "run": "",
    "export": "",
    "flags": "",
    "settings": "",
    "libs": "",
    "iterate": "",
    # Script commands
    "script": "",
    "wait": "",
    "print": "",
    # Unlisted
    "setup": "",
    "setup-workbench": "",
    # Backend
    "list-versions": "",
    "platforms": "",
    "projects": "",
    "targets": "",
    "options": "",
    "download-unlisted": "",
    "options-iterable": "",
    # Deprecated
    "uninstall": "",
    "upgrade": "",
}

# Print description, usage, commands, and options for a command
def get_help(command):
    try:
        command_info = help_commands[command]
    except KeyError:
        print("Unknown command!")

    description = command_info[0]
    subcommands = command_info[1]
    options = command_info[2]

    print(description)
    print("Usage: neopo %s" % command)

    if subcommands:
        print()
        print("Commands:")
        for entry in subcommands:
            print("  %s\t%s" % entry)

    if options:
        print()
        print("Options:")
        for entry in options:
            print("  %s\t%s" % entry)

    print()

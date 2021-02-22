help_commands = {
    # Meta commands
    "--version": ["Print the installed version of neopo"],
    "--help": ["Equivalent to `neopo help`"],
    "help": [
        "Print general help information or help for a specific neopo command",
        "[command]",
        None,
        None,
    ],
    # General commands
    "install": [
        "Install neopo dependencies and Particle toolchains to ~/.neopo and ~/.particle",
        "[option]",
        None,
        [
            (
                "-f",
                "Force reinstallation of all dependencies, restoring to original state.",
            ),
            (
                "-s",
                "Skip installation of all dependencies. Useful for containers and CI/CD.",
            ),
        ],
    ],
    "update": [
        "Update neopo dependencies and Particle toolchains to the latest versions"
    ],
    "versions": ["List downloadable DeviceOS versions and their supported platforms"],
    "get": [
        "Download a specific DeviceOS version and required toolchains",
        "<version>",
    ],
    "remove": [
        "Delete a specific DeviceOS version from ~/.particle/toolchains",
        "<version>",
    ],
    "particle": [
        "Access Particle CLI to run particle commands; also available as `particle`",
        "[options] [command...]",
    ],
    # Build commands
    "compile": [
        "Compile the current or specified project locally",
        "[project] [verbosity]",
        None,
        [
            ("-v", "Verbose compiler output"),
            ("-q", "Quiet compiler output"),
        ],
    ],
    "build": [
        "Compile the current or specified project locally",
        "[project] [verbosity]",
        None,
        [
            ("-v", "Verbose compiler output"),
            ("-q", "Quiet compiler output"),
        ],
    ],
    "flash": [
        "Compile and flash the current or specified project locally",
        "[project] [verbosity]",
        None,
        [
            ("-v", "Verbose compiler output"),
            ("-q", "Quiet compiler output"),
        ],
    ],
    "flash-all": [
        "Compile and flash the current or specified project and DeviceOS",
        "[project] [verbosity]",
        None,
        [
            ("-v", "Verbose compiler output"),
            ("-q", "Quiet compiler output"),
        ],
    ],
    "clean": [
        "Clean the current or specified project locally",
        "[project] [verbosity]",
        None,
        [
            ("-v", "Verbose compiler output"),
            ("-q", "Quiet compiler output"),
        ],
    ],
    # Special commands
    "create": [
        "Initialize and configure a Particle project compatible with official tools",
        "<project> [platform] [version]",
    ],
    "configure": [
        """Change the platform and DeviceOS version used in a project, verifying
compatibility and downloading toolchains if necessary. If used with a basic
Particle CLI project, the project is upgraded with Workbench and neopo support.\n""",
        "<platform> <version> [project]",
    ],
    "run": [
        "Execute a specific target from the Workbench Makefile.\nTo reveal targets run: `neopo targets`",
        "<target> [project] [verbosity]",
        None,
        [
            ("-v", "Verbose compiler output"),
            ("-q", "Quiet compiler output"),
        ],
    ],
    "export": [
        """Export a makefile target to a shell script in the bin/ directory of a project,
making it possible to use the Particle toolchains without requiring neopo.\n""",
        "<target> [project] [verbosity]",
        None,
        [
            ("-v", "Verbose compiler output"),
            ("-q", "Quiet compiler output"),
        ],
    ],
    "flags": [
        "Set the EXTRA_CFLAGS variable in a project which neopo passes to the compiler",
        "<quoted string> [project]",
    ],
    "settings": [
        "View configured settings in a project.\nIncludes platform, version, and EXTRA_CFLAGS",
        "[project]",
    ],
    "libs": [
        """Parse the project.properties file in a Particle project and install specified
libraries in the lib/ directory of the current or specifed project.\n""",
        "[project]",
    ],
    "iterate": [
        """Iterate over all Particle devices connected via USB, placing each device into
DFU mode and running a command on the device.\n""",
        "<command> [OPTIONS] [verbosity]",
        [
            ("compile", "Locally compile, flash, or clean a project"),
            ("build", ""),
            ("flash", ""),
            ("flash-all", ""),
            ("clean", ""),
            ("run", "\tExecute a specific makefile target"),
            ("script", "Load and execute a neopo script"),
            ("particle", "Access Particle CLI (Extemely useful)"),
        ],
    ],
    # Script commands
    "script": [
        "Load and execute a neopo script from a file or standard input",
        "[file]",
    ],
    "print": [
        "Print a message to the console. Intended for neopo scripts.",
        "[message]",
    ],
    "wait": ["Prompt and wait for user interaction. Intended for neopo scripts."],
    # Unlisted
    "setup": ["Run the optional post-install setup script for Linux"],
    "setup-workbench": ["Install Particle Workbench extensions in Visual Studio Code"],
    # Completion
    "list-versions": [],
    "platforms": [],
    "projects": [],
    "targets": [],
    "options": [],
    "options-iterable": [],
    # Deprecated
    "download-unlisted": [],
    "uninstall": [],
    "upgrade": [],
}

# Print description, usage, commands, and options for a command
def get_help(command):
    try:
        command_info = help_commands[command]
    except KeyError:
        print("Unknown command!")
        return

    description = usage = subcommands = options = None
    try:
        description = command_info[0]
        usage = command_info[1]
        subcommands = command_info[2]
        options = command_info[3]
    except IndexError:
        pass

    if description:
        print(description)
    else:
        print("No decription provided. Likely used for bash completion or deprecated.")

    if usage:
        print("Usage: neopo %s %s" % (command, usage))
    else:
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

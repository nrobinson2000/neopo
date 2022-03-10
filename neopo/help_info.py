help_commands = {
    # Meta commands
    "--version": ["Print the installed version of neopo"],
    "--help": ["Equivalent to `neopo help`"],
    "help": [
        "Print general help information or help for a specific neopo command",
        "[command]",
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
    "versions": ["List downloadable Device OS versions and their supported platforms"],
    "get": [
        "Download a specific Device OS version and required toolchains",
        "<version>",
    ],
    "remove": [
        "Delete a specific Device OS version from ~/.particle/toolchains",
        "<version>",
    ],
    "particle": [
        "Access Particle CLI to run particle commands. (Also available as `particle`)",
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
        "Compile and flash the current or specified project and Device OS",
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
    # Project commands
    "create": [
        "Initialize and configure a Particle project compatible with official tools",
        "<project> [platform] [version]",
    ],
    "configure": [
        """Change the platform and Device OS version used in a project, verifying
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
libraries in the lib/ directory of the current or specified project.\n""",
        "[project]",
    ],
    # Special commands
    "bootloader": [
        """Build and flash the bootloader for a specific platform and Device OS version.
After building the bootloader it is flashed over serial using particle-cli.\n""",
        "<platform> <version> [verbosity]",
        None,
        [
            ("-v", "Verbose compiler output"),
            ("-q", "Quiet compiler output"),
        ],
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
    "legacy": [
        """Run legacy commands for controlling serial and DFU modes on old deviceOS versions
for gen 2 devices. Only available on Linux and macOS at this time.\n""",
        "<command>",
        [
            ("serial open", "open serial mode on older devices"),
            ("serial close", "exit serial mode on older devices"),
            ("dfu open", "open DFU mode on older devices"),
            ("dfu close", "exit DFU mode on older devices"),
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
    "list-versions": ["Print all Device OS versions. (For bash completion.)"],
    "platforms": ["Print all device platforms. (For bash completion.)"],
    "projects": ["Find Particle projects relative to PWD. (For bash completion.)"],
    "targets": ["Print all targets available for `neopo run`. (For bash completion.)"],
    "options": ["Print all neopo commands. (For bash completion.)"],
    "options-iterable": [
        "Print all commmands supported by `neopo iterate`. (For bash completion)."
    ],
    # Deprecated
    "download-unlisted": [
        "Attempt to download an unlisted Device OS release. (Deprecated)",
        "<version>",
    ],
    "uninstall": ["Print information about uninstalling neopo. (Deprecated)"],
    "upgrade": ["Print information about upgrading neopo. (Deprecated)"],
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

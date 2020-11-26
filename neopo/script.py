import sys

# Local imports
from .common import ProcessError
from .command import main

# Wait for user to press enter [for scripting]
def script_wait(args = None):
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
    except IndexError:
        script = sys.stdin
        if script.isatty():
            raise ProcessError("Usage:\n\t$ neopo script <file>\n\t$ <another process> | neopo script")
    except FileNotFoundError:
        raise ProcessError("Could not find script %s!" % name)

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

if __name__ == "__main__":
    try:
        script_command([None, *sys.argv])
    except ProcessError as e:
        print(e)
        exit(1)
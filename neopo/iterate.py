import subprocess

from .common import ProcessError, UserError
from .common import particle_cli, running_on_windows

from .build import compile_command, flash_command, flash_all_command, clean_command, run_command
# from script import script_command

# Available options for iterate
iterable_commands = {
    "compile": compile_command,
    "build": compile_command,
    "flash": flash_command,
    "flash-all": flash_all_command,
    "clean": clean_command,
    "run": run_command,
    # "script": script_command
}

# Iterate through all connected devices and run a command
def iterate_command(args):
    # Find Particle deviceIDs connected via USB
    process = [particle_cli, "serial", "list"]
    particle = subprocess.run(process, stdout=subprocess.PIPE,
                                        shell=running_on_windows, check=True)
    devices = [line.decode("utf-8").split()[-1] for line in particle.stdout.splitlines()[1:]]

    if not devices:
        raise ProcessError("No devices found!")

    # Remove "iterate" from process
    del args[1]

    try:
        if not args[1] in iterable_commands.keys():
            raise UserError("Invalid command!")
    except IndexError as e:
        raise UserError("You must supply a command to iterate with!") from e

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

import os
import sys
import subprocess

from .build import add_build_tools
from .common import particle_cli, running_on_windows, ProcessError

# Wrapper for [particle]
def particle_command(args):
    # Add build tools to env
    temp_env = os.environ.copy()
    add_build_tools(temp_env)

    process = [particle_cli, *args[2:]]

    try:
        returncode = subprocess.run(process, env=temp_env, shell=running_on_windows, check=True).returncode
    # Return cleanly if ^C was pressed
    except KeyboardInterrupt:
        return
    if returncode:
        raise ProcessError("Particle CLI exited with code %s" % returncode)

if __name__ == "__main__":
    particle_args = sys.argv[1:]
    particle_command([None, None, *particle_args])

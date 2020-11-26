import os
import sys
import subprocess

from .build import addBuildtools
from .common import particle_cli, running_on_windows, ProcessError

# Wrapper for [particle]
def particle_command(args):
    # Add build tools to env
    tempEnv = os.environ.copy()
    addBuildtools(tempEnv)

    process = [particle_cli, *args[2:]]

    try:
        returncode = subprocess.run(process, env=tempEnv, shell=running_on_windows).returncode
    # Return cleanly if ^C was pressed
    except KeyboardInterrupt:
        return
    if returncode:
        raise ProcessError("Particle CLI exited with code %s" % returncode)

if __name__ == "__main__":
    args = sys.argv[1:]
    particle_command([None, None, *args])
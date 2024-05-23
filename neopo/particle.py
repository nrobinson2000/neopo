import subprocess
import sys

# Local imports
from .build import add_build_tools
from .common import min_particle_env, particle_cli, running_on_windows


# Create particle-cli temp_env
def particle_env():
    temp_env = min_particle_env()
    # Add build tools to env
    add_build_tools(temp_env)
    return temp_env


# Wrapper for [particle]
def particle_command(args):
    process = [particle_cli, *args[2:]]

    try:
        subprocess.run(
            process, env=particle_env(), shell=running_on_windows, check=True
        )
    # Return cleanly if ^C was pressed
    except KeyboardInterrupt:
        return
    except subprocess.CalledProcessError:
        return


if __name__ == "__main__":
    particle_args = sys.argv[1:]
    particle_command([None, None, *particle_args])

# Frontend for neopo scripting interface

import sys

# Local imports
from .common import ProcessError
from .command import script_command

if __name__ == "__main__":
    try:
        script_command([None, *sys.argv])
    except ProcessError as error:
        print(error)
        sys.exit(1)

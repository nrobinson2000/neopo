# Frontend for neopo iteration interface

import sys

# Local imports
from .command import iterate_command
from .common import ProcessError


def main():
    try:
        iterate_command([None, *sys.argv])
    except ProcessError as error:
        print(error)


if __name__ == "__main__":
    main()

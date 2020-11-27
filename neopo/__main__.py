# neopo: A lightweight solution for local Particle development.
# Copyright (c) 2020 Nathan Robinson.
# https://neopo.xyz


# Provides access to using neopo with:
# python -m neopo

import sys
from .command import main

if __name__ == "__main__":
    main(sys.argv)

# neopo: A lightweight solution for local Particle development.
# Copyright (c) 2020 Nathan Robinson.
# https://neopo.xyz

import os

# Disable RuntimeWarning for neopo.particle and neopo.script
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

# Import module api
from .cli import main, particle

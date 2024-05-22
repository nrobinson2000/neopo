# neopo: A lightweight solution for local Particle development.
# Copyright (c) 2021 Nathan Robinson.
# https://neopo.xyz

import os

# Disable RuntimeWarning for neopo.particle and neopo.script
import warnings

warnings.filterwarnings("ignore", category=RuntimeWarning)

# Import module api
from .cli import (
    build,
    clean,
    configure,
    create,
    flags,
    flash,
    flash_all,
    get,
    install,
    iterate,
    legacy,
    libs,
    main,
    particle,
    run,
    script,
    settings,
    uninstall,
    update,
    upgrade,
    versions,
)
from .command import script_wait

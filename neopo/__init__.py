# Provides access to using neopo as a module:
# import neopo

# General options
from .neopo import help, install, upgrade, uninstall, versions, create, particle

# Build options
from .neopo import build, flash, flash_all, clean

# Special options
from .neopo import run, configure, flags, settings, libs, iterate

# Script options
from .neopo import script, script_print, script_wait

# Dependency options
from .neopo import update, get

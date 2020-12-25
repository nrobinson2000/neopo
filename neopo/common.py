# Paths, dictionaries, and errors used by other modules
import os
import platform

# Home directory of user running neopo
HOME_DIR = os.path.expanduser("~")

# Specify custom path. Example:
# NEOPO_PATH=$PWD/temp neopo particle
NEOPO_PATH = "NEOPO_PATH" in os.environ

# OPT-IN to use ~/.local/share/neopo by exporting NEOPO_LOCAL. Example:
# NEOPO_LOCAL=1 neopo particle
BASE_DIR = os.path.join(HOME_DIR, ".local", "share", "neopo")
NEOPO_LOCAL = "NEOPO_LOCAL" in os.environ

# Set custom path if specified
if NEOPO_PATH:
    BASE_DIR = os.environ["NEOPO_PATH"]

# Use ~/.local/share/neopo or custom path
if NEOPO_LOCAL or NEOPO_PATH:
    PARTICLE_DEPS = os.path.join(BASE_DIR, "toolchains")
    NEOPO_DEPS = os.path.join(BASE_DIR, "resources")
    CACHE_DIR = os.path.join(NEOPO_DEPS, "cache")
else:
    # Fallback: ~/.neopo and ~/.particle
    # Primary directories: dependencies, caches, scripts
    BASE_DIR = HOME_DIR
    PARTICLE_DEPS = os.path.join(HOME_DIR, ".particle", "toolchains")
    NEOPO_DEPS = os.path.join(HOME_DIR, ".neopo")
    CACHE_DIR = os.path.join(NEOPO_DEPS, "cache")

# DEBUG
# print(BASE_DIR, PARTICLE_DEPS, NEOPO_DEPS, CACHE_DIR, sep="\n")

# Create a copy of the env with XDG_DATA_HOME set if necessary
def min_particle_env():
    temp_env = os.environ.copy()
    if NEOPO_LOCAL or NEOPO_PATH:
        temp_env["XDG_DATA_HOME"] = BASE_DIR
    return temp_env

# Precompiled gcc-arm for ARM platforms
ARM_GCC_ARM = {
    "aarch64": {
        "5.3.1": {
            "url": "https://github.com/nrobinson2000/neopo/releases/download/0.0.3/gcc-arm-v5.3.1-aarch64.tar.gz",
            "sha256": "06a392fb34103b0202cee65a7cae0e1a02b3e6e775c3d0d4b2111c631efbc303"
        },
        "9.2.1": {
            "url": "https://github.com/nrobinson2000/neopo/releases/download/0.0.3/gcc-arm-v9.2.1-aarch64.tar.gz",
            "sha256": "1530a1ebc43118cb81650af8621f6529df20b300e6c9d5e38aeb1ccc717c6a9e"
        }
    },
    "armv7l": {
        "5.3.1": {
            "url": "https://github.com/nrobinson2000/neopo/releases/download/0.0.1/gcc-arm-v5.3.1-raspberry-pi.tar.gz",
            "sha256": "dc5570abe2b4742a70dba06f59bf18bd1354107a879ce68029da29539113e3b0"
        },
        "9.2.1": {
            "url": "https://github.com/nrobinson2000/neopo/releases/download/0.0.2/gcc-arm-v9.2.1-raspberry-pi.tar.gz",
            "sha256": "d963b551122d57057aaacc82e61ca6a05a524df14bb9fe28ca55b67494639fce"
        }
    }
}

# Windows tricks
running_on_windows = platform.system() == "Windows"
particle_cli = os.path.join(
    NEOPO_DEPS, "particle.exe") if running_on_windows else os.path.join(NEOPO_DEPS, "particle")

# JSON cache files
jsonFiles = {
    "firmware": os.path.join(CACHE_DIR, "firmware.json"),
    "toolchains": os.path.join(CACHE_DIR, "toolchains.json"),
    "platforms": os.path.join(CACHE_DIR, "platforms.json"),
    "compilers": os.path.join(CACHE_DIR, "compilers.json"),
    "manifest": os.path.join(CACHE_DIR, "manifest.json")
}

# Workbench template files
vscodeFiles = {
    "dir": os.path.join(NEOPO_DEPS, "vscode"),
    "launch": os.path.join(NEOPO_DEPS, "vscode", "launch.json"),
    "settings": os.path.join(NEOPO_DEPS, "vscode", "settings.json")
}

# Files inside VSIX
extensionFiles = {
    "bin": "extension/src/cli/bin",
    "manifest": "extension/src/compiler/manifest.json",
    "launch": "extension/src/cli/vscode/launch.json",
    "settings": "extension/src/cli/vscode/settings.json"
}

# Files inside project
projectFiles = {
    "launch": os.path.join(".vscode", "launch.json"),
    "settings": os.path.join(".vscode", "settings.json"),
    "properties": "project.properties"
}

# Use this as .travis.yml when creating project repos
TRAVIS_YML = """# Build a neopo project with Travis CI
os: linux
language: shell
install:
  - bash <(curl -sL https://raw.githubusercontent.com/nrobinson2000/neopo/master/install.sh)
script:
  - neopo libs
  - neopo build
cache:
  directories:
    - $HOME/.particle
    - $HOME/.neopo
"""

# Custom errors
class UserError(RuntimeError):
    pass

class DependencyError(RuntimeError):
    pass

class ProcessError(RuntimeError):
    pass

class ProjectError(RuntimeError):
    pass

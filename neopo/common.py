# Paths, dictionaries, and errors used by other modules
import os
import platform

# Primary directories: dependencies, caches, scripts
HOME_DIR = os.path.expanduser("~")
BASE_DIR = HOME_DIR
PARTICLE_DEPS = os.path.join(HOME_DIR, ".particle", "toolchains")
NEOPO_DEPS = os.path.join(HOME_DIR, ".neopo")
CACHE_DIR = os.path.join(NEOPO_DEPS, "cache")

# EXPERIMENTAL:
# On Linux use /opt/neopo as the root of the package by setting NEOPO_GLOBAL
# TODO: Make use of this in the PKGBUILD.
# TODO: User will need ownership of /opt/neopo

# /opt/neopo
# ├── particle/
# │   ├── autoupdate
# │   ├── error.log
# │   ├── node_modules/
# │   │   └── particle-cli/
# │   ├── node-v12.16.1-linux-x64/
# │   │   ├── bin/
# │   │   ├── CHANGELOG.md
# │   │   ├── include/
# │   │   ├── lib/
# │   │   ├── LICENSE
# │   │   ├── README.md
# │   │   └── share/
# │   ├── package-lock.json
# │   ├── plugin-cache.json
# │   └── tmp/
# ├── resources/
# │   ├── cache/
# │   │   ├── compilers.json
# │   │   ├── firmware.json
# │   │   ├── manifest.json
# │   │   ├── platforms.json
# │   │   └── toolchains.json
# │   ├── particle*
# │   └── vscode/
# │       ├── launch.json
# │       └── settings.json
# └── toolchains/
#     ├── buildscripts/
#     │   └── 1.9.2/
#     ├── buildtools/
#     │   └── 1.1.1/
#     ├── deviceOS/
#     │   └── 2.0.1/
#     ├── gcc-arm/
#     │   └── 9.2.1/
#     └── openocd/
#         └── 0.11.2-adhoc6ea4372.0/

# OPT-IN to use /opt/neopo by exporting NEOPO_GLOBAL
NEOPO_GLOBAL = "NEOPO_GLOBAL" in os.environ

# Use /opt/neopo to store all neopo files
if NEOPO_GLOBAL:
    BASE_DIR = "/opt/neopo"
    PARTICLE_DEPS = os.path.join(BASE_DIR, "toolchains")
    NEOPO_DEPS = os.path.join(BASE_DIR, "resources")
    CACHE_DIR = os.path.join(NEOPO_DEPS, "cache")

# Create a copy of the env with XDG_DATA_HOME set if necessary
def min_particle_env():
    temp_env = os.environ.copy()
    if NEOPO_GLOBAL:
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

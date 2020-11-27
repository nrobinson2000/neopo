import os
import json

from .common import jsonFiles, projectFiles, PARTICLE_DEPS

# Print available versions compressed (for completion)
def versions_compressed(args):
    with open(jsonFiles["firmware"], "r") as firmwareFile:
        print(*[entry["version"] for entry in json.load(firmwareFile)])

# Print available platforms (for completion)
def platforms_command(args):
    with open(jsonFiles["platforms"], "r") as platformFile:
        print(*[entry["name"] for entry in json.load(platformFile)])

# Find all valid projects in PWD (for completion)
def findValidProjects(args):
    (_, dirs, _) = next(os.walk(os.getcwd()))
    print(*[dir for dir in dirs if os.access(os.path.join(dir, projectFiles["properties"]), os.R_OK)])

# Find all makefile targets (for completion)
def getMakefileTargets(args):
    with open(jsonFiles["manifest"], "r") as manifest:
        with open(os.path.join(PARTICLE_DEPS, "buildscripts", json.load(manifest)["buildscripts"], "Makefile")) as makefile:
            sep = ".PHONY: "
            print(*[line.partition(sep)[2].strip("\n") for line in makefile.readlines() if line.startswith(sep)])

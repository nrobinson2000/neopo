import os
import json

# Local imports
from .common import jsonFiles, projectFiles, PARTICLE_DEPS

# Print available versions compressed (for completion)
def versions_compressed(args):
    total_versions = set()
    with open(jsonFiles["firmware"], "r") as firmware_file:
        total_versions.update([entry["version"] for entry in json.load(firmware_file)])
    _, installed_versions, _ = next(os.walk(os.path.join(PARTICLE_DEPS, "deviceOS")))
    total_versions.update(installed_versions)
    print(*sorted(total_versions))

# Print available platforms (for completion)
def platforms_command(args):
    with open(jsonFiles["platforms"], "r") as platform_file:
        print(*[entry["name"] for entry in json.load(platform_file)])

# Find all valid projects in PWD (for completion)
def find_valid_projects(args):
    (_, dirs, _) = next(os.walk(os.getcwd()))
    print(*[dir for dir in dirs
        if os.access(os.path.join(dir, projectFiles["properties"]), os.R_OK)])

# Find all makefile targets (for completion)
def get_makefile_targets(args):
    with open(jsonFiles["manifest"], "r") as manifest:
        with open(os.path.join(PARTICLE_DEPS, "buildscripts", json.load(manifest)["buildscripts"], "Makefile")) as makefile:
            sep = ".PHONY: "
            print(*[line.partition(sep)[2].strip("\n")
                    for line in makefile.readlines() if line.startswith(sep)])

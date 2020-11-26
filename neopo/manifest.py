import os
import json

# Local imports
from .common import jsonFiles

# Update the manifest JSON file
def writeManifest(dep):
    with open(jsonFiles["manifest"], "r+") as file:
        try:
            manifest = json.load(file)
        except json.decoder.JSONDecodeError:
            manifest = {}

        manifest[dep["name"]] = dep["version"]
        file.seek(0)
        json.dump(manifest, file, indent=4)
        file.truncate()

# Create the manifest file
def createManifest():
    if not os.path.isfile(jsonFiles["manifest"]):
        open(jsonFiles["manifest"], "w")

# Load settings from the dependency mainfest JSON file
def loadManifest(tupleOrDict):
    with open(jsonFiles["manifest"], "r") as file:
        try:
            data = json.load(file)
        except json.decoder.JSONDecodeError:
            return None
        if tupleOrDict:
            return (
                data["gcc-arm"],
                data["buildscripts"],
                data["buildtools"],
                data["deviceOS"]
            )
        else:
            return {
                "gcc-arm": data["gcc-arm"],
                "buildscripts": data["buildscripts"],
                "buildtools": data["buildtools"],
                "deviceOS": data["deviceOS"],
                "openocd": data["openocd"]
            }
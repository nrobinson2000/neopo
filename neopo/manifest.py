import json
import os

# Local imports
from .common import jsonFiles
from .utility import handle_missing_file


# Update the manifest JSON file
def write_manifest(dep):
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
def create_manifest():
    if not os.path.isfile(jsonFiles["manifest"]):
        open(jsonFiles["manifest"], "w")


def get_manifest_value(key):
    try:
        with open(jsonFiles["manifest"], "r") as file:
            try:
                data = json.load(file)
            except json.decoder.JSONDecodeError:
                return None
            return data[key]
    except FileNotFoundError as error:
        handle_missing_file(error.filename)


def get_cached_json(key):
    try:
        with open(jsonFiles[key]) as file:
            try:
                data = json.load(file)
                return data
            except json.decoder.JSONDecodeError:
                return None
            except KeyError:
                return None
    except FileNotFoundError as error:
        handle_missing_file(error.filename)


# Load settings from the dependency mainfest JSON file
def load_manifest():
    with open(jsonFiles["manifest"], "r") as file:
        try:
            data = json.load(file)
        except json.decoder.JSONDecodeError:
            return None
        return (
            data["gcc-arm"],
            data["buildscripts"],
            data["buildtools"],
            data["deviceOS"],
        )

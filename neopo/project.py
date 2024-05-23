import json
import os
import pathlib
import shutil
import subprocess

# Local imports
from .common import (
    ProcessError,
    ProjectError,
    UserError,
    min_particle_env,
    particle_cli,
    projectFiles,
    running_on_windows,
    vscodeFiles,
)
from .manifest import get_manifest_value
from .toolchain import check_firmware_version
from .utility import check_login, download_library, write_file


# Create a Particle project and copy in Workbench settings
def create_project(path, name, config_device=None, config_version=None):
    # Default settings
    if not config_version:
        config_version = get_manifest_value("deviceOS")
    if not config_device:
        config_device = "argon"

    # Check supplied settings before creating project
    if config_device and config_version:
        if not check_firmware_version(config_device, config_version):
            raise ProjectError("Failed to create project %s!" % name)

    project_path = os.path.join(path, name)
    # Use particle-cli to create the project
    try:
        subprocess.run(
            [particle_cli, "project", "create", path, "--name", name],
            env=min_particle_env(),
            shell=running_on_windows,
            check=True,
        )
    except subprocess.CalledProcessError as error:
        raise ProcessError("Failed to create project %s!" % name) from error

    # If git is installed, initialize project as git repo
    if shutil.which("git"):
        subprocess.run(["git", "init", project_path], check=True)

        # Add .gitignore to project
        write_file("target", os.path.join(project_path, ".gitignore"), "w")

    # Add buttons to README.md
    neopo_button = "[![](https://img.shields.io/badge/built_with-neopo-informational)](https://neopo.xyz)"
    readme_path = os.path.join(project_path, "README.md")

    with open(readme_path, "r") as file:
        readme = file.readlines()
        readme.insert(0, "\n")
        readme.insert(0, neopo_button + "\n")
    with open(readme_path, "w") as file:
        file.writelines(readme)

    # Configure project with default or specified settings
    configure_project(project_path, config_device, config_version)


# Modify Workbench settings in a project (platform, firmwareVersion)
def configure_project(project_path, platform, firmware_version):
    # Ensure that firware is compatible with platform
    # Download requested version if required
    if not check_firmware_version(platform, firmware_version):
        raise ProjectError("Firmware related error!")

    # Ensure that a valid project was selected
    if not os.path.isfile(os.path.join(project_path, projectFiles["properties"])):
        raise ProjectError("%s is not a Particle project!" % project_path)

    # Upgrade a CLI project to Workbench format if required
    if not os.path.isfile(os.path.join(project_path, projectFiles["settings"])):
        pathlib.Path(os.path.join(project_path, ".vscode")).mkdir(
            parents=True, exist_ok=True
        )
        shutil.copyfile(
            vscodeFiles["launch"], os.path.join(project_path, projectFiles["launch"])
        )
        shutil.copyfile(
            vscodeFiles["settings"],
            os.path.join(project_path, projectFiles["settings"]),
        )

    # Apply configuration to project
    write_settings(project_path, platform, firmware_version)
    print(
        "Configured project %s: (%s, %s)" % (project_path, platform, firmware_version)
    )


# Read settings.json in a project
def open_settings(project_path):
    with open(os.path.join(project_path, projectFiles["settings"]), "r") as settings:
        try:
            return json.loads(settings.read())
        except json.decoder.JSONDecodeError as error:
            raise ProjectError(
                "Failed to load settings from %s\nPlease ensure that it contains valid JSON syntax."
                % projectFiles["settings"]
            ) from error


# Load Workbench settings from a project
def get_settings(project_path):
    data = open_settings(project_path)
    return (data["particle.targetPlatform"], data["particle.firmwareVersion"])


# Update Workbench settings in a project
def write_settings(project_path, platform, version):
    data = open_settings(project_path)
    with open(os.path.join(project_path, projectFiles["settings"]), "w") as settings:
        data["particle.targetPlatform"] = platform
        data["particle.firmwareVersion"] = version
        json.dump(data, settings, indent=4)


# Create a dictionary from a .properties file
def load_properties(properties_path):
    properties = {}
    with open(properties_path, "r") as file:
        for line in file.readlines():
            tokens = line.split("=", 1)
            if len(tokens) != 2:
                continue
            key = tokens[0]
            value = tokens[1].strip()
            properties[key] = value
    return properties


# Extract dependencies from .properties
def get_library_deps(properties):
    return [
        (key.split(".")[1], properties[key])
        for key in properties.keys()
        if key.startswith("dependencies")
    ]


# Discover dependencies of locally installed libraries
def find_sub_libraries(libraries, project_path):
    found_libraries = []
    for library in libraries:
        properties_file = os.path.join(
            project_path, "lib", library[0], "library.properties"
        )
        try:
            properties = load_properties(properties_file)
            found_libraries.extend(get_library_deps(properties))
        except FileNotFoundError:
            print("Failed to find: %s" % os.path.join(library[0], "library.properties"))
    return found_libraries


# Ensure that specified libraries are downloaded, otherwise install them
def check_libraries(project_path, active):
    try:
        properties = load_properties(
            os.path.join(project_path, projectFiles["properties"])
        )
        libraries = get_library_deps(properties)

    except FileNotFoundError as error:
        raise ProjectError("%s is not a Particle Project!" % project_path) from error

    libraries_intact = install_libraries(libraries, project_path, active)
    if libraries_intact:
        sub_libraries = find_sub_libraries(libraries, project_path)
        libraries_intact = install_libraries(sub_libraries, project_path, active)
    return libraries_intact


# Install a list of libraries
def install_libraries(libraries, project_path, active):
    libraries_intact = True
    for library in libraries:
        requested_version = library[1]
        try:
            lib_properties = load_properties(
                os.path.join(project_path, "lib", library[0], "library.properties")
            )
            actual_version = lib_properties["version"]
        except FileNotFoundError:
            actual_version = None

        if requested_version != actual_version:
            if active:
                download_library(library, project_path)
            else:
                print("WARNING: Library %s@%s not found locally." % library)
                libraries_intact = False
        else:
            if active:
                print("Library %s@%s is already installed." % library)
    return libraries_intact


# Get EXTRA_CFLAGS for a project or return empty string
def get_flags(project_path):
    try:
        settings_path = os.path.join(project_path, projectFiles["settings"])
        with open(settings_path, "r") as file:
            settings = json.load(file)
        return settings["EXTRA_CFLAGS"]
    except (FileNotFoundError, KeyError):
        return ""


# Set EXTRA_CFLAGS for a project
def set_flags(project_path, make_flags):
    settings_path = os.path.join(project_path, projectFiles["settings"])
    with open(settings_path, "r") as file:
        settings = json.load(file)
    settings["EXTRA_CFLAGS"] = make_flags
    with open(settings_path, "w") as file:
        json.dump(settings, file, indent=4)


# Wrapper for [create]
def create_command(args):
    try:
        project_path = os.path.abspath(args[2])
        platform = args[3] if len(args) >= 4 else None
        version = args[4] if len(args) >= 5 else None
        create_project(
            os.path.dirname(project_path),
            os.path.basename(project_path),
            platform,
            version,
        )
    except IndexError as error:
        raise UserError("You must supply a path for the project!") from error


# Wrapper for [config/configure]
def configure_command(args):
    try:
        project_path = args[4] if len(args) >= 5 else os.getcwd()
        configure_project(project_path, args[2], args[3])
    except IndexError as error:
        raise UserError("You must supply platform and deviceOS version!") from error


# Wrapper for [flags]
def flags_command(args):
    try:
        make_flags = args[2]
    except IndexError as error:
        raise UserError("You must provide the flags as one (quoted) string!") from error
    try:
        project = os.path.abspath(args[3])
    except IndexError:
        project = os.getcwd()

    set_flags(project, make_flags)


# Wrapper for [settings]
def settings_command(args):
    try:
        project_path = args[2] if len(args) >= 3 else os.getcwd()
        settings = get_settings(project_path)
        flags = get_flags(project_path)
        print("project: %s" % os.path.abspath(project_path))
        print("platform: %s" % settings[0])
        print("version: %s" % settings[1])
        print("EXTRA_CFLAGS: %s" % (flags if flags else "<not set>"))
    except FileNotFoundError as error:
        raise UserError("%s is not a Particle project!" % project_path) from error


# Wrapper for [libs]
def libraries_command(args):
    project_path = args[2] if len(args) >= 3 else os.getcwd()
    check_libraries(project_path, True)

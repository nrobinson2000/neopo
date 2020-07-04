# Neopo Complete Reference

## General Options

### help

When neopo is run with no arguments, or with `help`, brief documentation for all user-accessible commands is displayed.

Examples:

```bash
neopo

neopo help
```

### install

Install Particle dependencies and setup the neopo environment. It takes an optional parameter of `-f`, which is used to force dependencies to be reinstalled, rather than skipped if already installed.

Examples:

```bash
neopo install

neopo install -f
```

### upgrade

Upgrade the neopo utility to the latest version available on GitHub. *To update dependencies use [`update`](#update).*

Examples:

```bash
neopo upgrade
```

### uninstall

Remove the neopo utility from the system. *The `~/.particle` and `~/.neopo` directories are left untouched.*

Examples:

```bash
neopo uninstall
```

### versions

List all of the known versions and platforms available to neopo. *To select a platform and deviceOS version for a project, use [`configure`](#configure).*

Examples:

```bash
neopo versions
```

### create

Create a new Particle project at the specified project path. The created project is compatible with neopo, Particle Workbench, and Particle CLI. If `git` is installed on your system, the project is additionally initialized as a repository and support for [TravisCI](https://travis-ci.org/) is added.

Examples:

```bash
neopo create myProject

neopo create ~/Documents/myProject
```

### particle

Access the Particle CLI executable used internally by neopo. By simply prefixing any Particle CLI command with `neopo particle`, the powerful features of Particle CLI can be accessed easily. *The documentation for Particle CLI can be found here: <https://docs.particle.io/reference/developer-tools/cli/>*

Examples:

```
neopo run compile-all myProject

neopo particle login

neopo particle list
```

## Build Options

### compile

Compile the application firmware of a given Particle project, or the current directory if it's a project. Settings applied using [`configure`](#configure) will be passed to the compiler. The verbosity of the output can be increased with the `-v` flag, or the output can be quieted with the `-q` flag.

Examples:

```bash
neopo compile myProject

neopo compile myProject -v

neopo compile myProject -q

neopo compile

neopo compile -v

neopo compile -q
```

### build

Same as [`compile`](#compile). Added for convenience.

### flash

Compile application firmware and then flash the firmware to a connected device using DFU. Structure identical to [`compile`](#compile).

### flash-all

Compile application and system firmware and then flash all parts to a connected device using DFU. Structure identical to [`compile`](#compile).

### clean

Clean application firmware. Usually unnecessary but can eliminate some build errors. Structure identical to [`compile`](#compile).

## Special Options

### run

Run a specified makefile target for a project. Includes common targets used by [`Build Options`](#Build-Options), and other targets. The `-v` and `-q` flags are supported.

Examples:

```bash
neopo run

neopo run help myProject

neopo run compile-all myProject

neopo run compile-all myProject -v

neopo run clean-debug -q
```

### configure

Configure the device platform and deviceOS version a project should use. The platform and version are checked for compatibility and the specified version of deviceOS will be downloaded if it's not already installed. *To find deviceOS versions and their supported platforms use [`versions`](#versions). The tab completion function is especially handy here since it can fill in platforms and versions.*

Examples:

```bash
neopo configure argon 1.5.2

neopo configure electron 1.5.4-rc.1 myProject
```

### flags

Set the `EXTRA_CFLAGS` variable for a project to be used during compilation.

Examples:

```bash
neopo flags "-D FLAG_ONE=abc -D FLAG_TWO=123"
neopo flags "-D DEBUG_ENABLED" myProject
```

### iterate

An advanced command used to run a supported command iteratively for all connected devices. For each connected device, the deviceID is printed, the device is put into DFU mode, and the specified iteration command executed. This command was designed for quickly flashing to multiple connected devices, but there are many other ways this command can be used.

The following commands are supported: [`compile`](#compile), [`build`](#build), [`flash`](#flash-all), [`flash-all`](#flash-all), [`clean`](#clean), [`run`](#run), [`script`](#script).

The `-v` and `-q` flags can be passed if the iterated command supports them.

Examples:

```bash
neopo iterate flash

neopo iterate flash-all myProject -q

neopo iterate run compile-user myProject -v

neopo iterate run script myScript
```

## Script Options

One of the most powerful features of neopo is the scripting interface. Neopo scripts are a list of commands to run sequentially. Each command should be placed on its own line. Empty lines and lines starting `#` are skipped. Any neopo command can be used in a neopo script, **even Particle commands.**

Neopo scripts are plain-text and do not require an extension.

Here is an example script:

```py
# Configure the current project
configure argon 1.5.2

# Prompt the user to plug in a device
print "Please plug in your device."
wait

# Flash firmware to the device
flash

# Prompt the user to wait for the device to connect
print "Please wait for your device to connect to the cloud."
wait

# Subscribe to incoming messages
particle subscribe
```

### load

If this script was named `testDevice` and in the current directory, to run it you would first need to copy it into the central neopo scripts directory with:

```bash
neopo load testDevice
```

### script

Next, to run the `testDevice` script you would use the following:

```bash
neopo script testDevice
```

There are nearly infinite scripts that can be made, and I highly recommend using the scripting interface to automate numerous Particle development tasks.

## Dependency Options

### update

Redownload the Workbench manifest and download Particle dependencies if there are newer versions available.

Examples:

```bash
neopo update
```

### get

Download a specified deviceOS version for later use. Handy for situations when you need to download firmware in advance.

Examples:

```bash
neopo get 0.7.0

neopo get 1.5.2
```

## Tab Completion

When using neopo in bash and similar shells, tab completion is supported through the tab completion function.

While typing most neopo commands and arguments you can press the tab key to get suggestions and fill in arguments, making development very convenient.

When installing neopo on Linux the tab completion function is installed automatically. On other operating systems the user must download and source the script manually.

If you have a `~/.bashrc` file already, setting up tab completion is simple.

```bash
mkdir -p ~/.completion
curl -sLo ~/.completion/neopo https://git.io/JJkF5
echo 'source $HOME/.completion/neopo' >> ~/.bashrc
```
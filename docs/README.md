[![Build Status](https://travis-ci.org/nrobinson2000/neopo.svg?branch=master)](https://travis-ci.org/nrobinson2000/neopo)
[![Particle Community](https://img.shields.io/badge/particle-community-informational)](https://community.particle.io/t/neopo-a-lightweight-solution-for-local-particle-development/56378?u=nrobinson2000)

![Neopo Screenshot](neopo-carbon.png)

## Features

- Builds Particle projects locally without any overhead.
- Compatible with Particle Workbench and Particle CLI.
- Installs and manages necessary Particle dependencies.
- Built with Python using only the standard library.
- Supports Linux, macOS, Windows, and Raspberry Pi.
- Supports tab completion to assist development.

## Installation

The easiest way to install neopo is to open a Terminal and run:

```bash
$ bash <( curl -sL https://git.io/JfwhJ )
```

Alternatively, you can clone this repository, add the directory to your `PATH`, and run the install command:

```bash
$ git clone https://github.com/nrobinson2000/neopo
$ export PATH="$PATH:$PWD/neopo"
$ neopo install
```

On Windows the installation process is more involved but not very difficult: [Windows Installation](windows.md)

## Examples

### Creating a project

```bash
$ neopo create myProject
```

### Configuring a project

```bash
$ neopo configure argon 1.5.2 myProject
```

### Building a project

```bash
$ neopo build myProject
```

### Flashing a project

```bash
$ neopo flash myProject
```

### Running a specific Makefile target

```bash
$ neopo run clean-debug myProject
```

### Uninstalling

```bash
$ neopo uninstall
```

**Note: Specifying the project directory is optional if your current working directory is a Particle project. Tab completion can also find valid projects in the current working directory.**

**For example:**

```bash
$ cd myProject

$ neopo build

$ neopo flash
```
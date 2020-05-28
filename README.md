[![Build Status](https://travis-ci.org/nrobinson2000/neopo.svg?branch=master)](https://travis-ci.org/nrobinson2000/neopo)

# neopo
## A lightweight solution for local Particle development.

![Neopo Screenshot](docs/neopo.png)

## Features

- Builds Particle projects offline.
- Supports Linux and macOS.
- Compatible with Particle Workbench and Particle CLI.
- Downloads necessary Particle dependencies.
- One small and fast Python executable.
- Tab completion support.
- Much cleaner code than previous `po` projects.

## Installation

The easiest way to install neopo is to open a Terminal and run:

```bash
$ bash <( curl -sL https://git.io/JfwhJ )
```

Neopo will be installed to `~/.local/bin/neopo` (Linux) or `/usr/local/bin/neopo` (macOS).

Alternatively, you can clone this repository and add the directory to your `PATH`:

```bash
$ git clone https://github.com/nrobinson2000/neopo
$ export PATH="$PATH:$PWD/neopo"
$ neopo install
```

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

## Uninstalling

```bash
$ neopo uninstall
```

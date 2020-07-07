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

Universal Installer (Linux/macOS):

```bash
$ bash <( curl -sL https://git.io/JfwhJ )
```

Running from source:

```bash
$ git clone https://github.com/nrobinson2000/neopo
$ export PATH="$PATH:$PWD/neopo"
$ neopo install
```

For more installation information, please refer to the [Installation tutorial.](tutorials/install.md)

## Usage

To get started with neopo, please refer to the [Quick Reference.](quick-docs.md)

For descriptions of all available commands, please refer to the [Complete Reference.](full-docs.md)
[![GitHub Actions Status](https://github.com/nrobinson2000/neopo/workflows/python-pip/badge.svg)](https://github.com/nrobinson2000/neopo/actions)
[![Build Status](https://travis-ci.org/nrobinson2000/neopo.svg?branch=master)](https://travis-ci.org/nrobinson2000/neopo)
[![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/nrobinson2000/neopo)](https://hub.docker.com/r/nrobinson2000/neopo)
[![AUR package](https://repology.org/badge/version-for-repo/aur/neopo.svg)](https://aur.archlinux.org/packages/neopo-git/)
[![Particle Community](https://img.shields.io/badge/particle-community-informational)](https://community.particle.io/t/neopo-a-lightweight-solution-for-local-particle-development/56378?u=nrobinson2000)

# neopo
## A lightweight solution for local Particle development.

![Neopo Screenshot](https://d33wubrfki0l68.cloudfront.net/d9a010fe28827ee5728e18eaea93a00ee7631208/1833f/assets/images/neopo-carbon.png)

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
$ bash <(curl -sL neopo.xyz/install)
```

Install from [AUR](https://aur.archlinux.org/packages/neopo-git/):

```bash
$ yay -S neopo-git
$ neopo install
```

Install from source (pip):

```bash
$ git clone https://github.com/nrobinson2000/neopo
$ cd neopo
$ sudo python3 -m pip install .
$ neopo install
```

Docker container:

```bash
$ docker pull nrobinson2000/neopo
$ docker run -it nrobinson2000/neopo
```

For more installation information, please refer to the [Installation tutorial.](https://neopo.xyz/tutorials/install)

## Usage

To get started with neopo, please refer to the [Quick Reference.](https://neopo.xyz/docs/quick-docs)

For descriptions of all available commands, please refer to the [Complete Reference.](https://neopo.xyz/docs/full-docs)
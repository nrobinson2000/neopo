[![Build Status](https://travis-ci.org/nrobinson2000/neopo.svg?branch=master)](https://travis-ci.org/nrobinson2000/neopo)

# neopo: A replacement for po-util

## A lightweight solution for local Particle development built with Python

![Neopo screenshot](docs/neopo-screenshot.png)


## Installation

The easiest way to install neopo is by entering this into a terminal:

```bash
$ curl -sL https://git.io/JfwhJ | bash
```

Alternatively, you can clone this repository and add the directory to your PATH:

```bash
$ git clone https://github.com/nrobinson2000/neopo
$ export PATH="$PATH:$PWD/neopo"
$ neopo install
```

## Examples

**Creating a particle-cli and Workbench compatible project:**

```bash
$ neopo create myProject
```

**Configuring a project:**

```bash
$ neopo configure argon 1.5.2 myProject
```

**Building a project:**

```bash
$ neopo build myProject
```

**Flashing a project:**

```bash
$ neopo flash myProject
```

**Running a specific Makefile target:**

```bash
$ neopo run clean-debug myProject
```
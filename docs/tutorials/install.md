# Installing neopo

Neopo installs quickly giving you a local Particle development environment fast.

## Universal installer

```bash
$ bash <( curl -sL https://git.io/JfwhJ )
```

## Linux

On most Linux distributions the universal installer will correctly install the necessary dependencies with your package manager and install neopo and its dependencies.

## Mac

On macOS, the universal installer will work, but unlike on Linux, the tab completion script will not be automatically installed. [To install tab completion manually, follow these steps.](../full-docs#tab-completion)

## Windows

On Windows, the universal installer will not work, but neopo can be installed manually using Cygwin. [Please follow the steps here.](../windows.md)

## Running from source

```bash
$ git clone https://github.com/nrobinson2000/neopo
$ cd neopo
$ bin/neopo install
```

## Uninstalling

Uninstalling neopo takes two steps. First, you must delete the neopo script installed on your system. You can do this with:

```bash
$ neopo uninstall
```

Next, you must delete the `~/.neopo` directory which is used for neopo settings, caches, and scripts.

```bash
$ rm -rf ~/.neopo
```

Optionally, you can also delete `~/.particle`, but this directory is required for Particle Workbench and Particle CLI to function.

```bash
$ rm -rf ~/.particle
```
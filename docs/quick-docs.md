
# Neopo Quick Reference

*The [Complete Reference](full-docs.md) goes into much more detail.*

## Creating a project

```bash
$ neopo create myProject
```

## Configuring a project

```bash
$ neopo configure argon 1.5.2 myProject
```

## Building a project

```bash
$ neopo build myProject
```

## Flashing a project

```bash
$ neopo flash myProject
```

## Running a specific Makefile target

```bash
$ neopo run clean-debug myProject
```

## Uninstalling

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
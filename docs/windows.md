# Installing neopo on Windows

***For this tutorial basic knowledge of Vim is assumed. You can also use your preferred editor instead.***

## Step 1: Install Windows Dependencies

Download and install [Python](https://www.python.org/downloads/windows/), [Cygwin](https://www.cygwin.com/setup-x86_64.exe), and [Git](https://git-scm.com/download/win). When installing Cygwin, please also install Vim.

## Step 2: Download Neopo inside of Cygwin

Clone the neopo repository:

```bash
git clone https://github.com/nrobinson2000/neopo
```

Open `neopo/bin/neopo` with Vim or your preferred editor:

```bash
vim neopo/bin/neopo
```

Change the first line (shebang) to:

```bash
#!/usr/bin/env python
```

Save and close the file.

## Step 3: Create a neopo alias

Open `~/.bashrc` with Vim or your preferred editor:

```bash
vim ~/.bashrc
```

Add the followng line to the bottom of the file:

```
alias neopo='python C:\\cygwin64\\home\\'$USER'\\neopo\\bin\\neopo'
```

Save and close the file.

Reload ~/.bashrc or open a new Cygwin window so that the alias is available:

```bash
source ~/.bashrc
```

## Step 4: Install neopo dependencies

```bash
neopo install
```

## Step 5: Begin using neopo

To get started with neopo, please refer to the [Quick Reference.](quick-docs.md)


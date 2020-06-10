# Using neopo on Windows

***Basic knowledge of Vim is assumed.***

## Install Dependencies

### Python
https://www.python.org/downloads/windows/

### Cygwin and Vim
https://www.cygwin.com/setup-x86_64.exe

### Git
https://git-scm.com/download/win


## Install Neopo inside Cygwin

- Clone the repository:

```bash
cd
git clone https://github.com/nrobinson2000/neopo
```

- Edit the shebang (The first line):

```bash
vim neopo/bin/neopo

#!/usr/bin/env python
```

- Add a neopo alias to end of bashrc:

```bash
vim ~/.bashrc

alias neopo='python C:\\cygwin64\\home\\'$USER'\\neopo\\bin\\neopo'
```

- Reload bashrc:

```bash
source ~/.bashrc
```

- Install neopo dependencies:

```bash
neopo install
```

## Create a project

```bash
neopo create test
```

## Flash a project

```bash
neopo flash test
```



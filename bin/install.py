#!/usr/bin/env python3

# neopo: A lightweight solution for local Particle development.
# Copyright (c) 2020 Nathan Robinson.

import os
import stat
import urllib.request
import sys

try:
    confirm = sys.argv[1] != "-y"
except IndexError:
    confirm = True

chosen = not confirm

url = "https://raw.githubusercontent.com/nrobinson2000/neopo/master/bin/neopo"
binary = "neopo"

install = None
paths = os.environ["PATH"].split(":")
#paths.reverse()

for path in paths:
    if os.access(path, os.W_OK):
        install = os.path.join(path, binary)
        if confirm:
            print("Would you like to install to " + install + "?")
            answer = input("(Y/N): ")
            if answer.lower() == "y":
                chosen = True
                break

if not chosen:
    print("No path was chosen. Exiting...")
    exit(1)

if not install:
    print("No writable paths found!")
    exit(2)

print("Downloading neopo...")

with urllib.request.urlopen(url) as res:
    with open(install, "wb") as file:
        file.write(res.read())
        st = os.stat(install)
        os.chmod(install, st.st_mode | stat.S_IEXEC)

print("Downloaded neopo to: " + install)
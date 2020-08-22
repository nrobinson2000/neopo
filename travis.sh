#!/bin/bash

# neopo: A lightweight solution for local Particle development.
# Copyright (c) 2020 Nathan Robinson.

sudo cp bin/neopo.py /usr/local/bin/neopo

if [ "$(uname)" == 'Linux' ]; then
    sudo apt update
    sudo apt install libarchive-zip-perl libc6-i386
fi

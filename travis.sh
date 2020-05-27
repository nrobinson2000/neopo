#!/bin/bash

# neopo: A lightweight solution for local Particle development.
# Copyright (c) 2020 Nathan Robinson.

export PATH="$PATH:$PWD/bin"

if [ "$(uname)" == 'Linux' ]; then
    sudo apt update
    sudo apt install libarchive-zip-perl libc6-i386
fi

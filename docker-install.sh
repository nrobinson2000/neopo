#!/bin/bash

# neopo: A lightweight solution for local Particle development.
# Copyright (c) 2021 Nathan Robinson.

# Install core dependencies
apt update
apt -y --no-install-recommends install libarchive-zip-perl libc6-i386 python3 vim-tiny 

# Install build dependencies
apt -y --no-install-recommends install git python3-setuptools python3-pip

# Install neopo with pip
git clone https://github.com/nrobinson2000/neopo 2>&1
pushd neopo > /dev/null
python3 -m pip install .
popd > /dev/null

# Clean up
apt -y purge git python3-setuptools python3-pip
apt -y autoremove
apt -y clean
rm -rf /tmp/* /var/tmp/*
rm -rf /var/lib/apt/lists/*
rm -rf neopo

# Post-pull installation steps:
#   neopo install
#   particle --version
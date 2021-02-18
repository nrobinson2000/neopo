#!/bin/bash

# neopo: A lightweight solution for local Particle development.
# Copyright (c) 2021 Nathan Robinson.

# Install dependencies
apt update
apt -y install libarchive-zip-perl libc6-i386 python3 git vim python3-setuptools python3-pip

# Install neopo with pip
git clone https://github.com/nrobinson2000/neopo 2>&1
pushd neopo > /dev/null
python3 -m pip install .
popd > /dev/null

# Run the neopo installer
neopo install

# Run Particle CLI so that it has a chance to pre-download its dependencies
neopo particle 2>&1

#!/bin/bash

# neopo: A lightweight solution for local Particle development.
# Copyright (c) 2021 Nathan Robinson.

# Install dependencies
apt update
apt -y --no-install-recommends install libarchive-zip-perl libc6-i386 python3 vim-tiny \
git python3-setuptools python3-pip # Build only

# Install neopo with pip
python3 -m pip install .

# Preinstall neopo and particle-cli
neopo install -s

# Clean up
rm -rf neopo .git scripts setup.py
apt -y purge git python3-setuptools python3-pip
apt -y autoremove
apt -y clean
rm -rf /tmp/* /var/tmp/*
rm -rf /var/lib/apt/lists/*

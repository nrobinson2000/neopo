#!/bin/bash

# neopo: A lightweight solution for local Particle development.
# Copyright (c) 2021 Nathan Robinson.

# Install dependencies
apt update
apt -y --no-install-recommends install libarchive-zip-perl libc6-i386 python3 vim-tiny \
git python3-wheel python3-setuptools python3-pip curl # Build only

# Download particle completion
curl -sLo ".completions/particle" "https://raw.githubusercontent.com/nrobinson2000/particle-cli-completion/master/particle"

# Install neopo with pip
python3 -m pip install .

# Preinstall neopo and particle
neopo install -s

# Modify dotfiles
cat >> .bashrc << EOF

# neopo settings
source ~/.completions/particle
source ~/.completions/neopo
alias vim='vim.tiny'
alias ls='ls --color=auto'
alias ll='ls -la'
alias la='ls -A'
EOF

# Clean up
rm -rf neopo .git scripts setup.py
apt -y purge git python3-wheel python3-setuptools python3-pip curl
apt -y autoremove
apt -y clean
rm -rf /tmp/* /var/tmp/*
rm -rf /var/lib/apt/lists/*

#!/bin/bash

if [ "$(uname)" == 'Linux' ]; then
    sudo apt update
    sudo apt -y --no-install-recommends install libarchive-zip-perl libc6-i386 python3 vim-tiny \
    git python3-wheel python3-setuptools python3-pip curl # Build only
fi

# Install neopo using pip
python3 -m pip install --upgrade pip
python3 -m pip install .

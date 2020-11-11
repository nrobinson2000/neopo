#!/bin/bash

if [ "$(uname)" == 'Linux' ]; then
    sudo apt update
    sudo apt install libarchive-zip-perl libc6-i386 python3-pip python3-setuptools
fi

# Install neopo using pip
python3 -m pip install --upgrade pip
python3 -m pip install wheel
python3 -m pip install .
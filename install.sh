#!/bin/bash

# neopo: A lightweight solution for local Particle development.
# Copyright (c) 2021 Nathan Robinson.

# Docker/root compatiblity
if [ "$EUID" -ne 0 ]; then
    SUDO="sudo"
    SUDOPY="sudo -H"
fi

# Install additional dependencies for Linux
case "$(uname)" in
Linux)
    echo "Installing Linux dependencies..."
    
    # Ubuntu / Debian / Linux Mint
    if hash apt >/dev/null 2>&1; then
        case "$(uname -m)" in
        x86_64)
            $SUDO dpkg --add-architecture i386
            $SUDO apt update
            $SUDO apt install libarchive-zip-perl libc6-i386 python3 git vim libncurses5:i386 libncurses5 python3-setuptools python3-pip
        ;;
        armv7l)
            $SUDO apt install libarchive-zip-perl libusb-1.0-0-dev dfu-util libudev-dev libisl15 libfl-dev python3 git vim python3-pip python3-setuptools libncurses5
        esac

    # Fedora
    elif hash yum >/dev/null 2>&1; then
        $SUDO yum install glibc.i686 perl-Archive-Zip python3 vim git ncurses-compat-libs python3-pip python3-setuptools ncurses-libs
    
    # Void Linux
    elif hash xbps-install >/dev/null 2>&1; then
        $SUDO xbps-install -S dfu-util python3 git vim perl-Archive-Zip void-repo-multilib bash-completion python3-pip python3-setuptools ncurses-libs
        $SUDO xbps-install -S glibc-32bit ncurses-libs-32bit

    # Manjaro / Arch (x86_64 and aarch64)
    elif hash pacman >/dev/null 2>&1; then
        $SUDO pacman -S --needed yay base-devel
        TEMPDIR="$(mktemp -d)"
        cd "$TEMPDIR"
        yay -G neopo-git
        cd neopo-git
        makepkg -sif
        neopo setup
        exit
    fi
;;

# TODO: Mac dependencies
Darwin) 
    python3 -m pip install --upgrade pip
    python3 -m pip install wheel
;;

# This script does not support Windows
*)
    echo "To install neopo on Windows follow the instructions here:"
    echo "  https://neopo.xyz/tutorials/windows"
    exit 1
esac

# Install neopo as python module (experimental)
TEMPDIR="$(mktemp -d)"
git clone https://github.com/nrobinson2000/neopo "$TEMPDIR/neopo"
cd "$TEMPDIR/neopo"
$SUDOPY python3 -m pip install .

# Run the neopo installer
neopo install

# Run Particle CLI so that it has a chance to pre-download its dependencies
neopo particle usb configure

# Attempt to install bash completion script
# if [ -d /etc/bash_completion.d ]; then
#     echo "Installing tab completion script:"    
#     $SUDO curl -fsSLo /etc/bash_completion.d/neopo "https://raw.githubusercontent.com/nrobinson2000/neopo/master/completion/neopo"
# else
#     echo "The tab completion script is recommended for the best experience."
#     echo "You can follow the installation instructions here:"
#     echo "  https://neopo.xyz/docs/full-docs#tab-completion"
# fi

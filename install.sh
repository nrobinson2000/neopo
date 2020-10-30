#!/bin/bash

# neopo: A lightweight solution for local Particle development.
# Copyright (c) 2020 Nathan Robinson.

# Docker compatiblity
[ -f "/.dockerenv" ] && SUDO="" || SUDO="sudo"

# Install additional dependencies for Linux
case "$(uname)" in
Linux)
    echo "Installing Linux dependencies..."
    
    # Ubuntu / Debian / Linux Mint
    if hash apt >/dev/null 2>&1; then
        if [ "$(uname -m)" == "x86_64" ]; then
            $SUDO dpkg --add-architecture i386
            $SUDO apt update
            $SUDO apt install libarchive-zip-perl libc6-i386 python3 git vim libncurses5:i386 python3-setuptools
        fi
        # Raspbian
        if [ "$(uname -m)" == "armv7l" ]; then
            $SUDO apt install libarchive-zip-perl libusb-1.0-0-dev dfu-util libudev-dev libisl15 libfl-dev python3 git vim python3-setuptools
        fi

    # Fedora
    elif hash yum >/dev/null 2>&1; then
        $SUDO yum install glibc.i686 perl-Archive-Zip python3 vim git ncurses-compat-libs python3-setuptools
    
    # Void Linux
    elif hash xbps-install >/dev/null 2>&1; then
        $SUDO xbps-install -S dfu-util python3 git vim perl-Archive-Zip void-repo-multilib bash-completion python3-setuptools
        $SUDO xbps-install -S glibc-32bit ncurses-libs-32bit

    # Manjaro / Arch
    elif hash pacman >/dev/null 2>&1; then
        $SUDO pacman -S --needed base-devel
        TEMPDIR="$(mktemp -d)"
        cd "$TEMPDIR"
        git clone https://github.com/nrobinson2000/packages
        cd packages
        ./install-pkg neopo
        exit
    fi
;;

# TODO: Mac dependencies
Darwin) ;;

# This script does not support Windows
*)
    echo "To install neopo on Windows follow the instructions here:"
    echo "  https://neopo.xyz/tutorials/windows"
    exit 1
esac

echo "Downloading installation script..."
TEMPFILE="$(mktemp)"
curl -Lo "$TEMPFILE" "https://raw.githubusercontent.com/nrobinson2000/neopo/master/install.py"
$SUDO python3 "$TEMPFILE" || exit
$SUDO chown "$USER" "$($SUDO which neopo)"
rm "$TEMPFILE"

# Run the neopo installer
neopo install

# Run Particle CLI so that it has a chance to pre-download its dependencies
neopo particle usb configure

# Attempt to install bash completion script
if [ -d /etc/bash_completion.d ]; then
    echo "Installing tab completion script:"    
    $SUDO curl -fsSLo /etc/bash_completion.d/neopo "https://raw.githubusercontent.com/nrobinson2000/neopo/master/neopo/neopo-completion"
else
    echo "The tab completion script is recommended for the best experience."
    echo "You can follow the installation instructions here:"
    echo "  https://neopo.xyz/docs/full-docs#tab-completion"
fi

# Install neopo as python module (experimental)
TEMPDIR="$(mktemp -d)"
git clone https://github.com/nrobinson2000/neopo "$TEMPDIR/neopo"
cd "$TEMPDIR/neopo"
$SUDO python3 setup.py install --optimize=1
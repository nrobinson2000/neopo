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
            $SUDO apt install libarchive-zip-perl libc6-i386 python3 git vim libncurses5:i386
        fi
        # Raspbian
        if [ "$(uname -m)" == "armv7l" ]; then
            $SUDO apt install libarchive-zip-perl libusb-1.0-0-dev dfu-util libudev-dev libisl15 libfl-dev python3 git vim
        fi

    # Fedora
    elif hash yum >/dev/null 2>&1; then
        $SUDO yum install glibc.i686 perl-Archive-Zip python3 vim git ncurses-compat-libs
    
    # Void Linux
    elif hash xbps-install >/dev/null 2>&1; then
        $SUDO xbps-install -Sy dfu-util python3 git vim perl-Archive-Zip void-repo-multilib bash-completion
        $SUDO xbps-install -Sy glibc-32bit ncurses-libs-32bit

    # Manjaro / Arch
    elif hash pacman >/dev/null 2>&1; then
        $SUDO pacman -Sy libusb lib32-glibc python3 vim pamac git
        gpg --keyserver hkp://keys.gnupg.net:80 --recv-keys C52048C0C0748FEE227D47A2702353E0F7E48EDB
        $SUDO yay -S perl-archive-zip lib32-ncurses5-compat-libs
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
curl -Lo "$TEMPFILE" "https://raw.githubusercontent.com/nrobinson2000/neopo/master/bin/install.py"
$SUDO python3 "$TEMPFILE" || exit
$SUDO chown "$USER" "$($SUDO which neopo)"
rm "$TEMPFILE"

# Run the neopo installer
neopo install

# Run Particle CLI so that it has a chance to pre-download its dependencies
neopo particle --version

# Attempt to install bash completion script
if [ -d /etc/bash_completion.d ]; then
    echo "Installing tab completion script:"    
    $SUDO curl -fsSLo /etc/bash_completion.d/neopo "https://raw.githubusercontent.com/nrobinson2000/neopo/master/bin/neopo-completion"
else
    echo "The tab completion script is recommended for the best experience."
    echo "You can follow the installation instructions here:"
    echo "  https://neopo.xyz/docs/full-docs#tab-completion"
fi
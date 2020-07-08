#!/bin/bash

# neopo: A lightweight solution for local Particle development.
# Copyright (c) 2020 Nathan Robinson.

case "$(uname)" in
Linux)
    echo "Installing Linux dependencies..."
    
    if hash apt >/dev/null 2>&1; then
        if [ "$(uname -m)" == "x86_64" ]; then
            sudo apt install libarchive-zip-perl libc6-i386 python3 xxd git
        fi
        if [ "$(uname -m)" == "armv7l" ]; then
            sudo apt install libarchive-zip-perl libusb-1.0-0-dev dfu-util libudev-dev git
        fi

    elif hash yum >/dev/null 2>&1; then
        sudo yum install glibc.i686 perl-Archive-Zip vim git

    elif hash pacman >/dev/null 2>&1; then
        sudo pacman -Syu libusb lib32-glibc vim pamac git
        sudo pamac install perl-archive-zip
    fi
;;

Darwin) ;;

*) >&2 echo "Your OS is not supported! Use Linux or macOS." ; exit 1
esac

echo "Downloading installation script..."
curl -LO "https://raw.githubusercontent.com/nrobinson2000/neopo/master/bin/install.py"
sudo python3 install.py || exit
sudo chown "$USER" "$(sudo which neopo)"
rm install.py

neopo install

if [ "$(uname)" == "Linux" ]; then

    sudo mkdir -p /etc/bash_completion.d

    if [ -d /etc/bash_completion.d ]; then
        echo "Installing tab completion script:"    
        sudo curl -fsSLo /etc/bash_completion.d/neopo "https://raw.githubusercontent.com/nrobinson2000/neopo/master/bin/neopo-completion"
    fi
else
    echo "The tab completion script is recommended for the best experience:"
    echo "You can download it from:"
    echo "  https://raw.githubusercontent.com/nrobinson2000/neopo/master/bin/neopo-completion"
    echo "To load it you would run:"
    echo "  $ source neopo-completion"
fi
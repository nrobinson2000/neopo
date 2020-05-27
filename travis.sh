export PATH="$PATH:$PWD/bin"

if [ "$(uname -s)" == "Linux" ]; then
    sudo apt update
    sudo apt install libarchive-zip-perl libc6-i386
fi

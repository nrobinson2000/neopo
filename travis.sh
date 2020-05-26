export PATH="$PATH:$PWD"

if [ "$(uname -s)" == "Linux" ]; then
sudo apt update
sudo apt install python3-pip libarchive-zip-perl
fi

pip3 install -r requirements.txt

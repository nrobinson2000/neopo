export PATH="$PATH:$PWD"

if [ "$(uname -s)" == "Linux" ]; then
sudo apt update
sudo apt install python3-pip
fi

pip3 install -r requirements.txt

#!/bin/bash

case "$(uname)" in
    Linux)
        a="$HOME/.local/bin/neopo";;
    Darwin)
        a=/usr/local/bin/neopo;;
esac

curl -sLo $a https://raw.githubusercontent.com/nrobinson2000/neopo/master/neopo && chmod +x $a && $a install

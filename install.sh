#!/bin/bash

# neopo: A lightweight solution for local Particle development.
# Copyright (c) 2020 Nathan Robinson.

case "$(uname)" in
    Linux)
        a="$HOME/.local/bin/neopo";;

    Darwin)
        a='/usr/local/bin/neopo';;

    *)
        >&2 echo "OS is not supported! Use Linux or macOS."

        exit 1
esac

echo "Downloading neopo into $a..."

curl -Lo "$a" https://raw.githubusercontent.com/nrobinson2000/neopo/master/bin/neopo && chmod +x "$a" && "$a" install

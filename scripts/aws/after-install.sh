#!/bin/bash
set -euox pipefail

cd /var/lib/codedeploy-apps/HexBug

python3.11 -m venv venv #--clear
# TODO: hack
# we need the rust toolchain to build hexnumgen, and i don't want to install it just for codedeploy
# so run as my user where rust is already installed
sudo su object -c 'source venv/bin/activate && pip install -e ".[runtime]"'

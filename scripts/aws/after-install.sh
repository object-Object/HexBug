#!/bin/bash
set -euox pipefail

cd /var/lib/codedeploy-apps/HexBug

python3.11 -m venv venv #--clear
source venv/bin/activate
pip install -e ".[runtime]"

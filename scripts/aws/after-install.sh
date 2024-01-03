#!/bin/bash
set -euox pipefail

cd /var/lib/codedeploy-apps/HexBug

sudo chown -R object .

python3.11 -m venv venv
source venv/bin/activate
pip install -e ".[runtime,target-linux]"

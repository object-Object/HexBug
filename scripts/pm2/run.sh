#!/bin/bash
set -euo pipefail

source venv/bin/activate
export ENVIRONMENT=prod
python main.py

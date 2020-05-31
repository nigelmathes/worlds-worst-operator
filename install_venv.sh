#!/usr/bin/env bash

python -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements-dev.txt
pip install -r worlds_worst_operator/requirements.txt

deactivate
#!/bin/bash

python -m venv venv
. venv/bin/activate
pip install -r requirements-dev.txt
pip install --editable .
pre-commit install-hooks

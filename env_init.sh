#!/bin/bash

python -m venv venv
. venv/bin/activate
pip install -r requirements-dev.txt
pre-commit install-hooks

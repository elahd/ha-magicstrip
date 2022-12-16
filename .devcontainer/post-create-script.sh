#!/usr/bin/env bash

container install
pip install --upgrade pip
pip install -r requirements-dev.txt
pre-commit install
pre-commit install-hooks
chmod +x /workspaces/ha-magicstrip/.devcontainer/post-set-version-hook.sh

lib_dir="/workspaces/pymagicstrip"
repo_url="https://github.com/elahd/pymagicstrip"

if [ ! -d $lib_dir ]; then
    echo "Cloning pymagicstrip repository..."
    git clone "$repo_url" "$lib_dir"
else
    echo "pymagicstrip repository directory already exists."
fi

cd /workspaces/pymagicstrip
python setup.py develop

pip install -r /workspaces/pymagicstrip/requirements-dev.txt

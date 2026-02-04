#!/bin/bash

set -e

# Activate the python venv
pwd=$(pwd)
cd ../../
. .venv/bin/activate
cd "${pwd}"

# Build the wheel
python -m build --wheel

# Check if the wheel was built
echo
if [ -f dist/*.whl ]; then
    echo "Wheel built successfully in dist/"
else
    echo "Error: Wheel not built"
fi

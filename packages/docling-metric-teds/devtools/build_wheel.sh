#!/bin/bash
set -e

# Build the wheel
pwd="$(pwd)"
cd ../../
uv run python -m build --wheel packages/docling-metric-teds/
cd "${pwd}"

# Check if the wheel was built
echo
if [ -f dist/*.whl ]; then
    echo "Wheel built successfully in dist/"
else
    echo "Error: Wheel not built"
fi

#!/bin/bash

# BRACKETS_DIR="/Users/nli/TEDS-metric/ftn_brackets"
BRACKETS_DIR="/Users/nli/TEDS-metric/dpbench_brackets"

. .venv/bin/activate
python -m apted \
    -f \
    "${BRACKETS_DIR}/GT_01030000000200.pdf_0.bracket" \
    "${BRACKETS_DIR}/pred_01030000000200.pdf_0.bracket"


#!/bin/bash

. .venv/bin/activate


DS_ROOT="/Users/nli/data/datasets/GraniteDocling_table_eval"
BRACKET_ROOT="/Users/nli/TEDS-metric/GraniteDocling_brackets"
REPORT_ROOT="/Users/nli/TEDS-metric/report"


# python -m benchmark.main \
#     -o "export" \
#     -i "${DS_ROOT}" \
#     -s "${BRACKET_ROOT}"


python -m benchmark.main \
    -o "benchmark" \
    -i "${BRACKET_ROOT}" \
    -s "${REPORT_ROOT}"

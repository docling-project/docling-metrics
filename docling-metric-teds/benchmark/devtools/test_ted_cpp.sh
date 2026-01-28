#!/bin/bash

TED="../build/ted"

# BRACKETS_DIR="/Users/nli/TEDS-metric/ftn_brackets"
BRACKETS_DIR="/Users/nli/TEDS-metric/dpbench_brackets"


# "${TED}" file \
#     "${BRACKETS_DIR}/ZBRA.2018.page_89.pdf_172_0.bracket" \
#     "${BRACKETS_DIR}/ZBRA.2018.page_89.pdf_172_0.bracket"

"${TED}" file \
    "${BRACKETS_DIR}/GT_01030000000200.pdf_0.bracket" \
    "${BRACKETS_DIR}/pred_01030000000200.pdf_0.bracket"



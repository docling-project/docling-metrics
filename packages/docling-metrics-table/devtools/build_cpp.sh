#!/bin/bash

# Invariants
readonly BUILD_TYPE="Debug"  # One of ["Debug", "Release"]
readonly BUILD_DIR="build"
readonly EXTERNALS_DIR="externals"
readonly INSTALL_DIR="docling_metrics_table"

# Resolve venv: explicit $1 > activated venv > monorepo default
VENV_ROOT="${1:-${VIRTUAL_ENV:-../../.venv}}"
readonly VENV_ROOT


###########################################################################################
# Resolve python
#
if [ ! -x "${VENV_ROOT}/bin/python3" ]; then
    echo "No usable venv at '${VENV_ROOT}'."
    echo "Activate one (e.g. '. ../../.venv_py3.14.3/bin/activate') or pass its path as \$1."
    exit 1
fi

python_bin="$(cd "${VENV_ROOT}/bin"; pwd)/python3"
echo "Using $(${python_bin} --version) from ${VENV_ROOT}"


###########################################################################################
# Clean up dirs
#
# Also drop extension modules from previous runs: `cmake --install` below writes into
# the source package dir, so builds under different interpreters would otherwise pile up
rm -rf "${BUILD_DIR}" "${EXTERNALS_DIR}"
rm -f "${INSTALL_DIR}"/*.so



###########################################################################################
# Compile
#
cmake \
    -G Ninja \
    -S . \
    -B "${BUILD_DIR}" \
    -DPython3_EXECUTABLE="${python_bin}" \
    -DCMAKE_EXPORT_COMPILE_COMMANDS=1 \
    -DCMAKE_BUILD_TYPE="${BUILD_TYPE}"

cmake --build "${BUILD_DIR}" -j16


###########################################################################################
# Install
#
cmake --install "${BUILD_DIR}"


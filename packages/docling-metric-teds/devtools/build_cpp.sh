#!/bin/bash

# Invariants
readonly BUILD_TYPE="Debug"  # One of ["Debug", "Release"]
readonly BUILD_DIR="build"
readonly EXTERNALS_DIR="externals"
readonly VENV_ROOT="../../.venv"


###########################################################################################
# Resolve python
#
if [ ! -d "${VENV_ROOT}" ]; then
    echo "Missing venv at the root of the monorepo"
    exit 1
fi

python_root=$(cd "${VENV_ROOT}/bin"; pwd)
python_bin="${python_root}/python3"


###########################################################################################
# Clean up dirs
rm -rf "${BUILD_DIR}" "${EXTERNALS_DIR}"



###########################################################################################
# Compile

cmake \
    -S . \
    -B "${BUILD_DIR}" \
    -DPython3_EXECUTABLE="${python_bin}" \
    -DCMAKE_EXPORT_COMPILE_COMMANDS=1 \
    -DCMAKE_BUILD_TYPE="${BUILD_TYPE}"


cmake --build "${BUILD_DIR}" -j16



###########################################################################################
# Install
cmake --install "${BUILD_DIR}"


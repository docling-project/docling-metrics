#!/bin/bash

# Invariants
readonly BUILD_TYPE="Debug"  # One of ["Debug", "Release"]
readonly BUILD_DIR="build"
readonly INSTALL_DIR="install_root"
readonly EXTERNALS_DIR="externals"


###########################################################################################
# Prepare directories
rm -rf "${BUILD_DIR}" "${INSTALL_DIR}" "${EXTERNALS_DIR}"
mkdir "${BUILD_DIR}"


###########################################################################################
# Compile

cmake \
    -S . \
    -B "${BUILD_DIR}" \
    -DCMAKE_EXPORT_COMPILE_COMMANDS=1 \
    -DCMAKE_BUILD_TYPE="${BUILD_TYPE}"

cmake --build "${BUILD_DIR}" -j16


###########################################################################################
# Test
ctest --test-dir "${BUILD_DIR}"


###########################################################################################
# Install
cmake --install "${BUILD_DIR}"


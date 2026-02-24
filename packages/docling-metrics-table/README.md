# Docling metrics for document tables

Docling metrics for document tables.


## Overview

The following metrics are used:

- Tree Edit Distance.
- GriTS (coming).


<details>
    <summary>**Directory structure:**</summary>
Before building the C++ code, we have only the source code directories:

```
.
├── devtools              # Various bash scripts, useful with C++ development
├── cmake                 # Cmake files required to compile the C++ code.
├── cpp_src               # C++ source code
├── cpp_tests             # C++ source code for the test
├── docling_metrics_table   # Python wrapper for the C++ bindings that implements the docling-metrics-core API
└── test                  # Python tests
```


After building the C++ code we have the following directories:

```
.
├── build                  # C++ build directory required during the build process
├── cmake
├── cpp_src
├── cpp_test
├── docling_metrics_table
├── externals              # C++ code of external libraries. Required during the compilation.
└── tests

```
</details>


## Installation

All C++ and Python code is managed by `uv`. The following command starts the workflow that:

1. Installs all Python dependencies.
2. Builds the C++ code including the C++ external dependencies.
3. Installs the `*.so` file with the python bindings inside the uv venv.

```bash
uv sync --all-packages
```

In case a manual compilation of the C++ code is needed, you can use the bash scripts from `devtools/`:

Build the C++ code:

```bash
devtools/build_cpp.sh
```

Run the native C++ tests:

```bash
devtools/test_cpp.sh
```


## Usage

Check the [demo code](demo/demo_docling_metrics_table.py)


## Links

[tree-similarity](https://github.com/DatabaseGroup/tree-similarity)


## License

MIT

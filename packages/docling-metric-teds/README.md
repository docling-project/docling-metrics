# Docling metric for the Tree-Edit-Distance Score

This is an optimized implementation of the Tree Edit Distance Score.


## Overview

Main features:

- Parallelized C++ implementation.
- Python bindings.
- Docling API.

This repo builds on top of the [tree-similarity](https://github.com/DatabaseGroup/tree-similarity)


## Directory structure

Before building the C++ code, we have only the source code directories:

```
.
├── devtools              # Various bash scripts, useful with C++ development
├── cmake                 # Cmake files required to compile the C++ code.
├── cpp_src               # C++ source code
├── cpp_tests             # C++ source code for the test
├── docling_metric_teds   # Python wrapper for the C++ bindings that implements the docling-metrics-core API
└── test                  # Python tests
```


After building the C++ code we have the following directories:

```
.
├── build                  # C++ build directory required during the build process
├── cmake
├── cpp_src
├── cpp_test
├── docling_metric_teds
├── externals              # C++ code of external libraries. Required during the compilation.
└── tests

```

## Installation

All C++ and Python code is managed by `uv`. The following command starts the workflow that:

1. Installs all Python dependencies.
2. Builds the C++ code including the C++ external dependencies.
3. Installs the `*.so` file with the python bindings inside the uv venv.

```bash
uv sync -v --all-extras
```

In case a manual compilation of the C++ code is needed, you can use the bash scripts from `devtools/`:

Build C++ code:

```bash
devtools/build_cpp.sh
```

Run C++ tests:

```bash
devtools/test_cpp.sh
```


## Usage

```python
from docling_metric_teds.docling_metric_teds import (
    TEDSMetric,
    TEDSMetricInputSample,
    TEDSMetricSampleEvaluation,
)

sample = TEDSMetricInputSample(
    id="s1",
    gt_bracket="{x{a}{b}}",
    pred_bracket="{x{a}{c}}",
)
teds_metric = TEDSMetric()

sample_evaluation: TEDSMetricSampleEvaluation = teds_metric.evaluate_sample(sample)
print(sample_evaluation)
```


## Links

[tree-similarity](https://github.com/DatabaseGroup/tree-similarity)


## License

MIT

# docling-metric-hello-world-cpp

A minimal example metric implementation demonstrating a C++ (pybind11) backend
on top of `docling-metrics-core`.

## Overview

This package provides a simple "Hello World" metric that:
- Accepts string payloads as input samples
- Always returns a score of `1.0` for each sample evaluation
- Demonstrates a C++ extension using pybind11 and scikit-build-core

## Installation

From the monorepo root directory:

```bash
# 1. Create the uv venv
uv venv -p <python_version>

# 2. Build the C++ code and install all python dependencies
uv sync -v --all-extras
```

The compiled `*.so` file is placed by in the monorepo venv.

In case you want to manualy build the C++ code (e.g. for debugging/development reasons):

```bash
cmake -S . -B build/
cmake --build build/
cmake --install build/
```

The compiled `*.so` file is located in `docling_metric_hello_world_cpp/` dir.


## Usage

```python
from docling_metric_hello_world_cpp import HelloWorldMetric, StringInputSample

metric = HelloWorldMetric()

sample_a = StringInputSample(id="sample-1", payload="Hello")
sample_b = StringInputSample(id="sample-1", payload="World")

result = metric.evaluate_sample(sample_a, sample_b)
print(result.score)  # Always 1.0
```

## License

MIT

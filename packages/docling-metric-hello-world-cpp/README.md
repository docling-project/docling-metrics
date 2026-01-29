# docling-metric-hello-world-cpp

A minimal example metric implementation demonstrating a C++ (pybind11) backend
on top of `docling-metrics-core`.

## Overview

This package provides a simple "Hello World" metric that:
- Accepts string payloads as input samples
- Always returns a score of `1.0` for each sample evaluation
- Demonstrates a C++ extension using pybind11 and scikit-build-core

## Installation

```bash
pip install docling-metric-hello-world-cpp
```

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

# docling-metrics-hello-world

A minimal example metric implementation demonstrating how to build metrics on top of
`docling-metrics-core`.

## Overview

This package provides a simple "Hello World" metric that:
- Accepts string payloads as input samples
- Always returns a score of `1.0` for each sample evaluation
- Demonstrates the basic structure for implementing custom metrics

## Installation

```bash
pip install docling-metrics-hello-world
```

## Usage

```python
from docling_metrics_hello_world import HelloWorldMetric, StringInputSample

# Create metric instance
metric = HelloWorldMetric()

# Create sample inputs
sample_a = StringInputSample(id="sample-1", payload="Hello")
sample_b = StringInputSample(id="sample-1", payload="World")

# Evaluate a single sample pair
result = metric.evaluate_sample(sample_a, sample_b)
print(result.score)  # Always 1.0

# Evaluate multiple sample pairs
pairs = [
    (StringInputSample(id="1", payload="a"), StringInputSample(id="1", payload="b")),
    (StringInputSample(id="2", payload="c"), StringInputSample(id="2", payload="d")),
]
aggregate = metric.evaluate_dataset(pairs)
print(aggregate.mean_score)  # 1.0
print(aggregate.sample_count)  # 2
```

## License

MIT

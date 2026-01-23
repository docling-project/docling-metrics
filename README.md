# docling-metric-types

A minimal interface for computing and aggregating metrics on paired data samples.

## Overview

This package provides base types for building metrics that:
- Evaluate pairs of input samples (e.g., ground-truth vs. prediction)
- Produce per-sample results traceable by sample ID
- Aggregate results across multiple samples

## Core Types

- **`BaseInputSample`** — Input data with a unique `id` shared between sample pairs
- **`BaseSampleResult`** — Output of evaluating a single sample pair
- **`BaseAggregateResult`** — Output of aggregating multiple sample results
- **`BaseMetric`** — Abstract interface defining `evaluate_sample`, `aggregate`, and `evaluate_dataset`

## Installation

```bash
pip install docling-metric-types
```

## Requirements

- Python >=3.10,<4.0

## Usage

*Coming soon*

## Development

```bash
# Install in development mode
uv sync

# Run tests
uv run pytest
```

## License

MIT

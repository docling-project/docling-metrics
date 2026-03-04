# docling-metrics-chemistry

Chemistry evaluation metrics (SMILES and Markush structures) for the Docling metrics framework.

## Installation

```bash
pip install docling-metrics-chemistry
```

## Package Structure

```
docling_metrics_chemistry/
├── __init__.py            # Public API exports
├── smiles_metric.py       # BaseMetric implementation (SmilesMetric)
├── molecule_scores.py     # Score computation (Tanimoto, InChI, Markush)
├── smiles_utils.py        # Molecule parsing, canonicalization, wildcard replacement
└── cxsmiles_parser.py     # CXSMILES section parsing (M-sections, Sg-sections)
```

## Key Classes

### `SmilesMetric`

The main metric class implementing the `BaseMetric` interface. Provides three methods:

- `evaluate_sample(sample)` — evaluate a single predicted/ground-truth SMILES pair
- `aggregate(results)` — compute summary statistics from multiple sample results
- `evaluate_dataset(samples)` — evaluate an entire dataset (calls both of the above)

### `SmilesInputSample`

Input model for a single evaluation sample.

| Field               | Type                              | Default | Description                                      |
|---------------------|-----------------------------------|---------|--------------------------------------------------|
| `id`                | `str`                             | —       | Unique sample identifier                         |
| `predicted_smiles`  | `str`                             | —       | Predicted SMILES or CXSMILES string              |
| `gt_smiles`         | `str`                             | —       | Ground truth SMILES or CXSMILES string           |
| `is_markush`        | `bool`                            | `False` | Use Markush/CXSMILES evaluation mode             |
| `remove_stereo`     | `bool`                            | `True`  | Remove stereochemistry before comparison         |

### `SmilesSampleResult`

Per-sample result with all computed scores.

| Field                 | Type              | Description                                       |
|-----------------------|-------------------|---------------------------------------------------|
| `valid`               | `bool`            | Whether the predicted SMILES is chemically valid   |
| `tanimoto`            | `float`           | Tanimoto fingerprint similarity (0–1)              |
| `tanimoto1`           | `bool`            | Whether Tanimoto equals 1.0                        |
| `inchi_equality`      | `bool`            | Whether InChI representations match                |
| `string_equality`     | `bool`            | Whether SMILES strings are identical               |
| `r`                   | `Optional[float]` | R-group label accuracy (Markush only)              |
| `m`                   | `Optional[float]` | M-section accuracy (Markush only)                  |
| `sg`                  | `Optional[float]` | Sg-section accuracy (Markush only)                 |
| `num_fragments_gt`    | `int`             | Fragment count in ground truth                     |
| `num_fragments_pred`  | `int`             | Fragment count in prediction                       |
| `num_fragments_equal` | `bool`            | Whether fragment counts match                      |
| `cxsmi_equality`      | `bool`            | Overall CXSMILES equality (Markush only)           |

### `SmilesAggregateResult`

Aggregated statistics across a dataset.

| Field                  | Type              | Description                                    |
|------------------------|-------------------|------------------------------------------------|
| `sample_count`         | `int`             | Number of evaluated samples                    |
| `mean_tanimoto`        | `float`           | Mean Tanimoto similarity                       |
| `validity_rate`        | `float`           | Fraction of valid predictions                  |
| `inchi_equality_rate`  | `float`           | Fraction with matching InChI                   |
| `string_equality_rate` | `float`           | Fraction with exact string match               |
| `mean_r`               | `Optional[float]` | Mean R-group accuracy (Markush samples only)   |
| `mean_m`               | `Optional[float]` | Mean M-section accuracy (Markush samples only) |
| `mean_sg`              | `Optional[float]` | Mean Sg-section accuracy (Markush samples only)|
| `cxsmi_equality_rate`  | `Optional[float]` | Fraction with full CXSMILES equality           |

## Metrics

- **Tanimoto similarity**: RDKit fingerprint-based molecular similarity (0–1)
- **InChI equality**: International Chemical Identifier comparison
- **String equality**: Exact canonical SMILES string match
- **Validity**: Whether a SMILES string parses into a valid molecule
- **Markush evaluation**: R-group, M-section, Sg-section accuracy for CXSMILES

## Usage

### Simple molecule evaluation

```python
from docling_metrics_chemistry import SmilesMetric, SmilesInputSample

metric = SmilesMetric()

# Evaluate a single pair
sample = SmilesInputSample(
    id="sample_1",
    predicted_smiles="CCO",
    gt_smiles="CCO",
)
result = metric.evaluate_sample(sample)
print(result.tanimoto)        # 1.0
print(result.inchi_equality)  # True
print(result.valid)           # True
```

### Dataset evaluation

```python
samples = [
    SmilesInputSample(id="1", predicted_smiles="CCO", gt_smiles="CCO"),
    SmilesInputSample(id="2", predicted_smiles="c1ccccc1", gt_smiles="C1=CC=CC=C1"),
    SmilesInputSample(id="3", predicted_smiles="INVALID", gt_smiles="CCO"),
]

aggregate = metric.evaluate_dataset(samples)
print(aggregate.mean_tanimoto)        # Mean Tanimoto across all samples
print(aggregate.validity_rate)        # Fraction of valid predictions
print(aggregate.inchi_equality_rate)  # Fraction with matching InChI
```

### Markush structure evaluation

```python
# Evaluate CXSMILES with R-groups, M-sections, and Sg-sections
sample = SmilesInputSample(
    id="markush_1",
    predicted_smiles="*C(=O)O.*Cl |m:4:10.11.12.9|",
    gt_smiles="*C(=O)O.*Cl |m:4:10.11.12.9|",
    is_markush=True,
)
result = metric.evaluate_sample(sample)
print(result.r)               # R-group label accuracy (0-1 or None)
print(result.m)               # M-section accuracy (0-1 or None)
print(result.sg)              # Sg-section accuracy (0-1 or None)
print(result.cxsmi_equality)  # Overall CXSMILES match
```


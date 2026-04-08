"""Integration smoke test using persisted JSON vectors.

These JSON files are derived from the original PKL evaluation artifacts and live
in `tests/data`.
"""

from __future__ import annotations

import json
from pathlib import Path

from docling_metrics_chemistry import SmilesInputSample, SmilesMetric


def _load_json_list(filename: str) -> list:
    data_path = Path(__file__).parent / "data" / filename
    with data_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_evaluate_dataset_from_json_files() -> None:
    predicted = _load_json_list("test_predicted_smiles_list.json")
    gt = _load_json_list("test_gt_smiles_list.json")

    assert len(predicted) == len(gt)

    # Keep the test fast; we just want an end-to-end check.
    n = min(200, len(gt))

    samples: list[SmilesInputSample] = []
    for i in range(n):
        p = predicted[i]
        g = gt[i]
        if p is None or g is None:
            continue

        samples.append(
            SmilesInputSample(
                id=str(i),
                predicted_smiles=p,
                gt_smiles=g,
                is_markush=True,
            )
        )

    metric = SmilesMetric()
    aggregate = metric.evaluate_dataset(samples)

    assert aggregate.sample_count == len(samples)
    assert 0.0 <= aggregate.validity_rate <= 1.0
    assert 0.0 <= aggregate.mean_tanimoto <= 1.0


def test_evaluate_dataset_opt_from_json_files() -> None:
    predicted = _load_json_list("test_predicted_smiles_opt_list.json")
    gt = _load_json_list("test_gt_smiles_opt_list.json")

    assert len(predicted) == len(gt)

    # Keep the test fast; we just want an end-to-end check.
    n = min(200, len(gt))

    samples: list[SmilesInputSample] = []
    for i in range(n):
        p = predicted[i]
        g = gt[i]
        if p is None or g is None:
            continue

        samples.append(
            SmilesInputSample(
                id=str(i),
                predicted_smiles=p,
                gt_smiles=g,
                is_markush=True,
            )
        )

    metric = SmilesMetric()
    aggregate = metric.evaluate_dataset(samples)

    assert aggregate.sample_count == len(samples)
    assert 0.0 <= aggregate.validity_rate <= 1.0
    assert 0.0 <= aggregate.mean_tanimoto <= 1.0

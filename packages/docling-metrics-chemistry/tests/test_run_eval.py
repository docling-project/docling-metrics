import json
from pathlib import Path

from docling_metrics_chemistry import SmilesInputSample, SmilesMetric


def load_json(name):
    p = Path("packages/docling-metrics-chemistry/tests/data") / name
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def run_eval(predicted_name, gt_name, label):
    predicted = load_json(predicted_name)
    gt = load_json(gt_name)

    samples = []
    for i, (p, g) in enumerate(zip(predicted, gt)):
        if g is None:
            continue

        # Missing predictions should be counted as wrong/invalid
        if p is None:
            p = ""

        samples.append(
            SmilesInputSample(
                id=str(i), predicted_smiles=p, gt_smiles=g, is_markush=True
            )
        )

    metric = SmilesMetric()
    aggregate = metric.evaluate_dataset(samples)

    print(f"\n=== {label} ===")
    print(f"Total Samples:      {aggregate.sample_count}")
    print(f"Validity Rate:      {aggregate.validity_rate:.4f}")

    # Specific metrics requested:
    print(f"CXSMILES Equality:  {getattr(aggregate, 'cxsmi_equality_rate', 0.0):.4f}")
    print(f"InChI Equality:     {getattr(aggregate, 'inchi_equality_rate', 0.0):.4f}")
    print(f"ar_r:               {getattr(aggregate, 'mean_r', 0.0):.4f}")
    print(f"ar_m:               {getattr(aggregate, 'mean_m', 0.0):.4f}")
    print(f"ar_sg:              {getattr(aggregate, 'mean_sg', 0.0):.4f}")
    print(f"String Equality:    {getattr(aggregate, 'string_equality_rate', 0.0):.4f}")


run_eval(
    "test_predicted_smiles_list.json", "test_gt_smiles_list.json", "Standard Dataset"
)

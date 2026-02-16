import json
from pathlib import Path

from docling_metrics_text import TextMetrics
from docling_metrics_text.docling_metrics_text import TextPairSample
from docling_metrics_text.utils.data_loader import FileEntry, TextFileLoader

MD_DIR = Path(__file__).parent / "data" / "md"
METRICS = Path(__file__).parent / "data" / "metrics.json"
RELATIVE_TOLERANCE = 1e-6


def test_text_metrics():
    r""" """
    loader = TextFileLoader(Path(MD_DIR))
    metrics_calculator = TextMetrics()

    metrics_dict = {}

    # Load the expected metrics from the JSON file
    with open(METRICS, "r") as f:
        expected_metrics = json.load(f)

    file_entry: FileEntry
    for file_entry in loader.load():
        id = file_entry.id
        gt = file_entry.pivot_content
        pred = file_entry.target_content
        assert pred

        # Create a TextPairSample with the same content for both text_a and text_b
        sample = TextPairSample(id=id, text_a=gt, text_b=pred)

        # Compute metrics
        result = metrics_calculator.evaluate_sample(sample)

        # Store metrics in the dictionary
        computed_metrics = {
            "f1_score": result.f1_score,
            "precision_score": result.precision_score,
            "recall_score": result.recall_score,
            "edit_distance_score": result.edit_distance_score,
            "bleu_score": result.bleu_score,
            "meteor_score": result.meteor_score,
        }
        metrics_dict[id] = computed_metrics

        # Validate computed metrics against expected metrics
        if id not in expected_metrics:
            continue
        expected = expected_metrics[id]
        for metric_name, computed_value in computed_metrics.items():
            expected_value = expected[metric_name]

            # Check if values are within relative tolerance
            assert abs(computed_value - expected_value) <= RELATIVE_TOLERANCE, (
                f"Metric {metric_name} for {id}: expected {expected_value}, got {computed_value}"
            )


if __name__ == "__main__":
    test_text_metrics()

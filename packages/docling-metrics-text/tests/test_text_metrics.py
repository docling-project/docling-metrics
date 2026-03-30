import json
import multiprocessing as mp
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


def test_extreme_cases():
    r"""Test TextMetrics behavior when scores cannot be computed."""
    # Test Case 1: Empty text_b with default error_score
    metrics_calculator = TextMetrics()
    sample = TextPairSample(id="0", text_a="some text", text_b="")
    result = metrics_calculator.evaluate_sample(sample)

    # print(f"Default error: {result}")
    assert result.f1_score == -1.0
    assert result.precision_score == -1.0
    assert result.bleu_score == -1.0

    # Test Case 2: Custom error_score
    metrics_calculator_custom = TextMetrics(error_score=-2.0)
    sample = TextPairSample(id="1", text_a="some text", text_b="")
    result = metrics_calculator_custom.evaluate_sample(sample)
    # print(f"Custom error: {result}")

    assert result.f1_score == -2.0
    assert result.precision_score == -2.0
    assert result.bleu_score == -2.0


def _compute_bleu_in_process(
    sample_id: str,
    text_a: str,
    text_b: str,
    expected_bleu: float,
    result_queue: mp.Queue,
) -> None:
    r"""Compute BLEU in a child process and report the outcome."""
    try:
        metrics_calculator = TextMetrics()
        sample = TextPairSample(id=sample_id, text_a=text_a, text_b=text_b)
        computed_bleu = metrics_calculator.evaluate_sample(sample).bleu_score

        # Check if values are within relative tolerance
        assert abs(computed_bleu - expected_bleu) <= RELATIVE_TOLERANCE, (
            f"Concurrent BLEU computation for {sample_id}: "
            f"expected {expected_bleu}, got {computed_bleu}"
        )
        result_queue.put(("ok", sample_id, computed_bleu))
    except Exception as exc:
        result_queue.put(("error", sample_id, repr(exc)))


def test_multiple_bleu():
    r"""Test that multiple BLEU metrics can run in parallel"""
    loader = TextFileLoader(Path(MD_DIR))

    # Load the expected metrics from the JSON file
    with open(METRICS, "r") as f:
        expected_metrics = json.load(f)

    entries = list(loader.load())
    assert entries

    # Initialize the context
    ctx = mp.get_context("spawn")
    with ctx.Manager() as manager:
        result_queue = manager.Queue()

        processes = []
        file_entry: FileEntry
        for file_entry in entries:
            sample_id = file_entry.id
            assert sample_id in expected_metrics, (
                f"Missing expected metrics for {sample_id}"
            )
            assert file_entry.target_content is not None

            expected_bleu = expected_metrics[sample_id]["bleu_score"]
            processes.append(
                ctx.Process(
                    target=_compute_bleu_in_process,
                    args=(
                        sample_id,
                        file_entry.pivot_content,
                        file_entry.target_content,
                        expected_bleu,
                        result_queue,
                    ),
                )
            )

        print(f"Computing BLEU in {len(processes)} concurrent processes")
        for process in processes:
            process.start()

        for process in processes:
            process.join(timeout=120)
            assert process.exitcode == 0, (
                f"BLEU worker failed with exit code {process.exitcode}"
            )

        results = [result_queue.get(timeout=10) for _ in processes]
        for status, sample_id, payload in results:
            assert status == "ok", (
                f"BLEU computation raised an exception for {sample_id}: {payload}"
            )
            assert isinstance(payload, float)
            assert payload >= 0.0


if __name__ == "__main__":
    test_text_metrics()
    test_extreme_cases()
    test_multiple_bleu()

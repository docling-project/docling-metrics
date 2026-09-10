import json
import logging
from pathlib import Path

import pytest
from docling_metrics_text import TextMetrics
from docling_metrics_text.docling_metrics_text import TextPairSample
from docling_metrics_text.utils.data_loader import FileEntry, TextFileLoader

MD_DIR = Path(__file__).parent / "data" / "md"
METRICS = Path(__file__).parent / "data" / "metrics.json"
RELATIVE_TOLERANCE = 1e-6
TEXT_METRICS_LOGGER = "docling_metrics_text.docling_metrics_text"


@pytest.fixture(scope="module")
def metrics_calculator() -> TextMetrics:
    r"""One TextMetrics instance shared by the BLEU edge-case tests."""
    return TextMetrics()


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


@pytest.mark.parametrize(
    "text_a, text_b",
    [
        pytest.param("some text", "", id="empty_reference"),
        pytest.param("some text", " \n\t ", id="whitespace_reference"),
        pytest.param("", "some text", id="empty_prediction"),
        pytest.param("", "", id="both_empty"),
    ],
)
def test_bleu_undefined_returns_error_score(
    metrics_calculator: TextMetrics,
    caplog: pytest.LogCaptureFixture,
    text_a: str,
    text_b: str,
):
    r"""BLEU has no value without tokens on both sides: error_score + warning."""
    with caplog.at_level(logging.WARNING, logger=TEXT_METRICS_LOGGER):
        score = metrics_calculator._compute_bleu(text_a, text_b)

    assert score == -1.0
    assert any("BLEU is undefined" in rec.message for rec in caplog.records)

    # The same sample goes through the public entry point without raising
    sample = TextPairSample(id="undefined", text_a=text_a, text_b=text_b)
    result = metrics_calculator.evaluate_sample(sample)
    assert result.bleu_score == -1.0


def test_bleu_undefined_uses_custom_error_score():
    r"""The undefined case honours a custom error_score."""
    metrics_calculator = TextMetrics(error_score=-2.0)

    assert metrics_calculator._compute_bleu("some text", "") == -2.0
    assert metrics_calculator._compute_bleu("", "some text") == -2.0
    assert metrics_calculator._compute_bleu("", "") == -2.0


def test_bleu_defined_for_non_empty_texts(metrics_calculator: TextMetrics):
    r"""The pre-check must not affect ordinary inputs."""
    score = metrics_calculator._compute_bleu(
        "the cat sat on the mat", "the cat sat on the mat"
    )
    assert score == pytest.approx(1.0)


def test_bleu_unexpected_exception_is_logged(
    metrics_calculator: TextMetrics,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
):
    r"""A failure inside the BLEU computation is logged, not silently swallowed."""

    def failing_compute(*args, **kwargs):
        raise RuntimeError("synthetic failure")

    monkeypatch.setattr(metrics_calculator._bleu_eval, "compute", failing_compute)

    with caplog.at_level(logging.WARNING, logger=TEXT_METRICS_LOGGER):
        score = metrics_calculator._compute_bleu("some text", "other text")

    assert score == -1.0
    record = next(
        rec for rec in caplog.records if "BLEU computation failed" in rec.message
    )
    assert record.exc_info is not None
    assert record.exc_info[0] is RuntimeError


if __name__ == "__main__":
    test_text_metrics()
    test_extreme_cases()

"""Tests for the HelloWorld metric."""

from docling_metric_hello_world import (
    HelloWorldMetric,
    StringInputSample,
)


def test_evaluate_sample_returns_one() -> None:
    """Test that evaluate_sample always returns score of 1.0."""
    metric = HelloWorldMetric()
    sample = StringInputSample(id="s1", payload_a="p_a", payload_b="p_b")
    result = metric.evaluate_sample(sample)

    assert result.id == "s1"
    assert result.score == 1.0


def test_evaluate_dataset() -> None:
    """Test evaluating a dataset of sample pairs."""
    metric = HelloWorldMetric()
    data = [
        StringInputSample(id="1", payload_a="a1", payload_b="b1"),
        StringInputSample(id="1", payload_a="a2", payload_b="b2"),
    ]

    aggregate = metric.evaluate_dataset(data)

    assert aggregate.sample_count == 2
    assert aggregate.mean_score == 1.0

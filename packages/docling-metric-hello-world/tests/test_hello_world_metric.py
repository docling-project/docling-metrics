"""Tests for the HelloWorld metric."""

from docling_metric_hello_world import (
    HelloWorldMetric,
    StringInputSample,
)


def test_evaluate_sample_returns_one() -> None:
    """Test that evaluate_sample always returns score of 1.0."""
    metric = HelloWorldMetric()
    sample_a = StringInputSample(id="s1", payload="foo")
    sample_b = StringInputSample(id="s1", payload="bar")

    result = metric.evaluate_sample(sample_a, sample_b)

    assert result.id == "s1"
    assert result.score == 1.0


def test_evaluate_dataset() -> None:
    """Test evaluating a dataset of sample pairs."""
    metric = HelloWorldMetric()
    pairs = [
        (
            StringInputSample(id="1", payload="a"),
            StringInputSample(id="1", payload="b"),
        ),
        (
            StringInputSample(id="2", payload="c"),
            StringInputSample(id="2", payload="d"),
        ),
    ]

    aggregate = metric.evaluate_dataset(pairs)

    assert aggregate.sample_count == 2
    assert aggregate.mean_score == 1.0

"""Tests for the HelloWorld C++ metric."""

from docling_metrics_hello_world_cpp import HelloWorldMetric, StringInputSample


def test_evaluate_sample_returns_one() -> None:
    metric = HelloWorldMetric()
    sample = StringInputSample(id="s1", payload_a="foo", payload_b="bar")
    result = metric.evaluate_sample(sample)

    assert result.id == "s1"
    assert result.score == 1.0


def test_evaluate_dataset() -> None:
    metric = HelloWorldMetric()
    data = [
        StringInputSample(id="1", payload_a="a1", payload_b="b1"),
        StringInputSample(id="2", payload_a="a2", payload_b="b2"),
    ]

    aggregate = metric.evaluate_dataset(data)

    assert aggregate.sample_count == 2
    assert aggregate.mean_score == 1.0

"""Tests for the HelloWorld C++ metric."""

from docling_metric_hello_world_cpp import HelloWorldMetric, StringInputSample


def test_evaluate_sample_returns_one() -> None:
    metric = HelloWorldMetric()
    sample = StringInputSample(id="s1", payload="foo")
    result = metric.evaluate_sample(sample)

    assert result.id == "s1"
    assert result.score == 1.0


def test_evaluate_dataset() -> None:
    metric = HelloWorldMetric()
    data = [
        StringInputSample(id="1", payload="a"),
        StringInputSample(id="2", payload="b"),
    ]

    aggregate = metric.evaluate_dataset(data)

    assert aggregate.sample_count == 2
    assert aggregate.mean_score == 1.0

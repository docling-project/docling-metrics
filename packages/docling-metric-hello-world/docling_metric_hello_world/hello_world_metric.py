"""Hello World metric implementation demonstrating the docling-metrics-core interface."""

from typing import Annotated, Iterable

from docling_metrics_core.base_types import (
    BaseAggregateResult,
    BaseInputSample,
    BaseMetric,
    BaseSampleResult,
)
from pydantic import Field


class StringInputSample(BaseInputSample):
    """Input sample with a string payload."""

    payload_a: Annotated[str, Field(description="String payload A for this sample")]
    payload_b: Annotated[str, Field(description="String payload B for this sample")]


class HelloWorldSampleResult(BaseSampleResult):
    """Result of evaluating a single sample pair."""

    score: Annotated[
        float, Field(description="The evaluation score (always 1.0 for this metric)")
    ]


class HelloWorldAggregateResult(BaseAggregateResult):
    """Aggregated result from multiple sample evaluations."""

    mean_score: Annotated[
        float, Field(description="Mean score across all evaluated samples")
    ]


class HelloWorldMetric(BaseMetric):
    """A minimal example metric that always returns 1.0.

    This metric demonstrates the basic structure for implementing custom metrics
    using the docling-metrics-core base types. It accepts string payloads as input
    and always produces a score of 1.0 for each sample evaluation.
    """

    def evaluate_sample(  # type: ignore[override]
        self,
        sample: StringInputSample,
    ) -> HelloWorldSampleResult:
        """Evaluate a single sample pair.

        Args:
            sample_a: First input sample with string payload.
            sample_b: Second input sample with string payload.

        Returns:
            HelloWorldSampleResult with score always equal to 1.0.
        """
        return HelloWorldSampleResult(id=sample.id, score=1.0)

    def aggregate(  # type: ignore[override]
        self, results: Iterable[HelloWorldSampleResult]
    ) -> HelloWorldAggregateResult:
        """Aggregate multiple sample results.

        Args:
            results: Iterable of sample evaluation results.

        Returns:
            HelloWorldAggregateResult with mean score and sample count.
        """
        results_list = list(results)
        sample_count = len(results_list)
        if sample_count == 0:
            return HelloWorldAggregateResult(sample_count=0, mean_score=0.0)

        total_score = sum(r.score for r in results_list)
        return HelloWorldAggregateResult(
            sample_count=sample_count, mean_score=total_score / sample_count
        )

    def evaluate_dataset(  # type: ignore[override]
        self, sample_pairs: Iterable[StringInputSample]
    ) -> HelloWorldAggregateResult:
        """Evaluate an entire dataset of sample pairs.

        Args:
            sample_pairs: Iterable of (sample_a, sample_b) tuples.

        Returns:
            HelloWorldAggregateResult with aggregated statistics.
        """
        results = [self.evaluate_sample(sample) for sample in sample_pairs]
        return self.aggregate(results)

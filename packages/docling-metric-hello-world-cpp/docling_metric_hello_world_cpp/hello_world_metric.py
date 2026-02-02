"""Hello World metric implementation using a C++ backend."""

from typing import Annotated, Iterable

from docling_metrics_core.base_types import (
    BaseAggregateResult,
    BaseInputSample,
    BaseMetric,
    BaseSampleResult,
)
from pydantic import Field

from ._hello_world_cpp import evaluate_sample as cpp_evaluate_sample


class StringInputSample(BaseInputSample):
    """Input sample with a string payload."""

    payload: Annotated[str, Field(description="The string payload for this sample")]


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
    """A minimal example metric that always returns 1.0, backed by C++."""

    def evaluate_sample(  # type: ignore[override]
        self, sample: StringInputSample
    ) -> HelloWorldSampleResult:
        score = float(cpp_evaluate_sample(sample.id, sample.payload))
        return HelloWorldSampleResult(id=sample.id, score=score)

    def aggregate(  # type: ignore[override]
        self, results: Iterable[HelloWorldSampleResult]
    ) -> HelloWorldAggregateResult:
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
        results = [self.evaluate_sample(sample) for sample in sample_pairs]
        return self.aggregate(results)

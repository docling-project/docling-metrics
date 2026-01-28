from abc import ABC, abstractmethod
from typing import Annotated, Iterable, Tuple

from pydantic import BaseModel, Field


class BaseInputSample(BaseModel):
    """Base class for input samples to metrics."""

    id: Annotated[
        str,
        Field(
            description="Unique sample identifier, shared between ground-truth and predictions"
        ),
    ]


class BaseSampleResult(BaseModel):
    """Output of a single sample evaluation."""

    id: Annotated[
        str, Field(description="Sample identifier from the evaluated input pair")
    ]


class BaseAggregateResult(BaseModel):
    """Output of aggregating multiple sample results."""

    sample_count: Annotated[
        int, Field(description="Number of samples that contributed to this result")
    ]


class BaseMetric(ABC):
    """Abstract base class defining the interface for all metrics."""

    @abstractmethod
    def evaluate_sample(
        self, sample_a: BaseInputSample, sample_b: BaseInputSample
    ) -> BaseSampleResult:
        """Evaluate a single sample pair."""
        ...

    @abstractmethod
    def aggregate(self, results: Iterable[BaseSampleResult]) -> BaseAggregateResult:
        """Aggregate multiple sample results."""
        ...

    @abstractmethod
    def evaluate_dataset(
        self, sample_pairs: Iterable[Tuple[BaseInputSample, BaseInputSample]]
    ) -> BaseAggregateResult:
        """Evaluate an entire dataset."""
        ...

from enum import Enum
from typing import Iterable, Optional

from docling_metrics_core.base_types import (
    BaseAggregateResult,
    BaseInputSample,
    BaseSampleResult,
)


class LayoutMetricsMode(str, Enum):
    PYTHON = "Python"
    CPP = "C++"


class LayoutMetricSample(BaseInputSample):
    pass


class LayoutMetricSampleEvaluation(BaseSampleResult):
    pass


class LayoutMetricDatasetEvaluation(BaseAggregateResult):
    pass


class LayoutMetrics:
    r"""
    Various text metrics
    """

    def __init__(self, mode: LayoutMetricsMode = LayoutMetricsMode.PYTHON) -> None:
        r""" """
        self._mode = mode

    def evaluate_sample(
        self, sample: LayoutMetricSample
    ) -> LayoutMetricSampleEvaluation:
        r""" """
        sample_evaluation = LayoutMetricSampleEvaluation()
        return sample_evaluation

    def aggregate(
        self, results: Iterable[LayoutMetricSampleEvaluation]
    ) -> Optional[LayoutMetricDatasetEvaluation]:
        r"""
        Aggregate multiple sample results
        """
        return None

    def evaluate_dataset(
        self, sample_pairs: Iterable[LayoutMetricSample]
    ) -> LayoutMetricDatasetEvaluation:
        r"""
        Evaluate a dataset.
        """
        result = LayoutMetricDatasetEvaluation()
        return result

from typing import Annotated, Iterable, Tuple, Optional
from unittest import result

from docling_metrics_core.base_types import (
    BaseAggregateResult,
    BaseInputSample,
    BaseMetric,
    BaseSampleResult,
)

import docling_metric_teds_cpp
TEDSManager = docling_metric_teds_cpp.TEDSManager
TEDSSampleEvaluation = docling_metric_teds_cpp.TEDSampleEvaluation


class TEDSMetricInputSample(BaseInputSample):
    gt_bracket: str
    pred_bracket: str


class TEDSMetricSampleEvaluation(BaseSampleResult):
    gt_tree_size: int
    pred_tree_size: int
    teds: float


class TEDSMetricDatasetEvaluation(BaseAggregateResult):
    error_id: int
    error_msg: str
    gt_tree_size: str
    pred_tree_size: str


class TEDSMetric(BaseMetric):
    r"""
    Expose the C++ TEDS metric as a Python module.
    """
    def __init__(self) -> None:
        r"""
        """
        self._teds_manager = TEDSManager()

    def evaluate_sample(self, sample: TEDSMetricInputSample) -> TEDSMetricSampleEvaluation:
        r"""
        Evaluate a single sample.
        """
        sample_evaluaton: TEDSSampleEvaluation = self._teds_manager.evaluate_sample(
            sample.id,
            sample.gt_bracket,
            sample.pred_bracket,
        )
        if sample_evaluaton.error_id != 0:
            raise ValueError(sample_evaluaton.error_msg)
        
        result = TEDSMetricSampleEvaluation(
            id=sample.id,
            gt_tree_size=sample_evaluaton.gt_tree_size,
            pred_tree_size=sample_evaluaton.pred_tree_size,
            teds=sample_evaluaton.teds,
        )
        return result

    def aggregate(self, results: Iterable[TEDSMetricSampleEvaluation]) -> Optional[TEDSMetricDatasetEvaluation]:
        r"""
        Aggregate multiple sample results
        """
        pass

    def evaluate_dataset(
        self, sample_pairs: Iterable[Tuple[BaseInputSample, BaseInputSample]]
    ) -> TEDSMetricDatasetEvaluation:
        r"""
        Evaluate a dataset.
        """
        # TODO
        result = TEDSMetricDatasetEvaluation()
        return result

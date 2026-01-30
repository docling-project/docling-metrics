from typing import Any, Iterable, Optional, Tuple

import docling_metric_teds_cpp  # type: ignore[import-not-found]
from docling_metrics_core.base_types import (
    BaseAggregateResult,
    BaseInputSample,
    BaseMetric,
    BaseSampleResult,
)

TEDSManager = docling_metric_teds_cpp.TEDSManager
TEDSSampleEvaluation: Any = docling_metric_teds_cpp.TEDSSampleEvaluation
TEDSDatasetEvaluation: Any = docling_metric_teds_cpp.TEDSDatasetEvaluation


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
        r""" """
        self._teds_manager = TEDSManager()

    def evaluate_sample(  # type: ignore[override]
        self, sample: TEDSMetricInputSample
    ) -> TEDSMetricSampleEvaluation:
        r"""
        Evaluate a single sample.
        """
        sample_evaluaton: Any = self._teds_manager.evaluate_sample(
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

    def aggregate(  # type: ignore[override]
        self, results: Iterable[TEDSMetricSampleEvaluation]
    ) -> Optional[TEDSMetricDatasetEvaluation]:
        r"""
        Aggregate multiple sample results
        """
        return None

    def evaluate_dataset(
        self, sample_pairs: Iterable[Tuple[BaseInputSample, BaseInputSample]]
    ) -> TEDSMetricDatasetEvaluation:
        r"""
        Evaluate a dataset.
        """
        # TODO: Implement proper dataset evaluation
        result = TEDSMetricDatasetEvaluation(
            sample_count=0,
            error_id=0,
            error_msg="",
            gt_tree_size="",
            pred_tree_size="",
        )
        return result

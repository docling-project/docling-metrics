import logging
from enum import Enum
from pathlib import Path
from typing import Iterable, Optional

from docling_metrics_core.base_types import (
    BaseMetric,
)

from docling_metrics_layout.layout_types import (
    DatasetToreLayoutEvaluation,
    LayoutMetricDatasetEvaluation,
    LayoutMetricSample,
    LayoutMetricSampleEvaluation,
    MAPDatasetLayoutEvaluation,
    MAPPageLayoutEvaluation,
    PageToreEvaluation,
)
from docling_metrics_layout.map.map_layout_evaluator import (
    MAPLayoutEvaluator,
)
from docling_metrics_layout.tore.tore_layout_evaluator import (
    ToreLayoutEvaluator,
)

_log = logging.getLogger(__name__)

# Silence the coco tools
logging.getLogger("faster_coco_eval").setLevel(logging.WARNING)


class LayoutMetricsMode(str, Enum):
    PYTHON = "Python"
    CPP = "C++"


class LayoutMetrics(BaseMetric):
    r"""
    Various text metrics
    """

    def __init__(
        self,
        category_id_to_name: dict[int, str],
        concurrency: int = 4,
        save_root: Optional[Path] = None,
        mode: LayoutMetricsMode = LayoutMetricsMode.PYTHON,
    ):
        r"""
        Initialize the LayoutMetrics evaluator.

        Parameters:
            category_id_to_name: Mapping of category IDs to their string names.
            concurrency: Number of concurrent workers for parallel evaluation (default: 4).
            save_root: Optional root directory path for saving evaluation results.
                       If None, results will not be saved to disk.
            mode: Execution mode for layout evaluation, either PYTHON or C++ (default: PYTHON).
        """
        self._save_root = save_root
        self._category_id_to_name = category_id_to_name
        self._mode = mode

        # Evaluators
        self._tore_evaluator = ToreLayoutEvaluator(category_id_to_name, concurrency)
        self._map_evaluator = MAPLayoutEvaluator(category_id_to_name)

    def evaluate_sample(
        self, sample: LayoutMetricSample
    ) -> LayoutMetricSampleEvaluation:
        r"""Evaluate a single sample with TORE and mAP metrics"""
        # Evaluate TORE metric
        page_tore_evaluation = self._evaluate_tore_sample(sample)

        # Evaluate mAP metric
        page_map_layout_evaluation = self._evaluate_map_sample(sample)

        sample_evaluation = LayoutMetricSampleEvaluation(
            id=sample.id,
            page_tore_evaluation=page_tore_evaluation,
            page_map_layout_evaluation=page_map_layout_evaluation,
        )
        return sample_evaluation

    def aggregate(
        self, results: Iterable[LayoutMetricSampleEvaluation]
    ) -> Optional[LayoutMetricDatasetEvaluation]:
        r""" """
        return None

    def evaluate_dataset(
        self, samples: Iterable[LayoutMetricSample]
    ) -> LayoutMetricDatasetEvaluation:
        r"""Evaluate a dataset with TORE and mAP metrics"""
        sample_list = list(samples)

        # Evaluate mAP metrics
        ds_map_layout_evaluation = self._evaluate_map_dataset(sample_list)

        # Evaluate TORE metrics
        ds_tore_evaluation = self._evaluate_tore_dataset(sample_list)

        # Save export
        reports: list[Path] = []
        if self._save_root:
            _log.info("Exporting TORE evalution in %s", str(self._save_root))
            self._tore_evaluator.export_evaluations(ds_tore_evaluation, self._save_root)
            reports.append(
                ToreLayoutEvaluator.evaluation_filenames(self._save_root)["excel"]
            )

        # Build return object
        result = LayoutMetricDatasetEvaluation(
            sample_count=len(sample_list),
            dataset_tore_evaluation=ds_tore_evaluation,
            dataset_map_layout_evaluation=ds_map_layout_evaluation,
            reports=reports,
        )

        return result

    def _evaluate_tore_sample(self, sample: LayoutMetricSample) -> PageToreEvaluation:
        r"""Evaluate TORE metrics for a single sample"""
        _log.info("Evaluate TORE metrics for a single sample")
        return self._tore_evaluator.evaluate_sample(sample)

    def _evaluate_map_sample(
        self, sample: LayoutMetricSample
    ) -> MAPPageLayoutEvaluation:
        r"""Evaluate mAP metrics for a single sample"""
        _log.info("Evaluate mAP layout metrics for a single sample")
        return self._map_evaluator.evaluate_sample(sample)

    def _evaluate_tore_dataset(
        self, samples: list[LayoutMetricSample]
    ) -> DatasetToreLayoutEvaluation:
        r"""Evaluate TORE for a dataset"""
        _log.info("Evaluate TORE metrics for a dataset")
        return self._tore_evaluator.evaluate_dataset(samples)

    def _evaluate_map_dataset(
        self, samples: list[LayoutMetricSample]
    ) -> MAPDatasetLayoutEvaluation:
        r"""Evaluate mAP metrics for a dataset"""
        _log.info("Evaluate mAP layout metrics for a dataset")
        return self._map_evaluator.evaluate_dataset(samples)

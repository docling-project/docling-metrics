import logging
from enum import Enum
from pathlib import Path
from typing import Iterable, Optional

from docling_metrics_core.base_types import (
    BaseMetric,
)

from docling_metrics_layout.layout_types import (
    DatasetPixelLayoutEvaluation,
    LayoutMetricDatasetEvaluation,
    LayoutMetricSample,
    LayoutMetricSampleEvaluation,
    MAPDatasetLayoutEvaluation,
    MAPPageLayoutEvaluation,
    PagePixelLayoutEvaluation,
)
from docling_metrics_layout.map.map_layout_evaluator import (
    MAPLayoutEvaluator,
)
from docling_metrics_layout.pixel.pixel_layout_evaluator import (
    PixelLayoutEvaluator,
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
        self._pixel_evaluator = PixelLayoutEvaluator(category_id_to_name, concurrency)
        self._map_evaluator = MAPLayoutEvaluator(category_id_to_name)

    def evaluate_sample(
        self, sample: LayoutMetricSample
    ) -> LayoutMetricSampleEvaluation:
        r"""Evaluate a single sample with pixel-level and mAP metrics"""
        # Evaluate pixel-level metrics
        page_pixel_layout_evaluation = self._evaluate_pixel_sample(sample)

        # Evaluate mAP metrics
        page_map_layout_evaluation = self._evaluate_map_sample(sample)

        sample_evaluation = LayoutMetricSampleEvaluation(
            id=sample.id,
            page_pixel_layout_evaluation=page_pixel_layout_evaluation,
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
        r"""Evaluate a dataset with pixel-level and mAP metrics"""
        sample_list = list(samples)

        # Evaluate mAP metrics
        ds_map_layout_evaluation = self._evaluate_map_dataset(sample_list)

        # Evaluate pixel-level metrics
        ds_pixel_layout_evaluation = self._evaluate_pixel_dataset(sample_list)

        # Save export
        reports: list[Path] = []
        if self._save_root:
            _log.info(
                "Exporting pixel-wise layout evalution in %s", str(self._save_root)
            )
            self._pixel_evaluator.export_evaluations(
                ds_pixel_layout_evaluation, self._save_root
            )
            reports.append(
                PixelLayoutEvaluator.evaluation_filenames(self._save_root)["excel"]
            )

        # Build return object
        result = LayoutMetricDatasetEvaluation(
            sample_count=len(sample_list),
            dataset_pixel_layout_evaluation=ds_pixel_layout_evaluation,
            dataset_map_layout_evaluation=ds_map_layout_evaluation,
            reports=reports,
        )

        return result

    def _evaluate_pixel_sample(
        self, sample: LayoutMetricSample
    ) -> PagePixelLayoutEvaluation:
        r"""Evaluate pixel-level metrics for a single sample"""
        _log.info("Evaluate pixel-level layout metrics for a single sample")
        return self._pixel_evaluator.evaluate_sample(sample)

    def _evaluate_map_sample(
        self, sample: LayoutMetricSample
    ) -> MAPPageLayoutEvaluation:
        r"""Evaluate mAP metrics for a single sample"""
        _log.info("Evaluate mAP layout metrics for a single sample")
        return self._map_evaluator.evaluate_sample(sample)

    def _evaluate_pixel_dataset(
        self, samples: list[LayoutMetricSample]
    ) -> DatasetPixelLayoutEvaluation:
        r"""Evaluate pixel-level metrics for a dataset"""
        _log.info("Evaluate pixel-level layout metrics for a dataset")
        return self._pixel_evaluator.evaluate_dataset(samples)

    def _evaluate_map_dataset(
        self, samples: list[LayoutMetricSample]
    ) -> MAPDatasetLayoutEvaluation:
        r"""Evaluate mAP metrics for a dataset"""
        _log.info("Evaluate mAP layout metrics for a dataset")
        return self._map_evaluator.evaluate_dataset(samples)

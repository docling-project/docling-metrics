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
    PagePixelLayoutEvaluation,
)
from docling_metrics_layout.pixel.pixel_layout_evaluator import (
    PixelLayoutEvaluator,
)


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

    def evaluate_sample(
        self, sample: LayoutMetricSample
    ) -> LayoutMetricSampleEvaluation:
        r""" """
        page_pixel_layout_evaluation: PagePixelLayoutEvaluation = (
            self._pixel_evaluator.evaluate_sample(sample)
        )

        sample_evaluation = LayoutMetricSampleEvaluation(
            id=sample.id,
            page_pixel_layout_evaluation=page_pixel_layout_evaluation,
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
        r"""
        Evaluate a dataset
        """
        sample_list = list(samples)
        ds_pixel_layout_evaluation: DatasetPixelLayoutEvaluation = (
            self._pixel_evaluator.evaluate_dataset(sample_list)
        )

        # Save export
        if self._save_root:
            self._pixel_evaluator.export_evaluations(
                ds_pixel_layout_evaluation, self._save_root
            )

        # Build return object
        result = LayoutMetricDatasetEvaluation(
            sample_count=len(sample_list),
            dataset_pixel_layout_evaluation=ds_pixel_layout_evaluation,
        )

        return result

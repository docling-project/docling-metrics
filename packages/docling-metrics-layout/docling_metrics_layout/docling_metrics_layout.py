from enum import Enum
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
        mode: LayoutMetricsMode = LayoutMetricsMode.PYTHON,
    ):
        r"""
        Parameters:
        Mappings of category_id to category_name
        """
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
            page_pixel_layout_evaluation=page_pixel_layout_evaluation,
        )
        return sample_evaluation

    def aggregate(
        self, results: Iterable[LayoutMetricSampleEvaluation]
    ) -> Optional[LayoutMetricDatasetEvaluation]:
        r"""
        Aggregate multiple sample results
        """
        return None

    def evaluate_dataset(
        self, samples: Iterable[LayoutMetricSample]
    ) -> LayoutMetricDatasetEvaluation:
        r"""
        Evaluate a dataset.
        """
        ds_pixel_layout_evaluation: DatasetPixelLayoutEvaluation = (
            self._pixel_evaluator.evaluate_dataset(samples)
        )
        result = LayoutMetricDatasetEvaluation(
            dataset_pixel_layout_evaluation=ds_pixel_layout_evaluation,
        )
        return result

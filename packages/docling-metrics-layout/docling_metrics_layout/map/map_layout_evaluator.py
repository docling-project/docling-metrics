import logging
from typing import Iterable

import torch
from docling_metrics_layout.layout_types import (
    LayoutMetricSample,
    MAPDatasetLayoutEvaluation,
    MAPMetrics,
    MAPPageLayoutEvaluation,
)
from docling_metrics_layout.utils.stats import compute_stats
from docling_metrics_layout.utils.utils import tensor_to_float
from torch import Tensor
from torchmetrics.detection.mean_ap import MeanAveragePrecision

_log = logging.getLogger(__name__)


class MAPLayoutEvaluator:
    def __init__(
        self,
        category_id_to_name: dict[int, str],
    ):
        r""" """
        self._category_id_to_name = category_id_to_name

        # Compress the category_ids to have them "without holes" for torchmetrics
        # Create mapping from original category_id to compressed index (0, 1, 2, ...)
        sorted_category_ids = sorted(category_id_to_name.keys())
        self._category_id_to_compressed: dict[int, int] = {
            orig_id: compressed_idx
            for compressed_idx, orig_id in enumerate(sorted_category_ids)
        }
        # Reverse mapping for extracting per-class metrics
        self._compressed_to_category_id: dict[int, int] = {
            compressed_idx: orig_id
            for orig_id, compressed_idx in self._category_id_to_compressed.items()
        }

    def evaluate_sample(
        self,
        sample: LayoutMetricSample,
    ) -> MAPPageLayoutEvaluation:
        r"""
        Evaluation of a single page
        """
        # Extract the targets, predictions from the samples
        targets = []
        predictions = []
        self._extract_from_sample(sample, targets, predictions)

        # Compute mAP
        map_processor = self._get_map_processor()
        map_processor.update(preds=predictions, target=targets)
        map_result = map_processor.compute()

        # Prepare return object with all metrics
        result = MAPPageLayoutEvaluation(
            id=sample.id, **self._export_as_map_metrics(map_result).__dict__
        )
        return result

    def evaluate_dataset(
        self, samples: Iterable[LayoutMetricSample]
    ) -> MAPDatasetLayoutEvaluation:
        r"""Evaluate dataset and compute mAP metrics for all pages"""
        ds_targets = []
        ds_predictions = []
        page_evaluations: dict[str, MAPPageLayoutEvaluation] = {}

        map_values: list[float] = []
        map_50_values: list[float] = []
        map_75_values: list[float] = []

        for sample in samples:
            # Extract targets and predictions for this page
            page_targets = []
            page_predictions = []
            self._extract_from_sample(sample, page_targets, page_predictions)

            # Accumulate for dataset-level metrics
            ds_targets.extend(page_targets)
            ds_predictions.extend(page_predictions)

            # Compute page-level metrics
            map_processor = self._get_map_processor()
            map_processor.update(preds=page_predictions, target=page_targets)
            page_map_result = map_processor.compute()

            page_map_metrics = self._export_as_map_metrics(page_map_result)
            page_evaluation = MAPPageLayoutEvaluation(
                id=sample.id, **page_map_metrics.__dict__
            )
            page_evaluations[sample.id] = page_evaluation

            map_values.append(page_map_metrics.map)
            map_50_values.append(page_map_metrics.map_50)
            map_75_values.append(page_map_metrics.map_75)

        # Compute dataset-level metrics
        map_processor = self._get_map_processor()
        map_processor.update(preds=ds_predictions, target=ds_targets)
        map_result = map_processor.compute()

        ds_evaluation = MAPDatasetLayoutEvaluation(
            page_evaluations=page_evaluations,
            **self._export_as_map_metrics(map_result).__dict__,
            map_stats=compute_stats(map_values),
            map_50_stats=compute_stats(map_50_values),
            map_75_stats=compute_stats(map_75_values),
        )
        return ds_evaluation

    def _extract_from_sample(
        self,
        sample: LayoutMetricSample,
        targets: list,
        predictions: list,
    ):
        r"""
        Extract layout data from the sample and populate the targets/predictions
        """
        # Target - use compressed category IDs
        target_boxes = torch.tensor(
            [bbox.bbox for bbox in sample.page_resolution_a], dtype=torch.float32
        )
        target_labels = torch.tensor(
            [
                self._category_id_to_compressed[bbox.category_id]
                for bbox in sample.page_resolution_a
            ],
            dtype=torch.int64,
        )
        targets.append(
            {
                "boxes": target_boxes,
                "labels": target_labels,
            }
        )

        # Predictions with confidence scores - use compressed category IDs
        pred_boxes = torch.tensor(
            [bbox.bbox for bbox in sample.page_resolution_b], dtype=torch.float32
        )
        pred_labels = torch.tensor(
            [
                self._category_id_to_compressed[bbox.category_id]
                for bbox in sample.page_resolution_b
            ],
            dtype=torch.int64,
        )
        pred_scores = torch.tensor(
            [
                bbox.score if bbox.score is not None else 1.0
                for bbox in sample.page_resolution_b
            ],
            dtype=torch.float32,
        )
        predictions.append(
            {
                "boxes": pred_boxes,
                "scores": pred_scores,
                "labels": pred_labels,
            }
        )

    def _export_as_map_metrics(self, map_result: dict) -> MAPMetrics:
        r"""Convert the map_result to MAPMetrics"""
        # Extract scalar metrics
        map_metrics = MAPMetrics(
            map=tensor_to_float(map_result.get("map", -1.0)),
            map_50=tensor_to_float(map_result.get("map_50", -1.0)),
            map_75=tensor_to_float(map_result.get("map_75", -1.0)),
            map_large=tensor_to_float(map_result.get("map_large", -1.0)),
            map_medium=tensor_to_float(map_result.get("map_medium", -1.0)),
            map_small=tensor_to_float(map_result.get("map_small", -1.0)),
            mar_1=tensor_to_float(map_result.get("mar_1", -1.0)),
            mar_10=tensor_to_float(map_result.get("mar_10", -1.0)),
            mar_100=tensor_to_float(map_result.get("mar_100", -1.0)),
            mar_large=tensor_to_float(map_result.get("mar_large", -1.0)),
            mar_medium=tensor_to_float(map_result.get("mar_medium", -1.0)),
            mar_small=tensor_to_float(map_result.get("mar_small", -1.0)),
            # Extract per-class metrics
            map_per_class=self._extract_metrics_per_class(
                map_result.get("classes", None), map_result.get("map_per_class", None)
            ),
            mar_100_per_class=self._extract_metrics_per_class(
                map_result.get("classes", None),
                map_result.get("mar_100_per_class", None),
            ),
        )
        return map_metrics

    def _extract_metrics_per_class(
        self, classes_tensor: Tensor, per_class_tensor: Tensor
    ) -> dict[str, float]:
        r"""
        Extract per-class metrics from tensor and map to class names
        """
        if per_class_tensor is None:
            return {}

        evaluated_classes: list[int] = classes_tensor.tolist()
        map_classes = (
            [per_class_tensor.tolist()]
            if per_class_tensor.numel() == 1
            else per_class_tensor.tolist()
        )
        per_class_dict: dict[str, float] = {}
        for idx, category_map in enumerate(map_classes):
            category_id = evaluated_classes[idx]
            category_name = self._category_id_to_name[category_id]
            per_class_dict[category_name] = category_map
        return per_class_dict

    def _get_map_processor(self) -> MeanAveragePrecision:
        r"""Factory of  MeanAveragePrecision"""
        return MeanAveragePrecision(
            box_format="xyxy",
            iou_type="bbox",
            class_metrics=True,
            backend="faster_coco_eval",
        )

import json
import logging
from pathlib import Path

from docling_metrics_layout.layout_types import BboxResolution, LayoutMetricSample
from docling_metrics_layout.utils.utils import xywh_to_xyxy

_log = logging.getLogger(__name__)


def load_layout_samples(
    gt_coco_fn: Path,
    preds_coco_fn: Path,
) -> tuple[dict[int, str], list[LayoutMetricSample]]:
    r"""
    Load LayoutMetricSample objects from COCO GT and predictions files.

    Parameters:
        gt_coco_fn: Path to COCO ground-truth annotations JSON file.
        preds_coco_fn: Path to COCO predictions JSON file.

    Returns:
        Tuple of (category_id_to_name mapping, list of LayoutMetricSample).
    """
    with open(gt_coco_fn) as f:
        gt_coco = json.load(f)

    with open(preds_coco_fn) as f:
        predictions = json.load(f)

    # Build category mapping
    category_id_to_name: dict[int, str] = {
        cat["id"]: cat["name"] for cat in gt_coco["categories"]
    }

    # Build image info mapping: image_id -> image dict (includes width, height)
    image_info: dict[int, dict] = {img["id"]: img for img in gt_coco["images"]}

    # Build GT bboxes per image: image_id -> list[BboxResolution]
    gt_per_image: dict[int, list[BboxResolution]] = {}
    for ann in gt_coco["annotations"]:
        image_id = ann["image_id"]
        gt_per_image.setdefault(image_id, []).append(
            BboxResolution(
                category_id=ann["category_id"],
                bbox=xywh_to_xyxy(ann["bbox"]),
            )
        )

    # Build prediction bboxes per image: image_id -> list[BboxResolution]
    preds_per_image: dict[int, list[BboxResolution]] = {}
    for pred in predictions:
        image_id = pred["image_id"]
        preds_per_image.setdefault(image_id, []).append(
            BboxResolution(
                category_id=pred["category_id"],
                bbox=xywh_to_xyxy(pred["bbox"]),
                score=pred.get("score"),
            )
        )

    # Build one LayoutMetricSample per image that has predictions
    samples: list[LayoutMetricSample] = []
    for image_id, img in image_info.items():
        gt_bboxes = gt_per_image.get(image_id, [])
        pred_bboxes = preds_per_image.get(image_id)
        if pred_bboxes is None:
            _log.warning("Missing predictions for image_id: %s", image_id)
            continue
        sample = LayoutMetricSample(
            id=str(image_id),
            page_width=img["width"],
            page_height=img["height"],
            page_resolution_a=gt_bboxes,
            page_resolution_b=pred_bboxes,
        )
        samples.append(sample)

    _log.info("Loaded %d samples", len(samples))
    return category_id_to_name, samples

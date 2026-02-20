import logging
from pathlib import Path

from docling_metrics_layout import (
    LayoutMetrics,
    LayoutMetricSample,
)
from docling_metrics_layout.layout_types import LayoutMetricDatasetEvaluation

# Data
DATA = {
    "id": "page_001",
    "page_width": 612,
    "page_height": 792,
    "page_resolution_a": [
        {"category_id": 1, "bbox": [50.0, 80.0, 300.0, 200.0], "score": 0.97},
        {"category_id": 2, "bbox": [310.0, 80.0, 560.0, 200.0], "score": 0.91},
        {"category_id": 1, "bbox": [50.0, 220.0, 560.0, 380.0], "score": 0.88},
        {"category_id": 3, "bbox": [50.0, 400.0, 300.0, 500.0], "score": 0.76},
    ],
    "page_resolution_b": [
        {"category_id": 1, "bbox": [52.0, 82.0, 298.0, 202.0], "score": 0.95},
        {"category_id": 2, "bbox": [312.0, 78.0, 558.0, 199.0], "score": 0.89},
        {"category_id": 1, "bbox": [48.0, 218.0, 562.0, 382.0], "score": 0.85},
    ],
}

CATEGORIES = {1: "red", 2: "orange", 3: "green", 4: "blue"}

REPORT_DIR = "reports/"


def setup_logging():
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_format)


def demo():
    # Load the data as list[LayoutMetricSample]
    samples = [LayoutMetricSample.model_validate(DATA)]

    # Evaluate
    lm = LayoutMetrics(CATEGORIES, save_root=Path(REPORT_DIR))
    evaluation: LayoutMetricDatasetEvaluation = lm.evaluate_dataset(samples)

    # mAP metrics
    map_eval = evaluation.dataset_map_layout_evaluation
    print(f"\nmAP:           {map_eval.map:.4f}")
    print(f"mAP per class: {map_eval.map_per_class}")

    # Pixel metrics — detailed MultiLabelMatrixMetrics
    detailed = evaluation.dataset_pixel_layout_evaluation.matrix_evaluation.detailed
    print(f"\nPrecision matrix:\n{detailed.precision_matrix}")
    print(f"\nRecall matrix:\n{detailed.recall_matrix}")

    # Report files
    print("\nReport files:")
    for f in evaluation.reports:
        print(f"  {f.name}")


if __name__ == "__main__":
    setup_logging()
    demo()

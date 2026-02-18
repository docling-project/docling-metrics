import json
import tempfile
from pathlib import Path

from docling_metrics_layout.layout_types import (
    BboxResolution,
    LayoutMetricSample,
    PagePixelLayoutEvaluation,
    DatasetPixelLayoutEvaluation,
    MultiLabelMatrixEvaluation,
)
from docling_metrics_layout.pixel.pixel_layout_evaluator import (
    PixelLayoutEvaluator,
)

# Get the directory of this test file
TEST_DATA_DIR = Path(__file__).parent / "data"

# Tolerance for floating-point comparisons
FLOATING_POINT_TOLERANCE = 1e-6


def test_pixel_layout_evaluator():
    r"""Test LayoutMetrics evaluation on sample and dataset level."""
    # Load test data
    test_data_path = TEST_DATA_DIR / "dlnv1_t1_preds.json"
    with open(test_data_path) as f:
        test_data = json.load(f)

    # Create category mapping (using all unique category IDs found in test data)
    category_ids = set()
    for bbox in test_data["page_resolution_a"] + test_data["page_resolution_b"]:
        category_ids.add(bbox["category_id"])
    category_id_to_name = {cid: f"category_{cid}" for cid in sorted(category_ids)}

    # Create LayoutMetricSample from test data
    sample = LayoutMetricSample(
        id=test_data["id"],
        page_width=test_data["page_width"],
        page_height=test_data["page_height"],
        page_resolution_a=[
            BboxResolution(
                category_id=bbox["category_id"],
                bbox=bbox["bbox"],
            )
            for bbox in test_data["page_resolution_a"]
        ],
        page_resolution_b=[
            BboxResolution(
                category_id=bbox["category_id"],
                bbox=bbox["bbox"],
            )
            for bbox in test_data["page_resolution_b"]
        ],
    )

    # Test 1: Initialize LayoutMetrics and evaluate single sample
    evaluator = PixelLayoutEvaluator(
        category_id_to_name=category_id_to_name,
        concurrency=4,
    )

    sample_result = evaluator.evaluate_sample(sample)

    # Verify sample result structure
    assert isinstance(sample_result, PagePixelLayoutEvaluation), (
        "sample_result must be PagePixelLayoutEvaluation instance"
    )
    assert sample_result.id == test_data["id"], (
        f"sample_result.id should be {test_data['id']}, got {sample_result.id}"
    )
    assert sample_result.num_pixels > 0, (
        "num_pixels should be greater than 0"
    )
    assert (
        sample_result.num_pixels == test_data["page_width"] * test_data["page_height"]
    ), "num_pixels should equal page_width * page_height"
    assert isinstance(
        sample_result.matrix_evaluation,
        MultiLabelMatrixEvaluation,
    ), "matrix_evaluation should be MultiLabelMatrixEvaluation instance"

    # Verify detailed metrics
    detailed_metrics = sample_result.matrix_evaluation.detailed
    assert detailed_metrics.confusion_matrix.shape[0] == 6, (
        f"detailed confusion matrix should have 6 classes, got {detailed_metrics.confusion_matrix.shape[0]}"
    )
    assert detailed_metrics.confusion_matrix.shape == (6, 6), (
        f"detailed confusion matrix shape should be (6, 6), got {detailed_metrics.confusion_matrix.shape}"
    )
    assert detailed_metrics.precision_matrix.shape == (6, 6), (
        f"detailed precision matrix shape should be (6, 6), got {detailed_metrics.precision_matrix.shape}"
    )
    assert detailed_metrics.recall_matrix.shape == (6, 6), (
        f"detailed recall matrix shape should be (6, 6), got {detailed_metrics.recall_matrix.shape}"
    )
    assert detailed_metrics.f1_matrix.shape == (6, 6), (
        f"detailed f1 matrix shape should be (6, 6), got {detailed_metrics.f1_matrix.shape}"
    )

    # Verify expected classes in detailed metrics
    expected_classes = {
        "Background",
        "category_0",
        "category_4",
        "category_6",
        "category_7",
        "category_9",
    }
    actual_classes = set(detailed_metrics.class_names.values())
    assert actual_classes == expected_classes, (
        f"detailed classes should be {expected_classes}, got {actual_classes}"
    )

    # Verify detailed metrics aggregations
    assert (
        abs(detailed_metrics.agg_metrics.classes_precision_mean - 0.3333333333333333)
        < FLOATING_POINT_TOLERANCE
    ), (
        f"detailed precision mean should be ~0.333, got {detailed_metrics.agg_metrics.classes_precision_mean}"
    )
    assert (
        abs(detailed_metrics.agg_metrics.classes_recall_mean - 0.3333333333333333)
        < FLOATING_POINT_TOLERANCE
    ), (
        f"detailed recall mean should be ~0.333, got {detailed_metrics.agg_metrics.classes_recall_mean}"
    )
    assert (
        abs(detailed_metrics.agg_metrics.classes_f1_mean - 0.3333333333333333)
        < FLOATING_POINT_TOLERANCE
    ), (
        f"detailed f1 mean should be ~0.333, got {detailed_metrics.agg_metrics.classes_f1_mean}"
    )

    # Verify collapsed metrics
    collapsed_metrics = sample_result.matrix_evaluation.collapsed
    assert collapsed_metrics.confusion_matrix.shape == (2, 2), (
        f"collapsed confusion matrix shape should be (2, 2), got {collapsed_metrics.confusion_matrix.shape}"
    )
    assert collapsed_metrics.precision_matrix.shape == (2, 2), (
        f"collapsed precision matrix shape should be (2, 2), got {collapsed_metrics.precision_matrix.shape}"
    )
    assert collapsed_metrics.recall_matrix.shape == (2, 2), (
        f"collapsed recall matrix shape should be (2, 2), got {collapsed_metrics.recall_matrix.shape}"
    )
    assert collapsed_metrics.f1_matrix.shape == (2, 2), (
        f"collapsed f1 matrix shape should be (2, 2), got {collapsed_metrics.f1_matrix.shape}"
    )

    # Verify expected classes in collapsed metrics
    expected_collapsed_classes = {"Background", "all_classes"}
    actual_collapsed_classes = set(collapsed_metrics.class_names.values())
    assert actual_collapsed_classes == expected_collapsed_classes, (
        f"collapsed classes should be {expected_collapsed_classes}, got {actual_collapsed_classes}"
    )

    # Verify collapsed metrics aggregations (all 1.0 for perfect match)
    assert collapsed_metrics.agg_metrics.classes_precision_mean == 1.0, (
        f"collapsed precision mean should be 1.0, got {collapsed_metrics.agg_metrics.classes_precision_mean}"
    )
    assert collapsed_metrics.agg_metrics.classes_recall_mean == 1.0, (
        f"collapsed recall mean should be 1.0, got {collapsed_metrics.agg_metrics.classes_recall_mean}"
    )
    assert collapsed_metrics.agg_metrics.classes_f1_mean == 1.0, (
        f"collapsed f1 mean should be 1.0, got {collapsed_metrics.agg_metrics.classes_f1_mean}"
    )

    # Test 2: Evaluate dataset (single sample in this case)
    dataset_result = evaluator.evaluate_dataset([sample])

    # Verify dataset result structure
    assert isinstance(dataset_result, DatasetPixelLayoutEvaluation), (
        "dataset_result must be DatasetPixelLayoutEvaluation instance"
    )
    assert dataset_result.num_pages == 1, (
        f"num_pages should be 1, got {dataset_result.num_pages}"
    )
    assert dataset_result.num_pixels > 0, (
        "num_pixels should be greater than 0"
    )
    assert (
        dataset_result.num_pixels == test_data["page_width"] * test_data["page_height"]
    ), "num_pixels should equal page_width * page_height"
    assert (
        test_data["id"] in dataset_result.page_evaluations
    ), f"page_evaluations should contain {test_data['id']}"
    assert len(dataset_result.page_evaluations) == 1, (
        f"page_evaluations should have 1 entry, got {len(dataset_result.page_evaluations)}"
    )

    # Test 3: Evaluate dataset with save functionality
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_root = Path(tmp_dir)

        # Evaluate and export
        dataset_result_with_save = evaluator.evaluate_dataset([sample])
        evaluator.export_evaluations(dataset_result_with_save, tmp_root)

        # Verify dataset result is created
        assert isinstance(dataset_result_with_save, DatasetPixelLayoutEvaluation), (
            "dataset_result_with_save must be DatasetPixelLayoutEvaluation instance"
        )
        assert dataset_result_with_save.num_pages == 1, (
            f"num_pages should be 1, got {dataset_result_with_save.num_pages}"
        )

        # Get expected filenames from PixelLayoutEvaluator
        eval_filenames = PixelLayoutEvaluator.evaluation_filenames(tmp_root)

        # Verify that all expected files exist
        for file_type, file_path in eval_filenames.items():
            assert file_path.exists(), (
                f"Expected {file_type} file should exist at {file_path}"
            )
            assert file_path.is_file(), (
                f"{file_type} file at {file_path} should be a file, not a directory"
            )
            assert file_path.stat().st_size > 0, (
                f"{file_type} file at {file_path} should not be empty"
            )

        # Verify JSON file structure
        json_file = eval_filenames["json"]
        with open(json_file) as f:
            json_data = json.load(f)
        assert "num_pages" in json_data, "JSON should contain 'num_pages'"
        assert "num_pixels" in json_data, "JSON should contain 'num_pixels'"
        assert "page_evaluations" in json_data, "JSON should contain 'page_evaluations'"

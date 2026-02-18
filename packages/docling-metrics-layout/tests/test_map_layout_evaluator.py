import json
from pathlib import Path

from docling_metrics_layout.layout_types import (
    BboxResolution,
    LayoutMetricSample,
    MAPDatasetLayoutEvaluation,
    MAPPageLayoutEvaluation,
)
from docling_metrics_layout.map.map_layout_evaluator import (
    MAPLayoutEvaluator,
)

# Get the directory of this test file
TEST_DATA_DIR = Path(__file__).parent / "data"

# Tolerance for floating-point comparisons
FLOATING_POINT_TOLERANCE = 1e-6


def test_map_layout_evaluations():
    r"""Test MAPLayoutEvaluator evaluation on sample and dataset level with actual value assertions."""
    test_data_path = TEST_DATA_DIR / "dlnv1_t1_preds_score.json"

    # Load the test data with scores
    with open(test_data_path) as f:
        test_data = json.load(f)

    # Create category mapping (using all unique category IDs found in test data)
    category_ids = set()
    for bbox in test_data["page_resolution_a"] + test_data["page_resolution_b"]:
        category_ids.add(bbox["category_id"])
    category_id_to_name = {cid: f"category_{cid}" for cid in sorted(category_ids)}

    # Create LayoutMetricSample from test data with confidence scores
    sample = LayoutMetricSample(
        id=test_data["id"],
        page_width=test_data["page_width"],
        page_height=test_data["page_height"],
        page_resolution_a=[
            BboxResolution(
                category_id=bbox["category_id"],
                bbox=bbox["bbox"],
                score=bbox.get("score", 1.0),
            )
            for bbox in test_data["page_resolution_a"]
        ],
        page_resolution_b=[
            BboxResolution(
                category_id=bbox["category_id"],
                bbox=bbox["bbox"],
                score=bbox.get("score", 1.0),
            )
            for bbox in test_data["page_resolution_b"]
        ],
    )

    # Initialize MAPLayoutEvaluator
    evaluator = MAPLayoutEvaluator(
        category_id_to_name=category_id_to_name,
    )

    # Test 1: Evaluate single sample
    sample_result = evaluator.evaluate_sample(sample)

    # Verify sample result is correct type
    assert isinstance(sample_result, MAPPageLayoutEvaluation)
    assert sample_result.id == test_data["id"]

    # Verify primary map scores
    assert sample_result.map == 1.0, (
        f"map should be 1.0 (perfect match), got {sample_result.map}"
    )
    assert sample_result.map_50 == 1.0, (
        f"map_50 should be 1.0, got {sample_result.map_50}"
    )
    assert sample_result.map_75 == 1.0, (
        f"map_75 should be 1.0, got {sample_result.map_75}"
    )

    # Verify area-based map scores
    assert sample_result.map_small == 1.0, (
        f"map_small should be 1.0, got {sample_result.map_small}"
    )
    assert sample_result.map_medium == 1.0, (
        f"map_medium should be 1.0, got {sample_result.map_medium}"
    )
    assert sample_result.map_large == 1.0, (
        f"map_large should be 1.0, got {sample_result.map_large}"
    )

    # Verify recall scores
    assert abs(sample_result.mar_1 - 0.6) < 0.1, (
        f"mar_1 should be ~0.6, got {sample_result.mar_1}"
    )
    assert sample_result.mar_10 == 1.0, (
        f"mar_10 should be 1.0, got {sample_result.mar_10}"
    )
    assert sample_result.mar_100 == 1.0, (
        f"mar_100 should be 1.0, got {sample_result.mar_100}"
    )

    # Verify area-based recall scores
    assert sample_result.mar_small == 1.0, (
        f"mar_small should be 1.0, got {sample_result.mar_small}"
    )
    assert sample_result.mar_medium == 1.0, (
        f"mar_medium should be 1.0, got {sample_result.mar_medium}"
    )
    assert sample_result.mar_large == 1.0, (
        f"mar_large should be 1.0, got {sample_result.mar_large}"
    )

    # Verify per-class metrics
    expected_classes = {
        "category_0",
        "category_4",
        "category_6",
        "category_7",
        "category_9",
    }
    assert set(sample_result.map_per_class.keys()) == expected_classes, (
        f"map_per_class keys should be {expected_classes}, got {set(sample_result.map_per_class.keys())}"
    )
    assert all(v == 1.0 for v in sample_result.map_per_class.values()), (
        f"All per-class map values should be 1.0, got {sample_result.map_per_class}"
    )

    assert set(sample_result.mar_100_per_class.keys()) == expected_classes, (
        f"mar_100_per_class keys should be {expected_classes}, got {set(sample_result.mar_100_per_class.keys())}"
    )
    assert all(v == 1.0 for v in sample_result.mar_100_per_class.values()), (
        f"All per-class mar_100 values should be 1.0, got {sample_result.mar_100_per_class}"
    )

    # Test 2: Evaluate dataset
    dataset_result = evaluator.evaluate_dataset([sample])

    # Verify dataset result is correct type
    assert isinstance(dataset_result, MAPDatasetLayoutEvaluation)

    # Verify dataset-level map scores
    assert dataset_result.map == 1.0, (
        f"dataset map should be 1.0, got {dataset_result.map}"
    )
    assert dataset_result.map_50 == 1.0, (
        f"dataset map_50 should be 1.0, got {dataset_result.map_50}"
    )
    assert dataset_result.map_75 == 1.0, (
        f"dataset map_75 should be 1.0, got {dataset_result.map_75}"
    )

    # Verify page evaluations
    assert len(dataset_result.page_evaluations) == 1, (
        f"page_evaluations should have 1 entry, got {len(dataset_result.page_evaluations)}"
    )
    assert test_data["id"] in dataset_result.page_evaluations, (
        f"page_evaluations should contain {test_data['id']}"
    )

    # Verify page evaluation values match sample evaluation
    page_eval = dataset_result.page_evaluations[test_data["id"]]
    assert isinstance(page_eval, MAPPageLayoutEvaluation)
    assert page_eval.id == test_data["id"]
    assert page_eval.map == sample_result.map, (
        f"page_eval.map should match sample_result.map: {page_eval.map} vs {sample_result.map}"
    )
    assert page_eval.map_50 == sample_result.map_50, (
        f"page_eval.map_50 should match sample_result.map_50: {page_eval.map_50} vs {sample_result.map_50}"
    )


if __name__ == "__main__":
    test_map_layout_evaluations()

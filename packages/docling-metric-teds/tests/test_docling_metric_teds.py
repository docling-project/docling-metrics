import math
from pathlib import Path
from typing import Tuple

import pytest
from docling_metric_teds import (
    TEDSManager,
    TEDSSampleEvaluation,
)
from docling_metric_teds.docling_metric_teds import (
    TEDSMetric,
    TEDSMetricInputSample,
    TEDSMetricSampleEvaluation,
)


def load_test_data() -> Tuple[str, str, str]:
    """
    Load test bracket files.

    Returns:
        Tuple of (gt_bracket, pred_bracket, broken_bracket)
    """
    test_dir = Path(__file__).parent
    broken_bracket_fn = test_dir / "data/broken.bracket"
    gt_bracket_fn = test_dir / "data/GT_ZBRA.2018.page_89.pdf_172_0.bracket"
    pred_bracket_fn = test_dir / "data/pred_ZBRA.2018.page_89.pdf_172_0.bracket"

    with open(gt_bracket_fn, "r") as f:
        gt_bracket = f.read()
    with open(pred_bracket_fn, "r") as f:
        pred_bracket = f.read()
    with open(broken_bracket_fn, "r") as f:
        broken_bracket = f.read()

    return gt_bracket, pred_bracket, broken_bracket


def test_cpp_bindings():
    r"""
    Test the low-level C++ bindings via TEDSManager.
    """
    # Load test data
    gt_bracket, pred_bracket, broken_bracket = load_test_data()

    # Initialize TEDSManager
    teds_manager = TEDSManager()

    # Evaluate sample
    id = "s1"
    sample_evaluation: TEDSSampleEvaluation = teds_manager.evaluate_sample(
        id, gt_bracket, pred_bracket
    )

    # Assertions
    assert sample_evaluation.error_id == 0, "Expected no error for valid brackets"
    assert math.isclose(sample_evaluation.teds, 0.970588, rel_tol=1e-6), (
        "Wrong TEDS score for valid bracket"
    )
    assert sample_evaluation.gt_tree_size > 0, "GT tree size should be positive"
    assert sample_evaluation.pred_tree_size > 0, "Pred tree size should be positive"

    # Print results
    print("\n=== Sample Evaluation Results ===")
    print(f"Sample ID: {sample_evaluation.id}")
    print(f"Error ID: {sample_evaluation.error_id}")
    print(f"Error Message: {sample_evaluation.error_msg}")
    print(f"GT Tree Size: {sample_evaluation.gt_tree_size}")
    print(f"Pred Tree Size: {sample_evaluation.pred_tree_size}")
    print(f"TEDS Score: {sample_evaluation.teds}")

    # Test with broken bracket
    print("\n=== Testing Broken Bracket ===")
    broken_eval: TEDSSampleEvaluation = teds_manager.evaluate_sample(
        "s2", broken_bracket, pred_bracket
    )
    print(f"Error ID: {broken_eval.error_id}")
    print(f"Error Message: {broken_eval.error_msg}")

    # Assertions
    assert broken_eval.error_id != 0, "Expected error for broken bracket"

    print("\n All tests passed!")


def test_teds_metric_api():
    r"""
    Test the high-level TEDSMetric API with valid and broken bracket notations.
    """
    # Load test data
    gt_bracket, pred_bracket, broken_bracket = load_test_data()

    # Initialize TEDSMetric
    teds_metric = TEDSMetric()

    # Evaluate sample using the high-level API
    sample = TEDSMetricInputSample(
        id="s1",
        gt_bracket=gt_bracket,
        pred_bracket=pred_bracket,
    )
    sample_evaluation: TEDSMetricSampleEvaluation = teds_metric.evaluate_sample(sample)

    # Print results
    print("\n=== Sample Evaluation Results ===")
    print(f"GT Tree Size: {sample_evaluation.gt_tree_size}")
    print(f"Pred Tree Size: {sample_evaluation.pred_tree_size}")
    print(f"TEDS Score: {sample_evaluation.teds}")

    # Test with broken bracket - should raise ValueError
    print("\n=== Testing Broken Bracket ===")
    broken_sample = TEDSMetricInputSample(
        id="s2",
        gt_bracket=broken_bracket,
        pred_bracket=pred_bracket,
    )

    with pytest.raises(ValueError) as exc_info:
        teds_metric.evaluate_sample(broken_sample)

    print(f"Expected error caught: {exc_info.value}")

    # Assertions
    assert math.isclose(sample_evaluation.teds, 0.970588, rel_tol=1e-6), (
        "Wrong TEDS score for valid bracket"
    )
    assert sample_evaluation.gt_tree_size > 0, "GT tree size should be positive"
    assert sample_evaluation.pred_tree_size > 0, "Pred tree size should be positive"

    print("\n All tests passed!")


if __name__ == "__main__":
    test_cpp_bindings()
    test_teds_metric_api()

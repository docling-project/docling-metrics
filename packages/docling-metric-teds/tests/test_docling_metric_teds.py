import math
from pathlib import Path

import pytest
from docling_metric_teds import docling_metric_teds_cpp
from docling_metric_teds.docling_metric_teds import (
    TEDSMetric,
    TEDSMetricBracketInputSample,
    TEDSMetricHTMLInputSample,
    TEDSMetricSampleEvaluation,
)

# Test configuration
TEDS_RELATIVE_TOLERANCE = 1e-6

# Test data configuration: stems and expected values
TEST_DATA: dict[str, dict[str, int | float]] = {
    "CHD.2018.page_21.pdf_147707_0": {
        "html_teds": 0.285714285714286,
        "html_structure_only_teds": 0.571428571428571,
        "bracket_teds": 0.285714285714286,
        "tree_a_size": 14,
        "tree_b_size": 12,
    },
    "WU.2016.page_106.pdf_68194_0": {
        "html_teds": 0.323529411764706,
        "html_structure_only_teds": 0.980392156862745,
        "bracket_teds": 0.323529411764706,
        "tree_a_size": 101,
        "tree_b_size": 102,
    },
}


def load_test_data() -> dict[str, dict[str, str]]:
    """
    Load test bracket and HTML files.

    Returns:
        Nested dictionary where:
        - First level key: stem (e.g., "ZBRA.2018.page_89.pdf_172_0")
        - Second level keys: ["gt_bracket", "gt_html", "pred_bracket", "pred_html", "broken_bracket"]
    """
    test_dir = Path(__file__).parent
    prefixes = ["GT_", "pred_"]
    extensions = [".html", ".bracket"]

    # Load test data files using triple for loop
    all_data: dict[str, dict[str, str]] = {}
    for stem in TEST_DATA.keys():
        stem_data = {}
        for prefix in prefixes:
            for ext in extensions:
                filename = f"{prefix}{stem}{ext}"
                filepath = test_dir / "data" / filename
                with open(filepath, "r") as f:
                    # Create key like 'gt_html', 'gt_bracket', 'pred_html', 'pred_bracket'
                    key = f"{prefix.rstrip('_').lower()}_{ext.lstrip('.')}"
                    stem_data[key] = f.read()

        # Load broken bracket file separately (shared across all stems)
        broken_bracket_fn = test_dir / "data/broken.bracket"
        with open(broken_bracket_fn, "r") as f:
            stem_data["broken_bracket"] = f.read()

        # Verify we have all expected keys for this stem
        expected_count = len(prefixes) * len(extensions) + 1
        assert len(stem_data) == expected_count, (
            f"Expected {expected_count} keys for stem '{stem}', but got {len(stem_data)}: {set(stem_data.keys())}"
        )

        all_data[stem] = stem_data

    return all_data


def test_cpp_bindings():
    r"""
    Test the low-level C++ bindings via TEDSManager.
    """
    # Load test data
    all_test_data: dict[str, dict[str, str]] = load_test_data()

    # Initialize TEDSManager
    teds_manager = docling_metric_teds_cpp.TEDSManager()

    # Loop over all stems
    for stem, test_data in all_test_data.items():
        # Get expected values for this stem from config
        config = TEST_DATA[stem]
        expected_bracket_teds = config["bracket_teds"]
        expected_tree_a_size = config["tree_a_size"]
        expected_tree_b_size = config["tree_b_size"]

        print(f"\n{'=' * 60}")
        print(f"Testing stem: {stem}")
        print(f"{'=' * 60}")

        # Evaluate sample
        id = f"s1_{stem}"
        sample_evaluation = teds_manager.evaluate_sample(
            id, test_data["gt_bracket"], test_data["pred_bracket"]
        )

        # Assertions
        assert sample_evaluation.error_id == 0, (
            f"Expected no error for valid brackets (stem: {stem})"
        )
        assert math.isclose(
            sample_evaluation.teds,
            expected_bracket_teds,
            rel_tol=TEDS_RELATIVE_TOLERANCE,
        ), (
            f"Wrong TEDS score for valid bracket (stem: {stem}). Expected {expected_bracket_teds}, got {sample_evaluation.teds}"
        )
        assert sample_evaluation.tree_a_size == expected_tree_a_size, (
            f"Wrong tree A size (stem: {stem}). Expected {expected_tree_a_size}, got {sample_evaluation.tree_a_size}"
        )
        assert sample_evaluation.tree_b_size == expected_tree_b_size, (
            f"Wrong tree B size (stem: {stem}). Expected {expected_tree_b_size}, got {sample_evaluation.tree_b_size}"
        )

        # Print results
        print("\n=== Sample Evaluation Results ===")
        print(f"Sample ID: {sample_evaluation.id}")
        print(f"Error ID: {sample_evaluation.error_id}")
        print(f"Error message: {sample_evaluation.error_msg}")
        print(f"Tree A size: {sample_evaluation.tree_a_size}")
        print(f"Tree B size: {sample_evaluation.tree_b_size}")
        print(f"TEDS Score: {sample_evaluation.teds}")

        # Test with broken bracket
        print("\n=== Testing Broken Bracket ===")
        broken_eval = teds_manager.evaluate_sample(
            f"s2_{stem}", test_data["broken_bracket"], test_data["pred_bracket"]
        )
        print(f"Error ID: {broken_eval.error_id}")
        print(f"Error Message: {broken_eval.error_msg}")

        # Assertions
        assert broken_eval.error_id != 0, (
            f"Expected error for broken bracket (stem: {stem})"
        )

    print("\n All tests passed!")


def test_teds_metric_api():
    r"""
    Test the high-level TEDSMetric API with valid and broken bracket notations and HTML inputs.
    """
    # Load test data
    all_test_data: dict[str, dict[str, str]] = load_test_data()

    # Initialize TEDSMetric
    teds_metric = TEDSMetric()

    # Loop over all stems
    for stem, test_data in all_test_data.items():
        # Get expected values for this stem from config
        config = TEST_DATA[stem]
        expected_bracket_teds = config["bracket_teds"]
        expected_html_teds = config["html_teds"]
        expected_html_structure_only_teds = config["html_structure_only_teds"]
        expected_tree_a_size = config["tree_a_size"]
        expected_tree_b_size = config["tree_b_size"]

        print(f"\n{'=' * 60}")
        print(f"Testing stem: {stem}")
        print(f"{'=' * 60}")

        # Test 1: Evaluate sample using bracket notation
        print("\n=== Test 1: Bracket Notation ===")
        sample_bracket = TEDSMetricBracketInputSample(
            id=f"s1_{stem}",
            bracket_a=test_data["gt_bracket"],
            bracket_b=test_data["pred_bracket"],
        )
        sample_evaluation_bracket: TEDSMetricSampleEvaluation = (
            teds_metric.evaluate_sample(sample_bracket)
        )

        # Print results
        print(f"Tree A Size: {sample_evaluation_bracket.tree_a_size}")
        print(f"Tree B Size: {sample_evaluation_bracket.tree_b_size}")
        print(f"TEDS Score: {sample_evaluation_bracket.teds}")

        # Assertions for bracket notation test
        assert math.isclose(
            sample_evaluation_bracket.teds,
            expected_bracket_teds,
            rel_tol=TEDS_RELATIVE_TOLERANCE,
        ), (
            f"Wrong TEDS score for valid bracket (stem: {stem}). Expected {expected_bracket_teds}, got {sample_evaluation_bracket.teds}"
        )
        assert sample_evaluation_bracket.tree_a_size == expected_tree_a_size, (
            f"Wrong tree A size (stem: {stem}). Expected {expected_tree_a_size}, got {sample_evaluation_bracket.tree_a_size}"
        )
        assert sample_evaluation_bracket.tree_b_size == expected_tree_b_size, (
            f"Wrong tree B size (stem: {stem}). Expected {expected_tree_b_size}, got {sample_evaluation_bracket.tree_b_size}"
        )

        # Test 2: Evaluate sample using HTML input
        print("\n=== Test 2: HTML Input ===")
        sample_html = TEDSMetricHTMLInputSample(
            id=f"s2_{stem}",
            html_a=test_data["gt_html"],
            html_b=test_data["pred_html"],
            structure_only=False,
        )
        sample_evaluation_html: TEDSMetricSampleEvaluation = (
            teds_metric.evaluate_sample(sample_html)
        )

        # Print results
        print(f"Tree A Size: {sample_evaluation_html.tree_a_size}")
        print(f"Tree B Size: {sample_evaluation_html.tree_b_size}")
        print(f"TEDS Score: {sample_evaluation_html.teds}")

        # Assertions for HTML input test
        assert math.isclose(
            sample_evaluation_html.teds,
            expected_html_teds,
            rel_tol=TEDS_RELATIVE_TOLERANCE,
        ), (
            f"Wrong TEDS score for HTML input (stem: {stem}). Expected {expected_html_teds}, got {sample_evaluation_html.teds}"
        )
        assert sample_evaluation_html.tree_a_size == expected_tree_a_size, (
            f"Wrong tree A size for HTML (stem: {stem}). Expected {expected_tree_a_size}, got {sample_evaluation_html.tree_a_size}"
        )
        assert sample_evaluation_html.tree_b_size == expected_tree_b_size, (
            f"Wrong tree B size for HTML (stem: {stem}). Expected {expected_tree_b_size}, got {sample_evaluation_html.tree_b_size}"
        )

        # Test 2b: Evaluate sample using HTML input with structure_only=True
        print("\n=== Test 2b: HTML Input (structure_only=True) ===")
        sample_html_structure = TEDSMetricHTMLInputSample(
            id=f"s2b_{stem}",
            html_a=test_data["gt_html"],
            html_b=test_data["pred_html"],
            structure_only=True,
        )
        sample_evaluation_html_structure: TEDSMetricSampleEvaluation = (
            teds_metric.evaluate_sample(sample_html_structure)
        )

        # Print results
        print(f"Tree A Size: {sample_evaluation_html_structure.tree_a_size}")
        print(f"Tree B Size: {sample_evaluation_html_structure.tree_b_size}")
        print(f"TEDS Score: {sample_evaluation_html_structure.teds}")

        # Assertions for HTML input test with structure_only=True
        assert math.isclose(
            sample_evaluation_html_structure.teds,
            expected_html_structure_only_teds,
            rel_tol=TEDS_RELATIVE_TOLERANCE,
        ), (
            f"Wrong TEDS score for HTML input with structure_only=True (stem: {stem}). Expected {expected_html_structure_only_teds}, got {sample_evaluation_html_structure.teds}"
        )
        assert sample_evaluation_html_structure.tree_a_size == expected_tree_a_size, (
            f"Wrong tree A size for HTML with structure_only=True (stem: {stem}). Expected {expected_tree_a_size}, got {sample_evaluation_html_structure.tree_a_size}"
        )
        assert sample_evaluation_html_structure.tree_b_size == expected_tree_b_size, (
            f"Wrong tree B size for HTML with structure_only=True (stem: {stem}). Expected {expected_tree_b_size}, got {sample_evaluation_html_structure.tree_b_size}"
        )

        # Test 3: Test with broken bracket - should raise ValueError
        print("\n=== Test 3: Broken Bracket (Error Case) ===")
        broken_sample = TEDSMetricBracketInputSample(
            id=f"s3_{stem}",
            bracket_a=test_data["broken_bracket"],
            bracket_b=test_data["pred_bracket"],
        )
        with pytest.raises(ValueError) as exc_info:
            teds_metric.evaluate_sample(broken_sample)

        print(f"Expected error caught: {exc_info.value}")

    print("\n All tests passed!")


if __name__ == "__main__":
    test_cpp_bindings()
    test_teds_metric_api()

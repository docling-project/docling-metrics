import json
import math
from pathlib import Path

from docling_metrics_table.docling_metrics_table import (
    TableMetric,
    TableMetricBracketInputSample,
    TableMetricCell,
    TableMetricCellsInputSample,
    TableMetricHTMLInputSample,
    TableMetricKind,
)
from docling_metrics_table.utils.grits import cells_to_html
from docling_metrics_table.utils.teds import TEDScorer

# Test configuration
TEDS_RELATIVE_TOLERANCE = 1e-6

# Test data for GriTS
TEST_FILE = "tests/data/grits_10.json"


def load_test_data():
    r"""
    Load test GriTS data
    """
    package_dir = Path(__file__).parent.parent
    with open(package_dir / TEST_FILE, "r") as fp:
        return json.load(fp)


def assert_close(actual: float | None, expected: float | None, field_name: str) -> None:
    assert actual is not None
    assert expected is not None
    assert math.isclose(actual, expected, rel_tol=TEDS_RELATIVE_TOLERANCE), (
        f"Wrong {field_name}. Expected {expected}, got {actual}"
    )


def test_grits_api():
    r""" """
    all_test_data = load_test_data()

    # Initialize TableMetric for GriTs
    table_metric = TableMetric(metrics=[TableMetricKind.GRITS])
    teds_scorer = TEDScorer()

    for sample_idx, test_data in enumerate(all_test_data):
        true_cells = [
            TableMetricCell.model_validate(cell) for cell in test_data["true_cells"]
        ]
        pred_cells = [
            TableMetricCell.model_validate(cell) for cell in test_data["pred_cells"]
        ]

        # Test with Cells input
        cells_sample = TableMetricCellsInputSample(
            id=f"cells_{sample_idx}",
            cells_a=true_cells,
            cells_b=pred_cells,
        )
        cells_evaluation = table_metric.evaluate_sample(cells_sample)

        assert cells_evaluation.grits is not None
        assert_close(
            cells_evaluation.grits.grits_topology,
            test_data["grits_top"],
            "grits_topology",
        )
        assert_close(
            cells_evaluation.grits.grits_precision_topology,
            test_data["grits_precision_top"],
            "grits_precision_topology",
        )
        assert_close(
            cells_evaluation.grits.grits_recall_topology,
            test_data["grits_recall_top"],
            "grits_recall_topology",
        )
        assert_close(
            cells_evaluation.grits.grits_topology_upper_bound,
            test_data["grits_top_upper_bound"],
            "grits_topology_upper_bound",
        )
        assert_close(
            cells_evaluation.grits.grits_content,
            test_data["grits_con"],
            "grits_content",
        )
        assert_close(
            cells_evaluation.grits.grits_precision_content,
            test_data["grits_precision_con"],
            "grits_precision_content",
        )
        assert_close(
            cells_evaluation.grits.grits_recall_content,
            test_data["grits_recall_con"],
            "grits_recall_content",
        )
        assert_close(
            cells_evaluation.grits.grits_content_upper_bound,
            test_data["grits_con_upper_bound"],
            "grits_content_upper_bound",
        )
        assert_close(
            cells_evaluation.grits.grits_location,
            test_data["grits_loc"],
            "grits_location",
        )
        assert_close(
            cells_evaluation.grits.grits_precision_location,
            test_data["grits_precision_loc"],
            "grits_precision_location",
        )
        assert_close(
            cells_evaluation.grits.grits_recall_location,
            test_data["grits_recall_loc"],
            "grits_recall_location",
        )
        assert_close(
            cells_evaluation.grits.grits_location_upper_bound,
            test_data["grits_loc_upper_bound"],
            "grits_location_upper_bound",
        )

        # Test with HTML input
        html_a = cells_to_html([cell.model_dump() for cell in true_cells])
        html_b = cells_to_html([cell.model_dump() for cell in pred_cells])
        html_sample = TableMetricHTMLInputSample(
            id=f"html_{sample_idx}",
            html_a=html_a,
            html_b=html_b,
            structure_only=False,
        )
        html_evaluation = table_metric.evaluate_sample(html_sample)

        assert html_evaluation.grits is not None
        assert_close(
            html_evaluation.grits.grits_topology,
            test_data["grits_top"],
            "html grits_topology",
        )
        assert_close(
            html_evaluation.grits.grits_precision_topology,
            test_data["grits_precision_top"],
            "html grits_precision_topology",
        )
        assert_close(
            html_evaluation.grits.grits_recall_topology,
            test_data["grits_recall_top"],
            "html grits_recall_topology",
        )
        assert_close(
            html_evaluation.grits.grits_topology_upper_bound,
            test_data["grits_top_upper_bound"],
            "html grits_topology_upper_bound",
        )
        assert_close(
            html_evaluation.grits.grits_content,
            test_data["grits_con"],
            "html grits_content",
        )
        assert_close(
            html_evaluation.grits.grits_precision_content,
            test_data["grits_precision_con"],
            "html grits_precision_content",
        )
        assert_close(
            html_evaluation.grits.grits_recall_content,
            test_data["grits_recall_con"],
            "html grits_recall_content",
        )
        assert_close(
            html_evaluation.grits.grits_content_upper_bound,
            test_data["grits_con_upper_bound"],
            "html grits_content_upper_bound",
        )
        assert html_evaluation.grits.grits_location is None
        assert html_evaluation.grits.grits_precision_location is None
        assert html_evaluation.grits.grits_recall_location is None
        assert html_evaluation.grits.grits_location_upper_bound is None

        # Test with bracket input. Only structure is supported for GriTS.
        bracket_sample = TableMetricBracketInputSample(
            id=f"bracket_{sample_idx}",
            bracket_a=teds_scorer.html_to_bracket(html_a, structure_only=True),
            bracket_b=teds_scorer.html_to_bracket(html_b, structure_only=True),
        )
        bracket_evaluation = table_metric.evaluate_sample(bracket_sample)

        assert bracket_evaluation.grits is not None
        assert_close(
            bracket_evaluation.grits.grits_topology,
            test_data["grits_top"],
            "bracket grits_topology",
        )
        assert_close(
            bracket_evaluation.grits.grits_precision_topology,
            test_data["grits_precision_top"],
            "bracket grits_precision_topology",
        )
        assert_close(
            bracket_evaluation.grits.grits_recall_topology,
            test_data["grits_recall_top"],
            "bracket grits_recall_topology",
        )
        assert_close(
            bracket_evaluation.grits.grits_topology_upper_bound,
            test_data["grits_top_upper_bound"],
            "bracket grits_topology_upper_bound",
        )
        assert bracket_evaluation.grits.grits_content is None
        assert bracket_evaluation.grits.grits_precision_content is None
        assert bracket_evaluation.grits.grits_recall_content is None
        assert bracket_evaluation.grits.grits_content_upper_bound is None
        assert bracket_evaluation.grits.grits_location is None
        assert bracket_evaluation.grits.grits_precision_location is None
        assert bracket_evaluation.grits.grits_recall_location is None
        assert bracket_evaluation.grits.grits_location_upper_bound is None


if __name__ == "__main__":
    test_grits_api()

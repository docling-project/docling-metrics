from docling_metrics_table.docling_metrics_table import (
    TableMetric,
    TableMetricKind,
)

# Test configuration
TEDS_RELATIVE_TOLERANCE = 1e-6

# Test data for GriTS
TEST_FILE = "tests/data/grits_10.json"


def load_test_data():
    r"""
    Load test GriTS data
    """
    # TODO: Load the json file and return the loaded object


def test_grits_api():
    r""" """
    all_test_data = load_test_data()

    # Initialize TableMetric for GriTs
    table_metric = TableMetric(metrics=[TableMetricKind.GRITS])

    # TODO: Test the following use cases
    # - Use the loaded test data to create TableMetricCellsInputSample objects and compute all tasks. Compare the computed metrics with the ones from the test file.
    # - Convert the TableMetricCellsInputSample into HTML and compute the structure and content tasks. Compare the computed metrics with the ones from the test file.
    # - All comparisons with the values from the test file should be checked if they are within the tolerance.


if __name__ == "__main__":
    test_grits_api()

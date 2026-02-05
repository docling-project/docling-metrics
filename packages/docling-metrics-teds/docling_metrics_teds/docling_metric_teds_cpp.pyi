"""Type stubs for the docling_metric_teds_cpp C++ extension module."""

from typing import Final

class TEDSSampleEvaluation:
    """Evaluation result for a single sample."""

    error_id: int
    error_msg: str
    id: str
    tree_a_size: int
    tree_b_size: int
    teds: float

class TEDSDatasetEvaluation:
    """Evaluation result for an entire dataset."""

    error_id: int
    error_msg: str
    teds: float
    sample_evaluations: dict[str, TEDSSampleEvaluation]

class TEDSManager:
    """Manager for computing TEDS metrics on tree structures."""

    def __init__(self) -> None:
        """Initialize a new TEDSManager instance."""

    def evaluate_sample(
        self,
        id: str,
        bracket_a: str,
        bracket_b: str,
    ) -> TEDSSampleEvaluation:
        """Evaluate a single sample.

        Args:
            id: Sample identifier
            bracket_a: Input A in bracket notation
            bracket_b: Input B in bracket notation

        Returns:
            TEDSSampleEvaluation: Evaluation result containing TEDS score and metadata
        """

    def evaluate_html_sample(
        self,
        id: str,
        html_a: str,
        html_b: str,
        structure_only: bool,
    ) -> TEDSSampleEvaluation:
        """Evaluate a single sample from HTML format.

        Args:
            id: Sample identifier
            html_a: Input A in HTML format
            html_b: Input B in HTML format
            structure_only: If true the HTML content is not considered

        Returns:
            TEDSSampleEvaluation: Evaluation result containing TEDS score and metadata
        """

    def aggregate(self) -> None:
        """Aggregate evaluation results across all samples."""

    def evaluate_dataset(self) -> TEDSDatasetEvaluation:
        """Evaluate the entire dataset.

        Returns:
            TEDSDatasetEvaluation: Dataset-level evaluation result
        """

__all__: Final = ["TEDSDatasetEvaluation", "TEDSManager", "TEDSSampleEvaluation"]

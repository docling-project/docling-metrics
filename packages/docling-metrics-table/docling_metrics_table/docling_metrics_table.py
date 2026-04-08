from typing import Annotated, Any, Iterable, Optional

from docling_metrics_core.base_types import (
    BaseAggregateResult,
    BaseInputSample,
    BaseMetric,
    BaseSampleResult,
)
from lxml import html
from pydantic import Field

from docling_metrics_table.utils.grits import grits_from_html
from docling_metrics_table.utils.teds import TableTree, TEDScorer

from . import docling_metric_table_cpp


class TableMetricBracketInputSample(BaseInputSample):
    bracket_a: Annotated[
        str, Field(description="The input-a string to be evaluated in bracket format")
    ]
    bracket_b: Annotated[
        str, Field(description="The input-b string to be evaluated in bracket format")
    ]


class TableMetricHTMLInputSample(BaseInputSample):
    html_a: Annotated[
        str, Field(description="The input-a string to be evaluated in HTML format")
    ]
    html_b: Annotated[
        str, Field(description="The input-b string to be evaluated in HTML format")
    ]
    structure_only: Annotated[
        bool, Field(description="If True the content is not evaluated")
    ] = False


# BBox = Sequence[float]
# Cell = Dict[str, Any]
# class TableMetricInputSample(BaseInputSample):
#     true_bboxes: Sequence[BBox],
#     true_labels: Sequence[int],
#     true_scores: Sequence[float],
#     true_cells: List[Cell],
#     pred_bboxes: Sequence[BBox],
#     pred_labels: Sequence[int],
#     pred_scores: Sequence[float],
#     pred_cells: List[Cell],


class TableMetricSampleEvaluation(BaseSampleResult):
    tree_a_size: int
    tree_b_size: int
    teds: float

    grits_topology: float | None = None
    grits_precision_topology: float | None = None
    grits_recall_topology: float | None = None
    grits_topology_upper_bound: float | None = None

    grits_location: float | None = None
    grits_precision_location: float | None = None
    grits_recall_location: float | None = None
    grits_location_upper_bound: float | None = None

    grits_content: float | None = None
    grits_precision_content: float | None = None
    grits_recall_content: float | None = None
    grits_content_upper_bound: float | None = None


class TableMetricDatasetEvaluation(BaseAggregateResult): ...


class TableMetric(BaseMetric):
    r"""
    Expose the C++ TEDS metric as a Python module.
    """

    def __init__(self) -> None:
        r""" """
        self._teds_manager = docling_metric_table_cpp.TEDSManager()
        self._teds_scorer = TEDScorer()

    def evaluate_sample(  # type: ignore[override]
        self, sample: TableMetricBracketInputSample | TableMetricHTMLInputSample
    ) -> TableMetricSampleEvaluation:
        r"""
        Evaluate a single sample.
        """
        grits_metrics: dict[str, float | int] = {}
        # Decide if html should be first converted to bracket format
        if isinstance(sample, TableMetricHTMLInputSample):
            structure_only = sample.structure_only
            bracket_a = self._teds_scorer.html_to_bracket(
                sample.html_a, structure_only=structure_only
            )
            bracket_b = self._teds_scorer.html_to_bracket(
                sample.html_b, structure_only=structure_only
            )
            grits_metrics = grits_from_html(sample.html_a, sample.html_b)
        elif isinstance(sample, TableMetricBracketInputSample):
            bracket_a = sample.bracket_a
            bracket_b = sample.bracket_b
        else:
            raise ValueError("Invalid sample type")  # type: ignore[unreachable]

        # Evaluate the sample
        sample_evaluaton: Any = self._teds_manager.evaluate_sample(
            sample.id,
            bracket_a,
            bracket_b,
        )
        if sample_evaluaton.error_id != 0:
            raise ValueError(sample_evaluaton.error_msg)

        result = TableMetricSampleEvaluation(
            id=sample.id,
            tree_a_size=sample_evaluaton.tree_a_size,
            tree_b_size=sample_evaluaton.tree_b_size,
            teds=sample_evaluaton.teds,
            grits_topology=grits_metrics.get("grits_top"),
            grits_precision_topology=grits_metrics.get("grits_precision_top"),
            grits_recall_topology=grits_metrics.get("grits_recall_top"),
            grits_topology_upper_bound=grits_metrics.get("grits_top_upper_bound"),
            grits_location=grits_metrics.get("grits_loc"),
            grits_precision_location=grits_metrics.get("grits_precision_loc"),
            grits_recall_location=grits_metrics.get("grits_recall_loc"),
            grits_location_upper_bound=grits_metrics.get("grits_loc_upper_bound"),
            grits_content=grits_metrics.get("grits_con"),
            grits_precision_content=grits_metrics.get("grits_precision_con"),
            grits_recall_content=grits_metrics.get("grits_recall_con"),
            grits_content_upper_bound=grits_metrics.get("grits_con_upper_bound"),
        )
        return result

    def aggregate(  # type: ignore[override]
        self, results: Iterable[TableMetricSampleEvaluation]
    ) -> Optional[TableMetricDatasetEvaluation]:
        r"""
        Aggregate multiple sample results
        """
        return None

    def evaluate_dataset(
        self,
        sample_pairs: Iterable[
            TableMetricBracketInputSample | TableMetricHTMLInputSample
        ],
    ) -> TableMetricDatasetEvaluation:
        r"""
        Evaluate a dataset.
        """
        result = TableMetricDatasetEvaluation(sample_count=0)
        return result

    def _html_to_bracket(self, html_str: str) -> str:
        r"""
        Convert html to bracket format
        """
        html_obj = html.fromstring(html_str)
        table_tree: TableTree = self._teds_scorer.html_to_table_tree(html_obj)
        bracket: str = table_tree.bracket()
        return bracket

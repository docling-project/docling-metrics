from enum import StrEnum
from typing import Annotated, Iterable, Optional

from docling_metrics_core.base_types import (
    BaseAggregateResult,
    BaseInputSample,
    BaseMetric,
    BaseSampleResult,
)
from lxml import html
from pydantic import BaseModel, Field

from docling_metrics_table.utils.grits import grits_from_cells, grits_from_html
from docling_metrics_table.utils.teds import TableTree, TEDScorer

from . import docling_metric_table_cpp


class TableMetric(StrEnum):
    TEDS = "TEDS"
    GRITS = "GriTS"


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


class TableMetricCell(BaseModel):
    bbox: Annotated[
        list[float],
        Field(
            min_length=4,
            max_length=4,
            description="Cell bounding box as [x0, y0, x1, y1]",
        ),
    ]
    cell_text: Annotated[str, Field(description="Cell text content")]
    row_nums: Annotated[
        list[int], Field(description="Occupied row indices for this cell")
    ]
    column_nums: Annotated[
        list[int], Field(description="Occupied column indices for this cell")
    ]


class TableMetricGeometricInputSample(BaseInputSample):
    true_cells: Annotated[
        list[TableMetricCell],
        Field(description="Ground-truth table cells with geometry"),
    ]
    pred_cells: Annotated[
        list[TableMetricCell],
        Field(description="Predicted table cells with geometry"),
    ]


class TEDSSampleEvaluation(BaseModel):
    tree_a_size: int
    tree_b_size: int
    teds: float


class GriTSSampleEvaluation(BaseModel):
    # Detection of spans
    grits_topology: float
    grits_precision_topology: float
    grits_recall_topology: float
    grits_topology_upper_bound: float

    # Cell content
    grits_content: float
    grits_precision_content: float
    grits_recall_content: float
    grits_content_upper_bound: float

    # Bounding boxes of the cells. This is populated only when the InputSample contains bboxes
    grits_location: float | None
    grits_precision_location: float | None
    grits_recall_location: float | None
    grits_location_upper_bound: float | None


class TableMetricSampleEvaluation(BaseSampleResult):
    teds: TEDSSampleEvaluation | None = None
    grits: GriTSSampleEvaluation | None = None


class TableMetricDatasetEvaluation(BaseAggregateResult): ...


# TODO: Refactor the implementation of TableMetric to respect the self._metrics.
# All evaluation methods should perfom the corresponding metric only if it has been enabled


class TableMetric(BaseMetric):
    r"""
    Table Structure Recognition metrics:
    - TEDS. Expose the C++ TEDS metric as a Python module.
    - GriTS
    """

    def __init__(
        self, metrics: list[TableMetric] = [TableMetric.TEDS, TableMetric.GRITS]
    ) -> None:
        r""" """
        self._metrics = metrics
        self._teds_manager = docling_metric_table_cpp.TEDSManager()
        self._teds_scorer = TEDScorer()

    def evaluate_sample(  # type: ignore[override]
        self,
        sample: TableMetricBracketInputSample
        | TableMetricHTMLInputSample
        | TableMetricGeometricInputSample,
    ) -> TableMetricSampleEvaluation:
        r"""
        Evaluate a single sample.
        """
        grits_evaluation: GriTSSampleEvaluation | None = None
        teds_evaluation = None

        if isinstance(sample, TableMetricHTMLInputSample):
            structure_only = sample.structure_only
            bracket_a = self._teds_scorer.html_to_bracket(
                sample.html_a, structure_only=structure_only
            )
            bracket_b = self._teds_scorer.html_to_bracket(
                sample.html_b, structure_only=structure_only
            )
            grits_metrics = grits_from_html(sample.html_a, sample.html_b)
            sample_evaluaton = self._teds_manager.evaluate_sample(
                sample.id,
                bracket_a,
                bracket_b,
            )
            if sample_evaluaton.error_id != 0:
                raise ValueError(sample_evaluaton.error_msg)
            teds_evaluation = TEDSSampleEvaluation(
                tree_a_size=sample_evaluaton.tree_a_size,
                tree_b_size=sample_evaluaton.tree_b_size,
                teds=sample_evaluaton.teds,
            )
            grits_evaluation = GriTSSampleEvaluation(
                grits_topology=grits_metrics["grits_top"],
                grits_precision_topology=grits_metrics["grits_precision_top"],
                grits_recall_topology=grits_metrics["grits_recall_top"],
                grits_topology_upper_bound=grits_metrics["grits_top_upper_bound"],
                grits_content=grits_metrics["grits_con"],
                grits_precision_content=grits_metrics["grits_precision_con"],
                grits_recall_content=grits_metrics["grits_recall_con"],
                grits_content_upper_bound=grits_metrics["grits_con_upper_bound"],
                grits_location=None,
                grits_precision_location=None,
                grits_recall_location=None,
                grits_location_upper_bound=None,
            )
        elif isinstance(sample, TableMetricBracketInputSample):
            bracket_a = sample.bracket_a
            bracket_b = sample.bracket_b
            sample_evaluaton = self._teds_manager.evaluate_sample(
                sample.id,
                bracket_a,
                bracket_b,
            )
            if sample_evaluaton.error_id != 0:
                raise ValueError(sample_evaluaton.error_msg)
            teds_evaluation = TEDSSampleEvaluation(
                tree_a_size=sample_evaluaton.tree_a_size,
                tree_b_size=sample_evaluaton.tree_b_size,
                teds=sample_evaluaton.teds,
            )
        elif isinstance(sample, TableMetricGeometricInputSample):
            grits_metrics = grits_from_cells(
                [cell.model_dump() for cell in sample.true_cells],
                [cell.model_dump() for cell in sample.pred_cells],
            )
            grits_evaluation = GriTSSampleEvaluation(
                grits_topology=grits_metrics["grits_top"],
                grits_precision_topology=grits_metrics["grits_precision_top"],
                grits_recall_topology=grits_metrics["grits_recall_top"],
                grits_topology_upper_bound=grits_metrics["grits_top_upper_bound"],
                grits_content=grits_metrics["grits_con"],
                grits_precision_content=grits_metrics["grits_precision_con"],
                grits_recall_content=grits_metrics["grits_recall_con"],
                grits_content_upper_bound=grits_metrics["grits_con_upper_bound"],
                grits_location=grits_metrics["grits_loc"],
                grits_precision_location=grits_metrics["grits_precision_loc"],
                grits_recall_location=grits_metrics["grits_recall_loc"],
                grits_location_upper_bound=grits_metrics["grits_loc_upper_bound"],
            )
        else:
            raise ValueError("Invalid sample type")  # type: ignore[unreachable]

        result = TableMetricSampleEvaluation(
            id=sample.id,
            teds=teds_evaluation,
            grits=grits_evaluation,
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
            TableMetricBracketInputSample
            | TableMetricHTMLInputSample
            | TableMetricGeometricInputSample
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

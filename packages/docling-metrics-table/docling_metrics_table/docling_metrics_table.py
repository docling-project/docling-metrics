from enum import Enum
from typing import Annotated, Iterable, Optional

from docling_metrics_core.base_types import (
    BaseAggregateResult,
    BaseInputSample,
    BaseMetric,
    BaseSampleResult,
)
from lxml import html
from pydantic import BaseModel, Field

from docling_metrics_table.utils.grits import (
    cells_to_html,
    grits_from_cells,
    grits_from_html,
)
from docling_metrics_table.utils.teds import TableTree, TEDScorer

from . import docling_metric_table_cpp


class TableMetricKind(str, Enum):
    ALL = "ALL"
    TEDS = "TEDS"
    GRITS = "GriTS"


class TableMetricTaskKind(str, Enum):
    ALL = "ALL"
    STRUCTURE = "structure"
    CONTENT = "content"
    LOCATION = "location"


class TableMetricBracketInputSample(BaseInputSample):
    r"""Supports only the STRUCTURE task"""

    bracket_a: Annotated[
        str, Field(description="The input-a string to be evaluated in bracket format")
    ]
    bracket_b: Annotated[
        str, Field(description="The input-b string to be evaluated in bracket format")
    ]


class TableMetricHTMLInputSample(BaseInputSample):
    r"""Supports the tasks STRUCTURE and CONTENT"""

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
    r"""Supports the tasks STRUCTURE, CONTENT, LOCATION"""

    true_cells: Annotated[
        list[TableMetricCell],
        Field(description="Ground-truth table cells with geometry"),
    ]
    pred_cells: Annotated[
        list[TableMetricCell],
        Field(description="Predicted table cells with geometry"),
    ]

    # Limit the computed tasks to the given ones
    tasks: list[TableMetricTaskKind] = [TableMetricTaskKind.ALL]


class TEDSSampleEvaluation(BaseModel):
    tree_a_size: int
    tree_b_size: int
    teds: float


class GriTSSampleEvaluation(BaseModel):
    # Structure (topology)
    grits_topology: float | None
    grits_precision_topology: float | None
    grits_recall_topology: float | None
    grits_topology_upper_bound: float | None

    # Cell content
    grits_content: float | None
    grits_precision_content: float | None
    grits_recall_content: float | None
    grits_content_upper_bound: float | None

    # Location of the table cells
    grits_location: float | None
    grits_precision_location: float | None
    grits_recall_location: float | None
    grits_location_upper_bound: float | None


class TableMetricSampleEvaluation(BaseSampleResult):
    teds: TEDSSampleEvaluation | None = None
    grits: GriTSSampleEvaluation | None = None


class TableMetricDatasetEvaluation(BaseAggregateResult): ...


class TableMetric(BaseMetric):
    r"""
    Table Structure Recognition metrics:
    - TEDS. Expose the C++ TEDS metric as a Python module.
    - GriTS
    """

    def __init__(self, metrics: list[TableMetricKind] = [TableMetricKind.ALL]) -> None:
        r"""
        Initialize the TableMetric for the given list of metrics
        """
        # Select the metrics
        metric_set = set(metrics)
        if TableMetricKind.ALL in metric_set:
            metric_set.remove(TableMetricKind.ALL)
            metric_set.update(
                metric_kind
                for metric_kind in TableMetricKind
                if metric_kind is not TableMetricKind.ALL
            )
        self._metrics = metric_set

        if len(self._metrics) == 0:
            raise ValueError("Cannot initialize TableMetrics without tasks")

        self._teds_scorer = TEDScorer()

        # Initialize the TEDS metric
        if TableMetricKind.TEDS in self._metrics:
            self._teds_manager = docling_metric_table_cpp.TEDSManager()

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
        teds_evaluation: TEDSSampleEvaluation | None = None

        # Decide which metrics to compute
        compute_teds = TableMetricKind.TEDS in self._metrics
        compute_grits = TableMetricKind.GRITS in self._metrics

        if isinstance(sample, TableMetricHTMLInputSample):
            structure_only = sample.structure_only
            if compute_teds:
                teds_evaluation = self._evaluate_teds_from_html(
                    sample.id,
                    sample.html_a,
                    sample.html_b,
                    structure_only=structure_only,
                )
            if compute_grits:
                # The location task cannot be computed by the HTML inputs
                grits_metrics = grits_from_html(
                    sample.html_a,
                    sample.html_b,
                    enable_topology=True,
                    enable_content=not structure_only,
                )
                grits_evaluation = self._build_grits_evaluation(grits_metrics)
        elif isinstance(sample, TableMetricGeometricInputSample):
            true_cells_dict = [cell.model_dump() for cell in sample.true_cells]
            pred_cells_dict = [cell.model_dump() for cell in sample.pred_cells]

            if compute_teds:
                teds_evaluation = self._evaluate_teds_from_html(
                    sample.id,
                    cells_to_html(true_cells_dict),
                    cells_to_html(pred_cells_dict),
                )

            if compute_grits:
                grits_metrics = grits_from_cells(
                    true_cells_dict,
                    pred_cells_dict,
                    enable_topology=TableMetricTaskKind.STRUCTURE in sample.tasks,
                    enable_content=TableMetricTaskKind.CONTENT in sample.tasks,
                    enable_location=TableMetricTaskKind.LOCATION in sample.tasks,
                )
                grits_evaluation = self._build_grits_evaluation(grits_metrics)
        elif isinstance(sample, TableMetricBracketInputSample):
            if compute_teds:
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

            if compute_grits:
                html_a = self._teds_scorer.bracket_to_html(sample.bracket_a)
                html_b = self._teds_scorer.bracket_to_html(sample.bracket_b)
                grits_metrics = grits_from_html(
                    html_a,
                    html_b,
                    enable_topology=True,
                    enable_content=False,
                )
                grits_evaluation = self._build_grits_evaluation(grits_metrics)
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

    def _evaluate_teds_from_html(
        self, sample_id: str, html_a: str, html_b: str, structure_only: bool = False
    ) -> TEDSSampleEvaluation:
        bracket_a = self._teds_scorer.html_to_bracket(
            html_a, structure_only=structure_only
        )
        bracket_b = self._teds_scorer.html_to_bracket(
            html_b, structure_only=structure_only
        )
        sample_evaluaton = self._teds_manager.evaluate_sample(
            sample_id,
            bracket_a,
            bracket_b,
        )
        if sample_evaluaton.error_id != 0:
            raise ValueError(sample_evaluaton.error_msg)
        return TEDSSampleEvaluation(
            tree_a_size=sample_evaluaton.tree_a_size,
            tree_b_size=sample_evaluaton.tree_b_size,
            teds=sample_evaluaton.teds,
        )

    def _build_grits_evaluation(
        self, grits_metrics: dict[str, float | int]
    ) -> GriTSSampleEvaluation:
        return GriTSSampleEvaluation(
            grits_topology=grits_metrics.get("grits_top"),
            grits_precision_topology=grits_metrics.get("grits_precision_top"),
            grits_recall_topology=grits_metrics.get("grits_recall_top"),
            grits_topology_upper_bound=grits_metrics.get("grits_top_upper_bound"),
            grits_content=grits_metrics.get("grits_con"),
            grits_precision_content=grits_metrics.get("grits_precision_con"),
            grits_recall_content=grits_metrics.get("grits_recall_con"),
            grits_content_upper_bound=grits_metrics.get("grits_con_upper_bound"),
            grits_location=grits_metrics.get("grits_loc"),
            grits_precision_location=grits_metrics.get("grits_precision_loc"),
            grits_recall_location=grits_metrics.get("grits_recall_loc"),
            grits_location_upper_bound=grits_metrics.get("grits_loc_upper_bound"),
        )

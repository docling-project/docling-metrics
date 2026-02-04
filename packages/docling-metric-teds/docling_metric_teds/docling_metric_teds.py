from typing import Annotated, Any, Iterable, Optional

from docling_metrics_core.base_types import (
    BaseAggregateResult,
    BaseInputSample,
    BaseMetric,
    BaseSampleResult,
)
from lxml import html
from pydantic import Field

from docling_metric_teds.utils.teds import TableTree, TEDScorer

from . import docling_metric_teds_cpp

TEDSManager = docling_metric_teds_cpp.TEDSManager
TEDSSampleEvaluation: Any = docling_metric_teds_cpp.TEDSSampleEvaluation
TEDSDatasetEvaluation: Any = docling_metric_teds_cpp.TEDSDatasetEvaluation


class TEDSMetricBracketInputSample(BaseInputSample):
    bracket_a: Annotated[
        str, Field(description="The input-a string to be evaluated in bracket format")
    ]
    bracket_b: Annotated[
        str, Field(description="The input-b string to be evaluated in bracket format")
    ]


class TEDSMetricHTMLInputSample(BaseInputSample):
    html_a: Annotated[
        str, Field(description="The input-a string to be evaluated in HTML format")
    ]
    html_b: Annotated[
        str, Field(description="The input-b string to be evaluated in HTML format")
    ]
    structure_only: Annotated[
        bool, Field(description="If True the content is not evaluated")
    ] = False


class TEDSMetricSampleEvaluation(BaseSampleResult):
    tree_a_size: int
    tree_b_size: int
    teds: float


class TEDSMetricDatasetEvaluation(BaseAggregateResult): ...


class TEDSMetric(BaseMetric):
    r"""
    Expose the C++ TEDS metric as a Python module.
    """

    def __init__(self) -> None:
        r""" """
        self._teds_manager = TEDSManager()
        self._teds_scorer = TEDScorer()

    def evaluate_sample(  # type: ignore[override]
        self, sample: TEDSMetricBracketInputSample | TEDSMetricHTMLInputSample
    ) -> TEDSMetricSampleEvaluation:
        r"""
        Evaluate a single sample.
        """
        # Decide if html should be first converted to bracket format
        if isinstance(sample, TEDSMetricHTMLInputSample):
            # TODO: Switch to the C++ HTML-to-bracket conversion when it will be ready
            structure_only = sample.structure_only
            bracket_a = self._teds_scorer.html_to_bracket(
                sample.html_a, structure_only=structure_only
            )
            bracket_b = self._teds_scorer.html_to_bracket(
                sample.html_b, structure_only=structure_only
            )
        elif isinstance(sample, TEDSMetricBracketInputSample):
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

        result = TEDSMetricSampleEvaluation(
            id=sample.id,
            tree_a_size=sample_evaluaton.tree_a_size,
            tree_b_size=sample_evaluaton.tree_b_size,
            teds=sample_evaluaton.teds,
        )
        return result

    def aggregate(  # type: ignore[override]
        self, results: Iterable[TEDSMetricSampleEvaluation]
    ) -> Optional[TEDSMetricDatasetEvaluation]:
        r"""
        Aggregate multiple sample results
        """
        return None

    def evaluate_dataset(
        self, sample_pairs: Iterable[BaseInputSample]
    ) -> TEDSMetricDatasetEvaluation:
        r"""
        Evaluate a dataset.
        """
        # TODO: Add implementation
        result = TEDSMetricDatasetEvaluation(sample_count=0)
        return result

    def _html_to_bracket(self, html_str: str) -> str:
        r"""
        Convert html to bracket format
        """
        html_obj = html.fromstring(html_str)
        table_tree: TableTree = self._teds_scorer.html_to_table_tree(html_obj)
        bracket: str = table_tree.bracket()
        return bracket

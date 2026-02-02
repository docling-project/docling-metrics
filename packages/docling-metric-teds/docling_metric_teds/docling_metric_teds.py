from typing import Annotated, Any, Iterable, Optional

import docling_metric_teds_cpp  # type: ignore[import-not-found]
from docling_metrics_core.base_types import (
    BaseAggregateResult,
    BaseInputSample,
    BaseMetric,
    BaseSampleResult,
)
from lxml import html
from pydantic import Field

from docling_metric_teds.utils.teds import TableTree, TEDScorer

TEDSManager = docling_metric_teds_cpp.TEDSManager
TEDSSampleEvaluation: Any = docling_metric_teds_cpp.TEDSSampleEvaluation
TEDSDatasetEvaluation: Any = docling_metric_teds_cpp.TEDSDatasetEvaluation


class TEDSMetricBracketInputSample(BaseInputSample):
    a_bracket: Annotated[
        str, Field(description="The input-a string to be evaluated in bracket format")
    ]
    b_bracket: Annotated[
        str, Field(description="The input-b string to be evaluated in bracket format")
    ]


class TEDSMetricHTMLInputSample(BaseInputSample):
    a_html: Annotated[
        str, Field(description="The input-a string to be evaluated in HTML format")
    ]
    b_html: Annotated[
        str, Field(description="The input-b string to be evaluated in HTML format")
    ]
    structure_only: Annotated[
        bool, Field(description="If True the content is not evaluated")
    ] = False


class TEDSMetricSampleEvaluation(BaseSampleResult):
    gt_tree_size: int
    pred_tree_size: int
    teds: float


class TEDSMetricDatasetEvaluation(BaseAggregateResult):
    error_id: int
    error_msg: str
    gt_tree_size: str
    pred_tree_size: str


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
            a_bracket = self._teds_scorer.html_to_bracket(sample.a_html)
            b_bracket = self._teds_scorer.html_to_bracket(sample.b_html)
        elif isinstance(sample, TEDSMetricBracketInputSample):
            a_bracket = sample.a_bracket
            b_bracket = sample.b_bracket
        else:
            raise ValueError("Invalid sample type")  # type: ignore[unreachable]

        # Evaluate the sample
        sample_evaluaton: Any = self._teds_manager.evaluate_sample(
            sample.id,
            a_bracket,
            b_bracket,
        )
        if sample_evaluaton.error_id != 0:
            raise ValueError(sample_evaluaton.error_msg)

        result = TEDSMetricSampleEvaluation(
            id=sample.id,
            gt_tree_size=sample_evaluaton.gt_tree_size,
            pred_tree_size=sample_evaluaton.pred_tree_size,
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
        # TODO: Implement proper dataset evaluation
        result = TEDSMetricDatasetEvaluation(
            sample_count=0,
            error_id=0,
            error_msg="",
            gt_tree_size="",
            pred_tree_size="",
        )
        return result

    def _html_to_bracket(self, html_str: str) -> str:
        r"""
        Convert html to bracket format
        """
        html_obj = html.fromstring(html_str)
        table_tree: TableTree = self._teds_scorer.html_to_table_tree(html_obj)
        bracket: str = table_tree.bracket()
        return bracket

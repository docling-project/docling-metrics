"""SMILES metric implementation for the docling-metrics-core interface."""

from __future__ import annotations

import logging
from typing import Annotated, Any, Iterable, Optional

from docling_metrics_core.base_types import (
    BaseAggregateResult,
    BaseInputSample,
    BaseMetric,
    BaseSampleResult,
)
from pydantic import Field
from rdkit import Chem, RDLogger

from docling_metrics_chemistry.molecule_scores import (
    compute_markush_prediction_quality,
    compute_molecule_prediction_quality,
    get_molecule_information,
)
from docling_metrics_chemistry.smiles_utils import canonicalize_markush

RDLogger.DisableLog("rdApp.*")
logger = logging.getLogger(__name__)


class SmilesInputSample(BaseInputSample):
    """Input sample for SMILES evaluation."""

    predicted_smiles: Annotated[
        Optional[str], Field(description="Predicted SMILES or CXSMILES string")
    ]
    gt_smiles: Annotated[
        str, Field(description="Ground truth SMILES or CXSMILES string")
    ]
    is_markush: Annotated[
        bool,
        Field(
            default=False,
            description="Whether to use Markush/CXSMILES evaluation",
        ),
    ]
    remove_stereo: Annotated[
        bool,
        Field(
            default=True,
            description="Whether to remove stereochemistry for comparison",
        ),
    ]


class SmilesSampleResult(BaseSampleResult):
    """Result of evaluating a single SMILES sample."""

    valid: Annotated[
        bool, Field(description="Whether the predicted SMILES is chemically valid")
    ]
    tanimoto: Annotated[
        float,
        Field(description="Tanimoto fingerprint similarity (0-1)"),
    ]
    tanimoto1: Annotated[
        bool, Field(description="Whether Tanimoto similarity equals 1.0")
    ]
    inchi_equality: Annotated[
        bool, Field(description="Whether InChI representations match")
    ]
    string_equality: Annotated[
        bool, Field(description="Whether SMILES strings are identical")
    ]
    # Markush-specific (None when not applicable)
    r: Annotated[
        Optional[float],
        Field(
            default=None,
            description="R-group label accuracy (0-1), None if no R-groups",
        ),
    ]
    m: Annotated[
        Optional[float],
        Field(
            default=None,
            description="M-section accuracy (0-1), None if no M-sections",
        ),
    ]
    sg: Annotated[
        Optional[float],
        Field(
            default=None,
            description="Sg-section accuracy (0-1), None if no Sg-sections",
        ),
    ]
    num_fragments_gt: Annotated[
        int, Field(default=0, description="Number of fragments in ground truth")
    ]
    num_fragments_pred: Annotated[
        int, Field(default=0, description="Number of fragments in prediction")
    ]
    num_fragments_equal: Annotated[
        bool,
        Field(default=False, description="Whether fragment counts match"),
    ]
    cxsmi_equality: Annotated[
        bool,
        Field(
            default=False,
            description="Overall CXSMILES equality (all Markush aspects match)",
        ),
    ]


class SmilesAggregateResult(BaseAggregateResult):
    """Aggregated result from multiple SMILES evaluations."""

    mean_tanimoto: Annotated[
        float,
        Field(description="Mean Tanimoto similarity across all samples"),
    ]
    validity_rate: Annotated[
        float,
        Field(description="Fraction of predictions that are valid SMILES"),
    ]
    inchi_equality_rate: Annotated[
        float,
        Field(description="Fraction of predictions with matching InChI"),
    ]
    string_equality_rate: Annotated[
        float,
        Field(description="Fraction of exact SMILES string matches"),
    ]
    # Markush aggregate (None when no Markush samples)
    mean_r: Annotated[
        Optional[float],
        Field(
            default=None,
            description="Mean R-group accuracy across applicable samples",
        ),
    ]
    mean_m: Annotated[
        Optional[float],
        Field(
            default=None,
            description="Mean M-section accuracy across applicable samples",
        ),
    ]
    mean_sg: Annotated[
        Optional[float],
        Field(
            default=None,
            description="Mean Sg-section accuracy across applicable samples",
        ),
    ]
    cxsmi_equality_rate: Annotated[
        Optional[float],
        Field(
            default=None,
            description="Fraction of Markush samples with full CXSMILES equality",
        ),
    ]


def _default_result(sample_id: str) -> dict[str, Any]:
    """Return default scores for an invalid/unparseable prediction."""
    return {
        "valid": False,
        "tanimoto": 0.0,
        "tanimoto1": False,
        "inchi_equality": False,
        "string_equality": False,
        "r": None,
        "m": None,
        "sg": None,
        "num_fragments_gt": 0,
        "num_fragments_pred": 0,
        "num_fragments_equal": False,
        "cxsmi_equality": False,
    }


class SmilesMetric(BaseMetric):
    """Metric for evaluating SMILES and Markush structure predictions.

    Supports both simple molecule comparison (Tanimoto, InChI, validity)
    and complex Markush structure evaluation (R-groups, M-sections, Sg-sections,
    fragment matching).
    """

    def evaluate_sample(  # type: ignore[override]
        self,
        sample: SmilesInputSample,
    ) -> SmilesSampleResult:
        """Evaluate a single SMILES prediction against ground truth.

        Args:
            sample: Input sample with predicted and ground truth SMILES.

        Returns:
            SmilesSampleResult with computed metrics.
        """
        gt_smiles = sample.gt_smiles
        predicted_smiles = sample.predicted_smiles
        if predicted_smiles is None:
            predicted_smiles = ""

        # Validate ground truth
        parser_params = Chem.SmilesParserParams()
        parser_params.strictCXSMILES = False
        parser_params.sanitize = False
        parser_params.removeHs = False
        gt_molecule = Chem.MolFromSmiles(gt_smiles, parser_params)
        if gt_molecule is None:
            return SmilesSampleResult(id=sample.id, **_default_result(sample.id))

        # Validate prediction
        predicted_molecule = Chem.MolFromSmiles(predicted_smiles, parser_params)
        if predicted_molecule is None:
            # Set default incorrect scores based on molecule information
            result = _default_result(sample.id)
            if sample.is_markush:
                info = get_molecule_information(gt_smiles)
                if not info["r"]:
                    result["r"] = None
                else:
                    result["r"] = 0.0
                if not info["m"]:
                    result["m"] = None
                else:
                    result["m"] = 0.0
                if not info["sg"]:
                    result["sg"] = None
                else:
                    result["sg"] = 0.0
            return SmilesSampleResult(id=sample.id, **result)

        if sample.is_markush:
            # Canonicalize for Markush comparison
            gt_smiles_canon = canonicalize_markush(gt_smiles)
            if gt_smiles_canon is None:
                return SmilesSampleResult(id=sample.id, **_default_result(sample.id))
            try:
                predicted_smiles_canon = canonicalize_markush(predicted_smiles)
            except Exception:
                return SmilesSampleResult(id=sample.id, **_default_result(sample.id))
            if predicted_smiles_canon is None:
                return SmilesSampleResult(id=sample.id, **_default_result(sample.id))

            try:
                scores = compute_markush_prediction_quality(
                    predicted_smiles=predicted_smiles_canon,
                    gt_smiles=gt_smiles_canon,
                    remove_stereo=sample.remove_stereo,
                    remove_double_bond_stereo=True,
                )
            except Exception as e:
                logger.warning(
                    "Error in Markush evaluation for gt=%s, pred=%s: %s",
                    gt_smiles,
                    predicted_smiles,
                    e,
                )
                return SmilesSampleResult(id=sample.id, **_default_result(sample.id))
        else:
            # Simple molecule comparison
            gt_smiles_canon = Chem.MolToSmiles(gt_molecule)
            predicted_smiles_canon = Chem.MolToSmiles(predicted_molecule)

            scores = compute_molecule_prediction_quality(
                predicted_smiles=predicted_smiles_canon,
                gt_smiles=gt_smiles_canon,
                remove_stereo=sample.remove_stereo,
                remove_double_bond_stereo=True,
            )

        # Build result
        result_kwargs: dict[str, Any] = {
            "id": sample.id,
            "valid": scores.get("valid", False),
            "tanimoto": scores.get("tanimoto", 0.0),
            "tanimoto1": scores.get("tanimoto1", False),
            "inchi_equality": scores.get("inchi_equality", False),
            "string_equality": scores.get("string_equality", False),
            "r": scores.get("r"),
            "m": scores.get("m"),
            "sg": scores.get("sg"),
            "num_fragments_gt": scores.get("num_fragments_gt", 0),
            "num_fragments_pred": scores.get("num_fragments_pred", 0),
            "num_fragments_equal": scores.get("num_fragments_equal", False),
            "cxsmi_equality": scores.get("cxsmi_equality", False),
        }

        return SmilesSampleResult(**result_kwargs)

    def aggregate(  # type: ignore[override]
        self, results: Iterable[SmilesSampleResult]
    ) -> SmilesAggregateResult:
        """Aggregate multiple sample results into summary statistics.

        Args:
            results: Iterable of sample evaluation results.

        Returns:
            SmilesAggregateResult with aggregated metrics.
        """
        results_list = list(results)
        sample_count = len(results_list)
        if sample_count == 0:
            return SmilesAggregateResult(
                sample_count=0,
                mean_tanimoto=0.0,
                validity_rate=0.0,
                inchi_equality_rate=0.0,
                string_equality_rate=0.0,
            )

        mean_tanimoto = sum(r.tanimoto for r in results_list) / sample_count
        validity_rate = sum(1 for r in results_list if r.valid) / sample_count
        inchi_rate = sum(1 for r in results_list if r.inchi_equality) / sample_count
        string_rate = sum(1 for r in results_list if r.string_equality) / sample_count

        # Markush aggregates (only for samples that have them)
        r_values = [r.r for r in results_list if r.r is not None]
        m_values = [r.m for r in results_list if r.m is not None]
        sg_values = [r.sg for r in results_list if r.sg is not None]
        markush_results = [r for r in results_list if r.num_fragments_gt > 0]

        return SmilesAggregateResult(
            sample_count=sample_count,
            mean_tanimoto=round(mean_tanimoto, 3),
            validity_rate=round(validity_rate, 3),
            inchi_equality_rate=round(inchi_rate, 3),
            string_equality_rate=round(string_rate, 3),
            mean_r=(round(sum(r_values) / len(r_values), 3) if r_values else None),
            mean_m=(round(sum(m_values) / len(m_values), 3) if m_values else None),
            mean_sg=(round(sum(sg_values) / len(sg_values), 3) if sg_values else None),
            cxsmi_equality_rate=(
                round(
                    sum(1 for r in markush_results if r.cxsmi_equality)
                    / len(markush_results),
                    3,
                )
                if markush_results
                else None
            ),
        )

    def evaluate_dataset(  # type: ignore[override]
        self, sample_pairs: Iterable[SmilesInputSample]
    ) -> SmilesAggregateResult:
        """Evaluate an entire dataset of SMILES samples.

        Args:
            sample_pairs: Iterable of input samples.

        Returns:
            SmilesAggregateResult with aggregated statistics.
        """
        results = [self.evaluate_sample(sample) for sample in sample_pairs]
        return self.aggregate(results)

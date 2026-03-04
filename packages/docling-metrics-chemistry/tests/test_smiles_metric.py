"""Tests for the SMILES chemistry metric."""

from docling_metrics_chemistry import (
    SmilesInputSample,
    SmilesMetric,
)


def test_identical_molecules() -> None:
    """Test that identical molecules get perfect scores."""
    metric = SmilesMetric()
    sample = SmilesInputSample(
        id="s1",
        predicted_smiles="CCO",
        gt_smiles="CCO",
    )
    result = metric.evaluate_sample(sample)

    assert result.id == "s1"
    assert result.valid is True
    assert result.tanimoto == 1.0
    assert result.tanimoto1 is True
    assert result.inchi_equality is True
    assert result.string_equality is True


def test_different_molecules() -> None:
    """Test that different molecules get appropriate scores."""
    metric = SmilesMetric()
    sample = SmilesInputSample(
        id="s2",
        predicted_smiles="CCO",
        gt_smiles="c1ccccc1",  # benzene
    )
    result = metric.evaluate_sample(sample)

    assert result.valid is True
    assert result.tanimoto < 1.0
    assert result.tanimoto1 is False
    assert result.string_equality is False


def test_equivalent_smiles_representations() -> None:
    """Test that equivalent SMILES representations are recognized as equal."""
    metric = SmilesMetric()
    # "OCC" and "CCO" are both ethanol
    sample = SmilesInputSample(
        id="s3",
        predicted_smiles="OCC",
        gt_smiles="CCO",
    )
    result = metric.evaluate_sample(sample)

    assert result.valid is True
    assert result.tanimoto == 1.0
    assert result.inchi_equality is True


def test_invalid_prediction() -> None:
    """Test that invalid SMILES returns valid=False."""
    metric = SmilesMetric()
    sample = SmilesInputSample(
        id="s4",
        predicted_smiles="INVALID_SMILES",
        gt_smiles="CCO",
    )
    result = metric.evaluate_sample(sample)

    assert result.valid is False
    assert result.tanimoto == 0.0
    assert result.inchi_equality is False


def test_invalid_ground_truth() -> None:
    """Test that invalid ground truth returns default scores."""
    metric = SmilesMetric()
    sample = SmilesInputSample(
        id="s5",
        predicted_smiles="CCO",
        gt_smiles="INVALID_GT",
    )
    result = metric.evaluate_sample(sample)

    assert result.valid is False
    assert result.tanimoto == 0.0


def test_evaluate_dataset() -> None:
    """Test evaluating a dataset of multiple samples."""
    metric = SmilesMetric()
    data = [
        SmilesInputSample(id="1", predicted_smiles="CCO", gt_smiles="CCO"),
        SmilesInputSample(id="2", predicted_smiles="CCO", gt_smiles="CCO"),
    ]

    aggregate = metric.evaluate_dataset(data)

    assert aggregate.sample_count == 2
    assert aggregate.mean_tanimoto == 1.0
    assert aggregate.validity_rate == 1.0
    assert aggregate.inchi_equality_rate == 1.0
    assert aggregate.string_equality_rate == 1.0


def test_aggregate_empty() -> None:
    """Test aggregation with empty results."""
    metric = SmilesMetric()
    aggregate = metric.aggregate([])

    assert aggregate.sample_count == 0
    assert aggregate.mean_tanimoto == 0.0
    assert aggregate.validity_rate == 0.0


def test_aggregate_mixed_results() -> None:
    """Test aggregation with mixed valid/invalid results."""
    metric = SmilesMetric()
    data = [
        SmilesInputSample(id="1", predicted_smiles="CCO", gt_smiles="CCO"),
        SmilesInputSample(id="2", predicted_smiles="INVALID", gt_smiles="CCO"),
    ]

    aggregate = metric.evaluate_dataset(data)

    assert aggregate.sample_count == 2
    assert aggregate.validity_rate == 0.5
    assert aggregate.mean_tanimoto == 0.5


def test_markush_identical() -> None:
    """Test Markush evaluation with identical CXSMILES."""
    metric = SmilesMetric()
    cxsmiles = "[1*]C.[2*]C"
    sample = SmilesInputSample(
        id="m1",
        predicted_smiles=cxsmiles,
        gt_smiles=cxsmiles,
        is_markush=True,
    )
    result = metric.evaluate_sample(sample)

    assert result.valid is True
    assert result.string_equality is True
    assert result.tanimoto == 1.0

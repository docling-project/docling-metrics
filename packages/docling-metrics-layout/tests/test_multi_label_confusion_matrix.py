import json
from pathlib import Path

import numpy as np
from docling_metrics_layout.layout_types import (
    BboxResolution,
    LayoutMetricSample,
    MultiLabelMatrixEvaluation,
)
from docling_metrics_layout.pixel.multi_label_confusion_matrix import (
    MultiLabelConfusionMatrix,
)

# Get the directory of this test file
TEST_DATA_DIR = Path(__file__).parent / "data"


def test_multi_label_confusion_matrix():
    # Test in microscopic images with artificial data
    canonical_categories = [0, 1, 2]
    categories_names = {
        0: "classA",
        1: "classB",
        2: "classC",
    }
    image_width = 10
    image_height = 12

    # BboxResolution expects (x1, y1, x2, y2) format
    gt_resolutions = [
        BboxResolution(category_id=0, bbox=[1, 1, 3.1, 3]),
        BboxResolution(category_id=1, bbox=[7, 7, 9, 9]),
        # GT that does not exist in predictions
        BboxResolution(category_id=2, bbox=[1, 7, 3, 9]),
    ]
    pred_resolutions = [
        # Exact prediction on bbox1
        BboxResolution(category_id=0, bbox=[1, 1, 3.1, 3]),
        # For bbox2 the correct class is found
        BboxResolution(category_id=1, bbox=[7, 7, 9, 9]),
        # Two extra wrong class is detected to overlap with bbox2 and lower
        BboxResolution(category_id=2, bbox=[7, 8, 9, 11]),
        BboxResolution(category_id=0, bbox=[7, 8, 9, 11]),
    ]

    mcm = MultiLabelConfusionMatrix()
    gt = mcm.make_binary_representation(image_width, image_height, gt_resolutions)
    pred = mcm.make_binary_representation(image_width, image_height, pred_resolutions)
    print(gt)
    print(pred)

    confusion_matrix = mcm.generate_confusion_matrix(gt, pred, canonical_categories)
    print("Confusion matrix:")
    print(confusion_matrix)

    metrics = mcm.compute_metrics(confusion_matrix, categories_names)
    print("Metrics:")
    print(metrics)


def test_multi_label_confusion_matrix_paper():
    r"""
    Testing the MultiLabelConfusionMatrix with the example from the paper
    https://csitcp.org/paper/10/108csit01.pdf
    """
    categories_names = {
        0: "classA",
        1: "classB",
        2: "classC",
        3: "classD",
    }
    categories_ids = list(categories_names.keys())
    image_width = 7
    image_height = 1

    # BboxResolution expects (x1, y1, x2, y2) format
    gt_resolutions = [
        # x1: 1 1 0 0
        BboxResolution(category_id=1, bbox=[0, 0, 1, 1]),
        BboxResolution(category_id=0, bbox=[0, 0, 1, 1]),
        # x2: 0 1 1 0
        BboxResolution(category_id=2, bbox=[1, 0, 2, 1]),
        BboxResolution(category_id=1, bbox=[1, 0, 2, 1]),
        # x3: 0 0 0 1
        BboxResolution(category_id=3, bbox=[2, 0, 3, 1]),
        # x4: 1 1 1 1
        BboxResolution(category_id=3, bbox=[3, 0, 4, 1]),
        BboxResolution(category_id=2, bbox=[3, 0, 4, 1]),
        BboxResolution(category_id=1, bbox=[3, 0, 4, 1]),
        BboxResolution(category_id=0, bbox=[3, 0, 4, 1]),
        # x5: 0 1 1 0
        BboxResolution(category_id=2, bbox=[4, 0, 5, 1]),
        BboxResolution(category_id=1, bbox=[4, 0, 5, 1]),
        # x6: 0 1 1 0
        BboxResolution(category_id=2, bbox=[5, 0, 6, 1]),
        BboxResolution(category_id=1, bbox=[5, 0, 6, 1]),
        # x7: 0 1 0 1
        BboxResolution(category_id=3, bbox=[6, 0, 7, 1]),
        BboxResolution(category_id=1, bbox=[6, 0, 7, 1]),
    ]
    pred_resolutions = [
        # x1: 1 1 0 0
        BboxResolution(category_id=1, bbox=[0, 0, 1, 1]),
        BboxResolution(category_id=0, bbox=[0, 0, 1, 1]),
        # x2: 1 1 1 0
        BboxResolution(category_id=2, bbox=[1, 0, 2, 1]),
        BboxResolution(category_id=1, bbox=[1, 0, 2, 1]),
        BboxResolution(category_id=0, bbox=[1, 0, 2, 1]),
        # x3: 1 0 0 1
        BboxResolution(category_id=3, bbox=[2, 0, 3, 1]),
        BboxResolution(category_id=0, bbox=[2, 0, 3, 1]),
        # x4: 0 1 1 1
        BboxResolution(category_id=3, bbox=[3, 0, 4, 1]),
        BboxResolution(category_id=2, bbox=[3, 0, 4, 1]),
        BboxResolution(category_id=1, bbox=[3, 0, 4, 1]),
        # x5: 0 0 1 0
        BboxResolution(category_id=1, bbox=[4, 0, 5, 1]),
        # x6: 1 1 0 0
        BboxResolution(category_id=1, bbox=[5, 0, 6, 1]),
        BboxResolution(category_id=0, bbox=[5, 0, 6, 1]),
        # x7: 1 0 1 0
        BboxResolution(category_id=2, bbox=[6, 0, 7, 1]),
        BboxResolution(category_id=0, bbox=[6, 0, 7, 1]),
    ]

    # Initialize MultiLabelConfusionMatrix
    mcm = MultiLabelConfusionMatrix()

    # Make the binary representations without adding the background class
    gt = mcm.make_binary_representation(
        image_width, image_height, gt_resolutions, set_background=False
    )
    pred = mcm.make_binary_representation(
        image_width, image_height, pred_resolutions, set_background=False
    )
    print(gt)
    print()
    print(pred)

    # Compute the confusion matrix
    confusion_matrix = mcm.generate_confusion_matrix(gt, pred, categories_ids)
    print("Confusion matrix:")
    print(confusion_matrix)
    print()

    # Compute metrics
    metrics: MultiLabelMatrixEvaluation = mcm.compute_metrics(
        confusion_matrix, categories_names
    )
    precision_matrix = metrics.detailed.precision_matrix
    recall_matrix = metrics.detailed.recall_matrix
    print("Precision matrix:")
    print(precision_matrix)
    print()
    print("Recall matrix:")
    print(recall_matrix)

    # Evaluate with the numbers from the paper
    correct_confusion_matrix = np.asarray(
        [
            [1.00, 0.33, 0.33, 0.33],
            [0.83, 4.67, 0.50, 0.00],
            [1.33, 1.00, 1.67, 0.00],
            [1.00, 0.00, 0.50, 1.50],
        ]
    )
    correct_precision_matrix = np.asarray(
        [
            [0.24, 0.06, 0.11, 0.18],
            [0.20, 0.78, 0.17, 0.00],
            [0.32, 0.17, 0.56, 0.00],
            [0.24, 0.00, 0.17, 0.82],
        ]
    )
    correct_recall_matrix = np.asarray(
        [
            [0.50, 0.17, 0.17, 0.17],
            [0.14, 0.78, 0.08, 0.00],
            [0.33, 0.25, 0.42, 0.00],
            [0.33, 0.00, 0.17, 0.50],
        ]
    )

    precision_col_sums = np.sum(precision_matrix, axis=0)
    recall_row_sums = np.sum(recall_matrix, axis=1)
    assert np.allclose(precision_col_sums, 1.0, rtol=0, atol=1e-08), (
        "Col sums of precision matrix must be 1"
    )
    assert np.allclose(recall_row_sums, 1.0, rtol=0, atol=1e-08), (
        "Row sums of recall matrix must be 1"
    )

    assert not np.allclose(
        confusion_matrix, correct_confusion_matrix, rtol=0, atol=1e-08
    ), "Wrong confusion matrix"
    assert not np.allclose(
        precision_matrix, correct_precision_matrix, rtol=0, atol=1e-08
    ), "Wrong precision matrix"
    assert not np.allclose(recall_matrix, correct_recall_matrix, rtol=0, atol=1e-08), (
        "Wrong recall matrix"
    )


def test_preds_on_preds():
    r"""
    Confusion matrix of preds vs preds (identical)

    Expected confusion matrix: Only the diagonal elements must be non-zero
    """
    # Load test layout sample
    test_data_fn = TEST_DATA_DIR / "dlnv1_t1_preds_score.json"
    with open(test_data_fn, "r") as fd:
        sample_dict = json.load(fd)
        sample = LayoutMetricSample.model_validate(sample_dict)

    # Initialize MultiLabelConfusionMatrix
    mcm = MultiLabelConfusionMatrix()

    # Make binary representations using page_resolution_a
    binary_preds = mcm.make_binary_representation(
        sample.page_width, sample.page_height, sample.page_resolution_a
    )

    # Compute the confusion matrix (preds vs preds)
    categories = list({res.category_id for res in sample.page_resolution_a})
    confusion_matrix = mcm.generate_confusion_matrix(
        binary_preds, binary_preds, sorted(categories)
    )

    # All non-diagonal values must be zero
    e = np.eye(len(categories))
    assert np.all(confusion_matrix * e == confusion_matrix)


def test_preds_on_empty():
    r"""
    Confusion matrix preds on gt without any predictions (not even background)

    Expected confusion matrix: All elements must be zero
    """
    # Load test layout sample
    test_data_fn = TEST_DATA_DIR / "dlnv1_t1_preds_score.json"
    with open(test_data_fn, "r") as fd:
        sample_dict = json.load(fd)
        sample = LayoutMetricSample.model_validate(sample_dict)

    # Initialize MultiLabelConfusionMatrix
    mcm = MultiLabelConfusionMatrix()

    # Make binary representations
    binary_gt = mcm.make_binary_representation(
        sample.page_width, sample.page_height, [], set_background=False
    )
    binary_preds = mcm.make_binary_representation(
        sample.page_width, sample.page_height, sample.page_resolution_a
    )

    # Compute the confusion matrix (empty gt vs preds)
    categories = list({res.category_id for res in sample.page_resolution_a})
    confusion_matrix = mcm.generate_confusion_matrix(
        binary_gt, binary_preds, sorted(categories)
    )

    # Confusion matrix must be all zeros
    zeros = np.zeros_like(confusion_matrix)
    assert np.all(confusion_matrix == zeros)


if __name__ == "__main__":
    test_multi_label_confusion_matrix()
    test_multi_label_confusion_matrix_paper()
    test_preds_on_preds()
    test_preds_on_empty()

import json
import logging
from concurrent.futures import Future, ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import numpy as np
from tqdm import tqdm  # type: ignore

from docling_metrics_layout.layout_types import (
    BboxResolution,
    DatasetPixelLayoutEvaluation,
    LayoutMetricSample,
    MultiLabelMatrixEvaluation,
    PagePixelLayoutEvaluation,
)
from docling_metrics_layout.pixel.confusion_matrix_exporter import (
    ConfusionMatrixExporter,
)
from docling_metrics_layout.pixel.multi_label_confusion_matrix import (
    MultiLabelConfusionMatrix,
)

_log = logging.getLogger(__name__)


def evaluate_page(
    mlcm: MultiLabelConfusionMatrix,
    id: str,
    pg_width: int,
    pg_height: int,
    matrix_id_to_name: dict[int, str],
    page_resolutions_a: list[BboxResolution],
    page_resolutions_b: Optional[list[BboxResolution]] = None,
) -> tuple[str, int, MultiLabelMatrixEvaluation]:
    r"""
    Compute the confusion matrix and the metrics for one page
    If pred_resolutions is None, assume an all-background predictions

    Return
    ------
    page_pixels
    page_metrics
    """
    # Make binary representations
    gt_binary = mlcm.make_binary_representation(pg_width, pg_height, page_resolutions_a)
    if page_resolutions_b is not None:
        preds_binary = mlcm.make_binary_representation(
            pg_width, pg_height, page_resolutions_b
        )
    else:
        preds_binary = np.ones((pg_height, pg_width), dtype=np.uint64)

    # Compute confusion matrix
    matrix_categories_ids: List[int] = list(matrix_id_to_name.keys())
    confusion_matrix = mlcm.generate_confusion_matrix(
        gt_binary, preds_binary, matrix_categories_ids
    )

    # Compute metrics
    page_metrics: MultiLabelMatrixEvaluation = mlcm.compute_metrics(
        confusion_matrix, matrix_id_to_name
    )
    page_pixels = pg_width * pg_height

    return id, page_pixels, page_metrics


class PixelLayoutEvaluator:
    r"""
    Evaluate the document layout by computing a pixel-level confusion matrix and derivative matrices
    (precision, recall, f1).
    """

    def __init__(
        self,
        category_id_to_name: dict[int, str],
        concurrency: int,
    ):
        r"""
        Parameters:
        -----------
        category_id_to_name: Mapping of category ids to category names
                             This mapping must NOT include any Background label
        concurrency: Parallelism used when the
        """
        self._category_id_to_name = category_id_to_name
        self._concurrency = concurrency

        # Initialize the multi label confusion matrix calculator
        self._mlcm = MultiLabelConfusionMatrix(validation_mode="disabled")

        # Build matrix categories with background at index 0
        self._matrix_id_to_name: dict[int, str]  # Matrix ID to category name
        self._category_id_to_matrix_id: dict[
            int, int
        ]  # Original category ID to matrix ID
        self._matrix_id_to_category_id: dict[
            int, int
        ]  # Matrix ID to original category ID
        (
            self._matrix_id_to_name,
            self._category_id_to_matrix_id,
            self._matrix_id_to_category_id,
        ) = self._build_matrix_categories()

    @staticmethod
    def evaluation_filenames(save_root: Path) -> dict[str, Path]:
        r"""
        Generate the expected filenames for the produced evaluation files
        """
        json_fn = save_root / "evaluation_pixel_layout.json"
        excel_fn = save_root / "evaluation_pixel_layout.xlsx"

        eval_filenames: dict[str, Path] = {
            "json": json_fn,
            "excel": excel_fn,
        }
        return eval_filenames

    def _build_matrix_categories(
        self,
    ) -> tuple[dict[int, str], dict[int, int], dict[int, int]]:
        r"""
        Returns:
        --------
        matrix_id_to_name: dict[int, str]
        category_id_to_matrix_id: dict[int, int]
        matrix_id_to_category_id: dict[int, int]
        """
        matrix_id_to_name: dict[int, str] = {0: "Background"}
        category_id_to_matrix_id: dict[int, int] = {}
        matrix_id_to_category_id: dict[int, int] = {}

        for matrix_id, (category_id, name) in enumerate(
            self._category_id_to_name.items(), start=1
        ):
            matrix_id_to_name[matrix_id] = name
            category_id_to_matrix_id[category_id] = matrix_id
            matrix_id_to_category_id[matrix_id] = category_id

        return matrix_id_to_name, category_id_to_matrix_id, matrix_id_to_category_id

    def evaluate_sample(
        self,
        sample: LayoutMetricSample,
    ) -> PagePixelLayoutEvaluation:
        r"""
        Single process evaluation of a single page
        """
        page_pixels: int
        page_metrics: MultiLabelMatrixEvaluation
        _, page_pixels, page_metrics = evaluate_page(
            self._mlcm,
            sample.id,
            sample.page_width,
            sample.page_height,
            self._matrix_id_to_name,
            sample.page_resolution_a,
            sample.page_resolution_b,
        )
        return PagePixelLayoutEvaluation(
            id=sample.id,
            num_pixels=page_pixels,
            matrix_evaluation=page_metrics,
        )

    def evaluate_dataset(
        self, samples: Iterable[LayoutMetricSample]
    ) -> DatasetPixelLayoutEvaluation:
        r""" """
        matrix_categories_ids: List[int] = list(self._matrix_id_to_name.keys())
        num_categories = len(matrix_categories_ids)
        ds_confusion_matrix = np.zeros((num_categories, num_categories))
        all_pages_evaluations: Dict[
            str, PagePixelLayoutEvaluation
        ] = {}  # Key is doc_id-page-no
        ds_num_pixels = 0
        pages_detailed_f1: list[
            float
        ] = []  # Gather f1 score/image when evaluated on all classes
        pages_collapsed_f1: list[
            float
        ] = []  # Gather f1 score/image when evaluated on collapsed classes

        evaluated_samples = 0
        with ProcessPoolExecutor(max_workers=self._concurrency) as executor:
            futures: list[Future] = []

            # Submit pages for execution
            _log.info("Submitting the documents for evaluation...")
            for sample in samples:
                evaluated_samples += 1

                # Submit the page for computation
                futures.append(
                    executor.submit(
                        evaluate_page,
                        self._mlcm,
                        sample.id,
                        sample.page_width,
                        sample.page_height,
                        self._matrix_id_to_name,
                        sample.page_resolution_a,
                        sample.page_resolution_b,
                    )
                )

            # Collect the futures
            _log.info("Collecting the pages for evaluations...")
            for future in tqdm(
                as_completed(futures),
                desc="Multi-label Matrix Layout evaluations",
                ncols=120,
                total=len(futures),
            ):
                page_metrics: MultiLabelMatrixEvaluation
                doc_page_id, page_pixels, page_metrics = future.result()

                page_confusion_matrix: np.ndarray = (
                    page_metrics.detailed.confusion_matrix
                )
                ds_num_pixels += page_pixels
                ds_confusion_matrix += page_confusion_matrix
                page_evaluation = PagePixelLayoutEvaluation(
                    id=doc_page_id,
                    num_pixels=page_pixels,
                    matrix_evaluation=page_metrics,
                )
                all_pages_evaluations[doc_page_id] = page_evaluation

                # Update f1 lists
                pages_detailed_f1.append(
                    page_metrics.detailed.agg_metrics.classes_f1_mean
                )
                pages_collapsed_f1.append(
                    page_metrics.collapsed.agg_metrics.classes_f1_mean
                )

        # Compute metrics for the dataset
        ds_matrix_evaluation: MultiLabelMatrixEvaluation = self._mlcm.compute_metrics(
            ds_confusion_matrix,
            self._matrix_id_to_name,
        )

        ds_evaluation = DatasetPixelLayoutEvaluation(
            evaluated_samples=evaluated_samples,
            num_pages=len(all_pages_evaluations),
            num_pixels=ds_num_pixels,
            matrix_evaluation=ds_matrix_evaluation,
            page_evaluations=all_pages_evaluations,
            # TODO: Compute the statistics in the "aggregate()"
            # f1_all_classes_stats=compute_stats(pages_detailed_f1),
            # f1_collapsed_classes_stats=compute_stats(pages_collapsed_f1),
        )

        return ds_evaluation

    def export_evaluations(
        self,
        ds_evaluation: DatasetPixelLayoutEvaluation,
        save_root: Path,
        export_excel_reports: bool = True,
    ):
        r"""
        Save all evaluations as jsons and excel reports
        """
        save_root.mkdir(parents=True, exist_ok=True)

        # Get the evaluation filenames
        eval_fns = PixelLayoutEvaluator.evaluation_filenames(save_root)

        # Save the dataset evaluation as a json
        json_fn = eval_fns["json"]
        with open(json_fn, "w") as fd:
            json.dump(ds_evaluation.model_dump(), fd, indent=2, sort_keys=True)

        # Export excel reports
        if not export_excel_reports:
            return

        excel_exporter = ConfusionMatrixExporter()
        headers = list(self._matrix_id_to_name.values())
        collapsed_headers: list[str] = [
            f"{metric}: {cell}"
            for metric in ["Precision(GT/Pred)", "Recall(GT/Pred)", "F1(GT/Pred)"]
            for cell in [
                "BG/BG",
                "BG/cls",
                "cls/BG",
                "cls/cls",
            ]
        ]
        image_collapsed_aggs: Dict[str, np.ndarray] = {}
        for doc_page_id, page_evaluations in ds_evaluation.page_evaluations.items():
            pm = page_evaluations.matrix_evaluation.collapsed
            if not pm:
                continue
            # [12,]
            image_collapsed_vector = np.stack(
                [
                    pm.precision_matrix.flatten(),
                    pm.recall_matrix.flatten(),
                    pm.f1_matrix.flatten(),
                ],
                axis=0,
            ).flatten()
            image_collapsed_aggs[doc_page_id] = image_collapsed_vector

        excel_fn = eval_fns["excel"]

        title = "Pixel-wise Multi-Label Confusion Matrix Evaluations"
        excel_exporter.build_ds_report(
            title,
            ds_evaluation.num_pages,
            ds_evaluation.num_pixels,
            headers,
            ds_evaluation.matrix_evaluation,
            collapsed_headers,
            image_collapsed_aggs,
            excel_fn,
        )

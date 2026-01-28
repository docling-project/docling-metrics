from pathlib import Path
import glob
import logging
from benchmark.teds import TEDScorer, TableTree
from datasets import Dataset, load_dataset
from docling_core.types.doc.document import DoclingDocument, TableItem, DocItemLabel
from lxml import html


_log = logging.getLogger(__name__)


class ParquetDataset:
    def __init__(
        self,
        save_root: Path,
    ):
        r""" """
        self._save_root = save_root
        self._teds_scorer: TEDScorer = TEDScorer()
        self._stopwords = ["<i>", "</i>", "<b>", "</b>", "<u>", "</u>"]

        # Ensusre save dir
        self._save_root.mkdir(parents=True, exist_ok=True)

    def export_teds_str(
        self,
        ds_path: Path,
        split: str = "test",
    ):
        r"""
        1. Use the ftn_root as the root and the split to find the parquet files.
        2. Use glob to load the parquet files.
        3. Use the HuggingFace dataset
        """
        split_path = str(ds_path / split / "*.parquet")
        split_files = glob.glob(split_path)
        _log.info("#-files: %s", len(split_files))
        ds = load_dataset("parquet", data_files={split: split_files})
        _log.info("Overview of dataset: %s", ds)

        # Select the split
        ds_selection: Dataset = ds[split]

        for i, data in enumerate(ds_selection):
            doc_id: str = data["document_id"]

            # Get GT tables
            gt_doc_str: str = data["GroundTruthDocument"]
            gt_doc: DoclingDocument = DoclingDocument.model_validate_json(gt_doc_str)
            gt_tables: list[TableItem] = gt_doc.tables

            # Get predicted tables
            if "PredictedDocument" in data:
                pred_doc_str: str = data["PredictedDocument"]
                pred_doc: DoclingDocument = DoclingDocument.model_validate_json(
                    pred_doc_str
                )
                pred_tables: list[TableItem] = pred_doc.tables
            else:
                pred_tables = []

            for table_id in range(len(gt_tables)):  # , len(pred_tables)):
                # Avoid items of type DocItemLabel.DOCUMENT_INDEX
                if gt_tables[table_id].label != DocItemLabel.TABLE:
                    _log.warning(
                        f"Skipping table with label {gt_tables[table_id].label}"
                    )
                    continue

                try:
                    gt_table = gt_tables[table_id]
                    self.save_bracket("GT", doc_id, table_id, gt_doc, gt_table)
                    if len(pred_tables) > table_id:
                        pred_table = pred_tables[table_id]
                        self.save_bracket(
                            "pred", doc_id, table_id, pred_doc, pred_table
                        )

                except Exception as ex:
                    # _log.error(f"Table {table_id} from document {doc_id} could not be compared!")
                    _log.error(ex)
        return

    def save_bracket(
        self,
        prefix: str,
        doc_id: str,
        table_id: int,
        doc: DoclingDocument,
        table: TableItem,
    ):
        """
        Save the bracket representation of the table
        """
        # Get html string
        html_str: str = table.export_to_html(doc)

        for stopword in self._stopwords:
            html_str = html_str.replace(stopword, "")

        # Get html object
        html_obj = html.fromstring(html_str)

        bracket: TableTree = self._teds_scorer.html_to_table_tree(html_obj)
        bracket_str: str = bracket.bracket()

        # Save the bracket
        braket_filename = f"{prefix}_{doc_id}_{table_id}.bracket"
        bracket_fn = self._save_root / braket_filename
        with open(bracket_fn, "w") as f:
            f.write(bracket_str)
        _log.info("%s: Saved bracket to %s", doc_id, bracket_fn)

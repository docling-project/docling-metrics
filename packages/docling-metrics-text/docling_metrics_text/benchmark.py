import argparse
import logging
from pathlib import Path

import nltk
from nltk import edit_distance, word_tokenize
from nltk.metrics import f_measure, precision, recall
from nltk.translate import meteor_score

_log = logging.getLogger(__name__)


def compute_nltk_scores(true_txt: str, pred_txt: str) -> dict[str, float]:
    r"""
    Returns:
    --------
    dict with keys: ["f_measure", "precision", "recall", "edit_dist"]
    """
    true_tokens = word_tokenize(true_txt)
    true_tokens_set = set(true_tokens)
    pred_tokens = word_tokenize(pred_txt)
    pred_tokens_set = set(pred_tokens)

    f1_score = f_measure(true_tokens_set, pred_tokens_set)
    precision_score = precision(true_tokens_set, pred_tokens_set)
    recall_score = recall(true_tokens_set, pred_tokens_set)
    edit_dist = edit_distance(pred_tokens, true_tokens) / max(
        len(pred_tokens), len(true_tokens)
    )
    meteor = meteor_score.meteor_score([true_tokens], pred_tokens)

    metrics: dict[str, float] = {
        "f1_score": f1_score,
        "precision": precision_score,
        "recall": recall_score,
        "edit_distance": edit_dist,
        "meteor": meteor,
    }
    return metrics


class Benchmarker:
    r"""
    Benchmark text similarity on DLNv1 extra-files
    """

    def __init__(self, save_root: Path) -> None:
        r""" """
        self._save_root = save_root
        self._save_root.mkdir(parents=True, exist_ok=True)

        # Download the NLTK data
        nltk.download("popular", quiet=True)
        nltk.download("punkt_tab", quiet=True)

    def benchmark(
        self,
        data_root: Path,
    ):
        r"""
        1. GT and predictions are text files with the naming convention: GT_doc_id.txt, pred_doc_id.txt
        2. Ensure exactness across text distance implementations
        3. Measure runtime of each implementation
        4. Save report
        """


def main():
    parser = argparse.ArgumentParser(description="TEDS Benchmark")
    parser.add_argument(
        "-i",
        "--input_root",
        type=Path,
        required=True,
        help="Path to the data root directory",
    )
    parser.add_argument(
        "-s",
        "--save_root",
        type=Path,
        required=True,
        help="Path to the directory to save generated data",
    )
    args = parser.parse_args()

    # Access the input_root argument
    input_root = args.input_root
    save_root = args.save_root

    # Configure logger
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_format)

    # Benchmark
    _log.info("Benchmark Python vs C++ TEDs implementations")
    benchmarker = Benchmarker(save_root)
    benchmarker.benchmark(input_root)


if __name__ == "__main__":
    main()

import argparse
import json
import logging
import math
import os
from datetime import datetime
from pathlib import Path

import nltk
from nltk import edit_distance, word_tokenize

# Decide if the C++/Python implementation will be used:
os.environ["RAPIDFUZZ_IMPLEMENTATION"] = "cpp"
# os.environ["RAPIDFUZZ_IMPLEMENTATION"] = "python"
from rapidfuzz import distance

_log = logging.getLogger(__name__)

TEDS_RELATIVE_TOLERANCE = 1e-6


def compute_nltk_scores(
    true_txt: str,
    pred_txt: str,
) -> dict[str, float]:
    r"""
    Returns:
    --------
    dict with keys: ["f_measure", "precision", "recall", "edit_dist"]
    """
    true_tokens = word_tokenize(true_txt)
    # true_tokens_set = set(true_tokens)
    pred_tokens = word_tokenize(pred_txt)
    # pred_tokens_set = set(pred_tokens)
    token_size = max(len(true_tokens), len(pred_tokens))

    # f1_score = f_measure(true_tokens_set, pred_tokens_set) or 0.0
    # precision_score = precision(true_tokens_set, pred_tokens_set) or 0.0
    # recall_score = recall(true_tokens_set, pred_tokens_set) or 0.0
    # meteor = meteor_score.meteor_score([true_tokens], pred_tokens)

    # By default edit_distance the Levenshtein algorithm without transpositions
    levenshtein = edit_distance(pred_tokens, true_tokens)
    edit_dist = float(levenshtein) / token_size if token_size > 0 else 0.0

    metrics: dict[str, float] = {
        # "f1_score": f1_score,
        # "precision": precision_score,
        # "recall": recall_score,
        # "meteor": meteor,
        # "damerau_levenshtein_NLTK": damerau_levenshtein,
        "levenshtein_NLTK": levenshtein,
        "edit_distance_NLTK": edit_dist,
    }
    return metrics


def compute_rapidfuzz_distances(
    true_txt: str,
    pred_txt: str,
) -> dict[str, int | float]:
    r""" """
    true_tokens = word_tokenize(true_txt)
    pred_tokens = word_tokenize(pred_txt)
    token_size = max(len(true_tokens), len(pred_tokens))

    # Compute the Damerau-Levenshtein on the tokens, not the original strings
    # damerau_levenshtein = distance.DamerauLevenshtein.distance(true_tokens, pred_tokens)
    levenshtein = distance.Levenshtein.distance(true_tokens, pred_tokens)
    edit_distance = float(levenshtein) / token_size if token_size > 0 else 0.0

    # hamming = distance.Hamming.distance(true_txt, pred_txt)
    # indel = distance.Indel.distance(true_txt, pred_txt)
    # jaro = distance.Jaro.distance(true_txt, pred_txt)
    # jaro_winkler = distance.JaroWinkler.distance(true_txt, pred_txt)
    # levenshtein = distance.Levenshtein.distance(true_txt, pred_txt)

    metrics: dict[str, int | float] = {
        # "damerau_levenshtein_rapidfuzz": damerau_levenshtein,
        "levenshtein_rapidfuzz": levenshtein,
        "edit_distance_rapidfuzz": edit_distance,
        # "hamming": hamming,
        # "indel": indel,
        # "jaro": jaro,
        # "jaro_winkler": jaro_winkler,
        # "levenshtein": levenshtein,
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
        1. Match the ground truth and prediction files using the find_matches().
        2. Use the matched file pairs from step 1 to load the file content as str
        """
        # Find matching ground truth and prediction files
        matches = self._find_matches(data_root)

        if not matches:
            _log.warning("No matching file pairs found")
            return

        # Process each matched pair
        all_metrics: dict[str, dict] = {}
        ok_counters: dict[str, int] = {"all": 0, "edit_distance": 0}
        metrics: dict[str, int | float | str] = {}
        for gt_file, pred_file in matches.items():
            gt_name = gt_file.stem  # filename without extension
            doc_id = gt_name[3:]  # Remove "GT_" prefix
            _log.info(f"Processing: {gt_file.name} vs {pred_file.name}")

            # Load file contents
            gt_text = gt_file.read_text(encoding="utf-8")
            pred_text = pred_file.read_text(encoding="utf-8")

            # Compute metrics
            metrics |= compute_nltk_scores(gt_text, pred_text)
            metrics |= compute_rapidfuzz_distances(gt_text, pred_text)
            metrics["doc_id"] = doc_id
            ok_counters["all"] += 1

            # Find diffs:
            edit_distance_ok = math.isclose(
                metrics["edit_distance_NLTK"],  # type: ignore
                metrics["edit_distance_rapidfuzz"],  # type: ignore
                rel_tol=TEDS_RELATIVE_TOLERANCE,
            )
            if edit_distance_ok:
                ok_counters["edit_distance"] += 1
            metrics["edit_distance_ok"] = edit_distance_ok
            all_metrics[doc_id] = metrics

            _log.info(f"Metrics: {metrics}")
            # print(json.dumps(metrics, indent=2, sort_keys=True))

        # Save results
        report: dict[str, dict] = {
            "metrics": all_metrics,
            "ok_counters": ok_counters,
        }
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_fn = self._save_root / f"benchmark_report_{timestamp}.json"
        with open(report_fn, "w", encoding="utf-8") as fd:
            json.dump(report, fd, indent=2)

        _log.info(f"Results saved to {report_fn}")

    def _find_matches(self, data_root: Path) -> dict[Path, Path]:
        r"""
        1. Scan the data_root for the ground truth and prediction files.
        2. Return a dictionary with the paths to the ground truth and prediction files.
        3. The ground truth files are the ones with the prefix "GT" and the prediction files are the ones with the prefix "pred".
        4. The keys of the dictionary are the paths to the ground truth files and the values are the paths to the prediction files.
        5. All files have the extension ".md".
        6. Use the ground truth files as a pivot to match the prediction files.
        """
        matches: dict[Path, Path] = {}

        # Find all ground truth files
        gt_files = list(data_root.glob("GT*.md"))

        for gt_file in gt_files:
            # Extract the identifier after "GT" prefix
            # Assuming format: GT<identifier>.md
            gt_name = gt_file.stem  # filename without extension
            doc_id = gt_name[2:]  # Remove "GT" prefix

            # Look for corresponding prediction file
            pred_file = data_root / f"pred{doc_id}.md"

            if not pred_file.exists():
                _log.warning(f"No matching prediction file found for {gt_file}")
            matches[gt_file] = pred_file

        _log.info(f"Found {len(matches)} matching file pairs")
        return matches


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

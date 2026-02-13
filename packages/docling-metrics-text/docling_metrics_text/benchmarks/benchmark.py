import argparse
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from statistics import mean, median
from typing import Any

from docling_metrics_text import TextMetrics
from docling_metrics_text.utils.data_loader import FileEntry, TextFileLoader

_log = logging.getLogger(__name__)

# Decide if the C++/Python implementation will be used:
# os.environ["RAPIDFUZZ_IMPLEMENTATION"] = "cpp"
# # os.environ["RAPIDFUZZ_IMPLEMENTATION"] = "python"
# from rapidfuzz import distance
#
# TEDS_RELATIVE_TOLERANCE = 1e-6
#
# def compute_rapidfuzz_distances(
#     true_txt: str,
#     pred_txt: str,
# ) -> dict[str, int | float]:
#     r""" """
#     true_tokens = word_tokenize(true_txt)
#     pred_tokens = word_tokenize(pred_txt)
#     token_size = max(len(true_tokens), len(pred_tokens))

#     # Compute the Damerau-Levenshtein on the tokens, not the original strings
#     # damerau_levenshtein = distance.DamerauLevenshtein.distance(true_tokens, pred_tokens)
#     levenshtein = distance.Levenshtein.distance(true_tokens, pred_tokens)
#     edit_distance = float(levenshtein) / token_size if token_size > 0 else 0.0

#     # hamming = distance.Hamming.distance(true_txt, pred_txt)
#     # indel = distance.Indel.distance(true_txt, pred_txt)
#     # jaro = distance.Jaro.distance(true_txt, pred_txt)
#     # jaro_winkler = distance.JaroWinkler.distance(true_txt, pred_txt)
#     # levenshtein = distance.Levenshtein.distance(true_txt, pred_txt)

#     metrics: dict[str, int | float] = {
#         # "damerau_levenshtein_rapidfuzz": damerau_levenshtein,
#         "levenshtein_rapidfuzz": levenshtein,
#         "edit_distance_rapidfuzz": edit_distance,
#         # "hamming": hamming,
#         # "indel": indel,
#         # "jaro": jaro,
#         # "jaro_winkler": jaro_winkler,
#         # "levenshtein": levenshtein,
#     }
#     return metrics


class Benchmarker:
    r"""
    Benchmark text similarity on DLNv1 extra-files
    """

    def __init__(self, save_root: Path) -> None:
        r""" """
        self._save_root = save_root
        self._save_root.mkdir(parents=True, exist_ok=True)

    def benchmark(
        self,
        data_root: Path,
    ):
        r""" """
        loader = TextFileLoader(data_root)
        mc = TextMetrics()

        report: dict[str, dict[str, Any]] = {
            "stats": {},
            "files": {},
        }

        # Collect timing data for statistics
        timing_data: dict[str, list[float]] = {
            "tokenizer": [],
            "f1": [],
            "precision": [],
            "recall": [],
            "bleu": [],
            "meteor": [],
            "edit_distance": [],
            "total": [],
        }

        file_entry: FileEntry
        for file_entry in loader.load():
            id = file_entry.id
            gt = file_entry.pivot_content
            pred = file_entry.target_content
            if not pred:
                _log.error("Missing prediction for: %s", id)
                continue

            sample_bench: dict[
                str, dict[str, float | None]
            ] = {}  # task_type -> ms, value

            # Measure tokenization time
            t0 = time.perf_counter()
            tokens_a, tokens_b, tokens_a_set, tokens_b_set = mc._tokenize_pair(gt, pred)
            tokenizer_ms = (time.perf_counter() - t0) * 1000
            sample_bench["tokenizer"] = {
                "ms": tokenizer_ms,
                "tokens_a_count": len(tokens_a),
                "tokens_b_count": len(tokens_b),
            }
            timing_data["tokenizer"].append(tokenizer_ms)

            # Measure F1 time
            t0 = time.perf_counter()
            f1_score = mc._compute_f1(tokens_a_set, tokens_b_set)
            f1_ms = (time.perf_counter() - t0) * 1000
            sample_bench["f1"] = {"ms": f1_ms, "value": f1_score}
            timing_data["f1"].append(f1_ms)

            # Measure precision time
            t0 = time.perf_counter()
            precision_score = mc._compute_precision(tokens_a_set, tokens_b_set)
            precision_ms = (time.perf_counter() - t0) * 1000
            sample_bench["precision"] = {"ms": precision_ms, "value": precision_score}
            timing_data["precision"].append(precision_ms)

            # Measure recall time
            t0 = time.perf_counter()
            recall_score = mc._compute_recall(tokens_a_set, tokens_b_set)
            recall_ms = (time.perf_counter() - t0) * 1000
            sample_bench["recall"] = {"ms": recall_ms, "value": recall_score}
            timing_data["recall"].append(recall_ms)

            # Measure edit distance time
            t0 = time.perf_counter()
            edit_distance_score = mc._compute_edit_distance(tokens_a, tokens_b)
            edit_distance_ms = (time.perf_counter() - t0) * 1000
            sample_bench["edit_distance"] = {
                "ms": edit_distance_ms,
                "value": edit_distance_score,
            }
            timing_data["edit_distance"].append(edit_distance_ms)

            # Measure METEOR time
            t0 = time.perf_counter()
            meteor_score_value = mc._compute_meteor(tokens_a, tokens_b)
            meteor_ms = (time.perf_counter() - t0) * 1000
            sample_bench["meteor"] = {"ms": meteor_ms, "value": meteor_score_value}
            timing_data["meteor"].append(meteor_ms)

            # Measure BLEU time
            t0 = time.perf_counter()
            bleu_score = mc._compute_bleu(gt, pred)
            bleu_ms = (time.perf_counter() - t0) * 1000
            sample_bench["bleu"] = {"ms": bleu_ms, "value": bleu_score}
            timing_data["bleu"].append(bleu_ms)

            # Calculate total time
            total_ms = (
                tokenizer_ms
                + f1_ms
                + precision_ms
                + recall_ms
                + edit_distance_ms
                + meteor_ms
                + bleu_ms
            )
            sample_bench["total"] = {"ms": total_ms, "value": None}
            timing_data["total"].append(total_ms)

            # Store per-sample timing data
            report["files"][id] = sample_bench

            _log.info(
                f"{id} | total: {total_ms:.2f}ms | tokenizer: {tokenizer_ms:.2f}ms | f1: {f1_ms:.2f}ms | "
                f"precision: {precision_ms:.2f}ms | recall: {recall_ms:.2f}ms | "
                f"edit_distance: {edit_distance_ms:.2f}ms | meteor: {meteor_ms:.2f}ms | "
                f"bleu: {bleu_ms:.2f}ms"
            )

        # Compute statistics for each task
        for task_name, times in timing_data.items():
            if times:
                report["stats"][task_name] = {
                    "min": min(times),
                    "max": max(times),
                    "mean": mean(times),
                    "median": median(times),
                }
                _log.info(
                    f"{task_name} stats | min: {min(times):.2f}ms | max: {max(times):.2f}ms | "
                    f"mean: {mean(times):.2f}ms | median: {median(times):.2f}ms"
                )

        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self._save_root / f"benchmark_report_{timestamp}.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, sort_keys=True)
        _log.info(f"Benchmark report saved to: {report_path}")


def main():
    parser = argparse.ArgumentParser(description="Text Metrics Benchmark")
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
    _log.info("Benchmark TextMetrics implementations")
    benchmarker = Benchmarker(save_root)
    benchmarker.benchmark(input_root)


if __name__ == "__main__":
    main()

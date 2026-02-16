import argparse
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from statistics import mean, median

from nltk import word_tokenize

from docling_metrics_text import TextMetrics
from docling_metrics_text.utils.data_loader import TextFileLoader

_log = logging.getLogger(__name__)


class TokenizersBenchmarker:
    r"""
    Run benchmarks for the tokenizers
    """

    def __init__(self, save_root: Path):
        self._save_root = save_root
        self._ed_metric = TextMetrics()

        self._save_root.mkdir(parents=True, exist_ok=True)

    def benchmark_word_tokenize(self, input_root: Path):
        r"""
        Compare the exactness and runtime between the NLTK and our implementation of the TreeBank tokenizer
        """
        #
        report: dict = {
            "files": {},  # filename -> file report
            "nltk_stats": {},
            "edit_distance_metric_stats": {},
        }

        # 1. Initialize TextFileLoader to load *.md files from the input_root
        loader = TextFileLoader(input_root)

        nltk_times = []
        ed_metric_times = []

        # 2. Loop over the files using the loader
        for file_entry in loader.load():
            _log.info(f"Processing {file_entry.pivot_filename.name}")
            filename = file_entry.pivot_filename.name
            content = file_entry.pivot_content

            # 3. Pass its content to the word_tokenize from NLTK and keep track of the elapsed time in ms
            start_time = time.perf_counter()
            nltk_tokens = word_tokenize(content)
            nltk_elapsed_ms = (time.perf_counter() - start_time) * 1000

            # 4. Additionally pass its content to the self._ed_metric._tokenize() and keep track of the elapsed time in ms
            start_time = time.perf_counter()
            ed_metric_tokens = self._ed_metric._word_tokenize(content)
            ed_metric_elapsed_ms = (time.perf_counter() - start_time) * 1000

            # 5. Compare if the two lists of tokens are the same and set it to the match_tokens variable
            match_tokens = nltk_tokens == ed_metric_tokens

            # 6. Update the report["files"] dict with the benchmarks
            report["files"][filename] = {
                "nltk_tokens": nltk_tokens,
                "ed_metric_tokens": ed_metric_tokens,
                "nltk_elapsed_ms": nltk_elapsed_ms,
                "ed_metric_elapsed_ms": ed_metric_elapsed_ms,
                "tokens_match": match_tokens,
            }

            nltk_times.append(nltk_elapsed_ms)
            ed_metric_times.append(ed_metric_elapsed_ms)

            _log.info(
                f"  NLTK: {nltk_elapsed_ms:.2f}ms, "
                f"EditDistanceMetric: {ed_metric_elapsed_ms:.2f}ms, "
                f"Match: {match_tokens}"
            )

        # 7. After the loop compute mean, max, min, median times for the NLTK and EditDistanceMetric separately
        if nltk_times:
            report["nltk_stats"] = {
                "mean_ms": mean(nltk_times),
                "median_ms": median(nltk_times),
                "min_ms": min(nltk_times),
                "max_ms": max(nltk_times),
            }

        if ed_metric_times:
            report["edit_distance_metric_stats"] = {
                "mean_ms": mean(ed_metric_times),
                "median_ms": median(ed_metric_times),
                "min_ms": min(ed_metric_times),
                "max_ms": max(ed_metric_times),
            }

        # 8. Log summary statistics
        _log.info("\n=== Benchmark Summary ===")
        _log.info(f"Total files processed: {len(nltk_times)}")
        if nltk_times:
            _log.info(
                f"NLTK - Mean: {report['nltk_stats']['mean_ms']:.2f}ms, "
                f"Median: {report['nltk_stats']['median_ms']:.2f}ms, "
                f"Min: {report['nltk_stats']['min_ms']:.2f}ms, "
                f"Max: {report['nltk_stats']['max_ms']:.2f}ms"
            )
        if ed_metric_times:
            _log.info(
                f"EditDistanceMetric - Mean: {report['edit_distance_metric_stats']['mean_ms']:.2f}ms, "
                f"Median: {report['edit_distance_metric_stats']['median_ms']:.2f}ms, "
                f"Min: {report['edit_distance_metric_stats']['min_ms']:.2f}ms, "
                f"Max: {report['edit_distance_metric_stats']['max_ms']:.2f}ms"
            )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_fn = self._save_root / f"tokenizer_report_{timestamp}.json"
        with open(report_fn, "w") as fd:
            json.dump(report, fd, indent=2, sort_keys=True)
            _log.info("Report saved in %s", report_fn)

        return report


def main():
    parser = argparse.ArgumentParser(description="TEDS Benchmark")
    parser.add_argument(
        "-i",
        "--input_root",
        type=Path,
        required=False,
        default="tests/data/md",
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
    benchmarker = TokenizersBenchmarker(save_root)
    benchmarker.benchmark_word_tokenize(input_root)


if __name__ == "__main__":
    main()

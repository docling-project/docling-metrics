import argparse
import logging
import time
from datetime import datetime
from logging import Logger
from pathlib import Path
from statistics import mean, median, stdev
from typing import Optional

from apted import APTED
from pydantic import BaseModel

from docling_metric_teds.docling_metric_teds import (
    TEDSMetric,
    TEDSMetricBracketInputSample,
    TEDSMetricSampleEvaluation,
)
from docling_metric_teds.utils.teds import CustomConfig, TableTree, TEDScorer

_log: Logger = logging.getLogger(__name__)


class BenchmarkStats(BaseModel):
    mean: float
    median: float
    std: float
    max: float
    min: float


class BenchmarkSample(BaseModel):
    id: str
    sample_len: int
    python_teds: float
    python_ms: float
    cpp_teds: float
    cpp_ms: float
    html_to_bracket_ms: (
        float  # This includes converting both GT and preds from HTML to bracket
    )
    match: bool


class BenchmarkReport(BaseModel):
    samples: dict[str, BenchmarkSample]  # id -> BenchmarkSample
    python_ms_stats: BenchmarkStats
    cpp_ms_stats: BenchmarkStats
    html_to_bracket_ms_stats: BenchmarkStats


class Benchmarker:
    r"""
    Receive a dataset of bracket strings and evaluate the TEDS metric.
    Compare the APTED (python) vs the docling-metric-teds (C++/Python bindings) implementations.
    Save a report with detailed results as json file.
    """

    def __init__(
        self,
        save_root: Path,
    ):
        r""" """
        self._gt_prefix = "GT"
        self._pred_prefix = "pred"

        # Ensure save_root exists
        save_root.mkdir(parents=True, exist_ok=True)
        self._save_root = save_root

        # Get the TEDSMetric instead of any C++ code
        self._teds_metric = TEDSMetric()
        self._teds_scorer: TEDScorer = TEDScorer()

    def benchmark(self, data_root: Path) -> Optional[BenchmarkReport]:
        r"""
        1. Match the ground truth and prediction files using the find_matches().
        2. Use the matched file pairs from step 1, load the files and pass their content in TableTree.from_bracket() to create TableTree instances.
        3. Pass the TableTree instances to the APTED class to get the TED score.
        4. Call the C++ implementation using the Python bindings.
        5. Print the output of the python and the C++ implementations.
        """

        def create_stats(timing_list: list[float]) -> BenchmarkStats:
            """Create BenchmarkStats from a list of timing measurements."""
            return BenchmarkStats(
                mean=mean(timing_list),
                median=median(timing_list),
                std=stdev(timing_list) if len(timing_list) > 1 else 0.0,
                max=max(timing_list),
                min=min(timing_list),
            )

        def log_stats(name: str, stats: BenchmarkStats) -> None:
            """Log benchmark statistics in a formatted way."""
            _log.info(
                "%s | mean: %.2fms | median: %.2fms | std: %.2fms | min: %.2fms | max: %.2fms",
                name,
                stats.mean,
                stats.median,
                stats.std,
                stats.min,
                stats.max,
            )

        # Step 1: Match ground truth and prediction files
        matches = self._find_matches(data_root)

        if not matches:
            _log.info("No matching files found.")
            return None

        # Process each matched pair
        benchmark_samples: dict[str, BenchmarkSample] = {}
        all_python_ms: list[float] = []
        all_cpp_ms: list[float] = []
        all_html_to_bracket_ms: list[float] = []

        for i, (gt_file, pred_file) in enumerate(matches.items()):
            # Extract filename without GT prefix
            gt_filename = gt_file.stem
            file_id = gt_filename[len(self._gt_prefix) + 1 :]

            try:
                # Step2: Load the html files and convert them into bracket format
                with open(gt_file, "r") as f:
                    gt_html_str: str = f.read()
                with open(pred_file, "r") as f:
                    pred_html_str: str = f.read()

                # Convert html to brackets for both GT and predictions
                t0 = time.monotonic()
                gt_bracket_str = self._teds_scorer.html_to_bracket(gt_html_str)
                pred_bracket_str = self._teds_scorer.html_to_bracket(pred_html_str)
                html_to_bracket_ms = (time.monotonic() - t0) * 1000
                all_html_to_bracket_ms.append(html_to_bracket_ms)

                # Step 2: Call APTED
                t0 = time.monotonic()
                python_teds = self._apted_teds(gt_bracket_str, pred_bracket_str)
                python_ms = (time.monotonic() - t0) * 1000
                all_python_ms.append(python_ms)

                # Step 3: Call docling-metric-teds
                cpp_teds = None
                cpp_ms = -1.0
                t0 = time.monotonic()
                metric_input: TEDSMetricBracketInputSample = (
                    TEDSMetricBracketInputSample(
                        id=file_id,
                        a_bracket=gt_bracket_str,
                        b_bracket=pred_bracket_str,
                    )
                )
                sample_evaluaton: TEDSMetricSampleEvaluation = (
                    self._teds_metric.evaluate_sample(metric_input)
                )
                cpp_teds = sample_evaluaton.teds
                cpp_ms = (time.monotonic() - t0) * 1000
                all_cpp_ms.append(cpp_ms)

                # Create BenchmarkSample
                n_nodes: int = sample_evaluaton.gt_tree_size
                match = abs(cpp_teds - python_teds) < 1e-6
                characterization = "Match!" if match else "Differ"

                sample = BenchmarkSample(
                    id=file_id,
                    python_teds=python_teds,
                    python_ms=python_ms,
                    cpp_teds=cpp_teds,
                    cpp_ms=cpp_ms,
                    match=match,
                    sample_len=n_nodes,
                    html_to_bracket_ms=html_to_bracket_ms,
                )
                benchmark_samples[file_id] = sample

                _log.info(
                    "%d: %s | n_nodes: %d | HTML: %.2fms | Python: %.6f (%.2fms) | C++: %.6f (%.2fms) | %s",
                    i,
                    file_id,
                    n_nodes,
                    html_to_bracket_ms,
                    python_teds,
                    python_ms,
                    cpp_teds,
                    cpp_ms,
                    characterization,
                )
            except Exception as e:
                _log.error("%s | error: %s", file_id, str(e))

        # Create BenchmarkStats from timing data
        if not all_python_ms or not all_cpp_ms:
            _log.error("No valid benchmark data collected")
            return None

        python_ms_stats = create_stats(all_python_ms)
        cpp_ms_stats = create_stats(all_cpp_ms)
        html_to_bracket_ms_stats = create_stats(all_html_to_bracket_ms)

        # Create and return BenchmarkReport
        report = BenchmarkReport(
            samples=benchmark_samples,
            python_ms_stats=python_ms_stats,
            cpp_ms_stats=cpp_ms_stats,
            html_to_bracket_ms_stats=html_to_bracket_ms_stats,
        )

        # Log benchmark statistics
        log_stats("Python stats", python_ms_stats)
        log_stats("C++ stats   ", cpp_ms_stats)
        log_stats("HTML to bracket stats", html_to_bracket_ms_stats)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self._save_root / f"benchmark_report_{timestamp}.json"
        with open(report_path, "w") as f:
            f.write(report.model_dump_json(indent=2))
        _log.info("Benchmark report saved to: %s", report_path)

        return report

    def _find_matches(self, data_root: Path) -> dict[Path, Path]:
        r"""
        1. Scan the root for the ground truth and prediction files.
        2. Return a dictionary with the paths to the ground truth and prediction files.
        3. The ground truth files are the ones with the prefix "GT" and the prediction files are the ones with the prefix "pred".
        4. The keys of the dictionary are the paths to the ground truth files and the values are the paths to the prediction files.
        5. All files have an extension of ".bracket".
        6. Use the ground truth files as a pivot to match the prediction files.
        """
        matches = {}

        # Find all ground truth files with the GT prefix
        gt_files = sorted(
            # data_root.glob(f"{self._gt_prefix}_*.bracket"), key=lambda p: p.stem
            data_root.glob(f"{self._gt_prefix}_*.html"),
            key=lambda p: p.stem,
        )

        for gt_file in gt_files:
            # Extract the doc_id and table_id from the GT filename
            # Format: GT_{doc_id}_{table_id}.bracket
            gt_filename = gt_file.stem  # Remove .bracket extension
            # Remove the GT_ prefix
            suffix = gt_filename[len(self._gt_prefix) + 1 :]  # +1 for underscore

            # Construct the corresponding prediction filename
            # pred_filename = f"{self._pred_prefix}_{suffix}.bracket"
            pred_filename = f"{self._pred_prefix}_{suffix}.html"
            pred_file = data_root / pred_filename

            # Only add to matches if the prediction file exists
            if pred_file.exists():
                matches[gt_file] = pred_file

        return matches

    def _apted_teds(self, gt_bracket_str: str, pred_bracket_str: str) -> float:
        r""" """
        gt_tree: TableTree = TableTree.from_bracket(gt_bracket_str)
        pred_tree: TableTree = TableTree.from_bracket(pred_bracket_str)

        # Calculate number of nodes for normalization
        def count_nodes(tree):
            count = 1
            for child in tree.children:
                count += count_nodes(child)
            return count

        n_nodes_gt = count_nodes(gt_tree)
        n_nodes_pred = count_nodes(pred_tree)
        n_nodes = max(n_nodes_gt, n_nodes_pred)
        python_distance = APTED(
            pred_tree, gt_tree, CustomConfig()
        ).compute_edit_distance()
        python_teds = 1.0 - (float(python_distance) / n_nodes)

        return python_teds


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

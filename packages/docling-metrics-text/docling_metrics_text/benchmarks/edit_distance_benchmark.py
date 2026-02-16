import argparse
import json
import logging
import math
import time
from datetime import datetime
from pathlib import Path
from statistics import mean, median
from typing import Any

from docling_metrics_text import TextMetrics
from docling_metrics_text.docling_metrics_text import TextMetricsMode
from docling_metrics_text.utils.data_loader import FileEntry, TextFileLoader

_log = logging.getLogger(__name__)

RELATIVE_TOLERANCE = 1e-6


class EditDistanceBenchmarker:
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
        mc_python = TextMetrics(mode=TextMetricsMode.PYTHON)
        mc_cpp = TextMetrics(mode=TextMetricsMode.CPP)

        report: dict[str, dict[str, Any]] = {
            "stats": {},
            "files": {},
        }

        timing_data: dict[str, list[float]] = {
            "tokenizer": [],
            "edit_distance_python": [],
            "edit_distance_cpp": [],
        }

        mismatches: list[str] = []

        file_entry: FileEntry
        for file_entry in loader.load():
            id = file_entry.id
            gt = file_entry.pivot_content
            pred = file_entry.target_content
            if not pred:
                _log.error("Missing prediction for: %s", id)
                continue

            sample_bench: dict[str, dict[str, float | None]] = {}

            # Measure tokenization time
            t0 = time.perf_counter()
            tokens_a, tokens_b, _, _ = mc_python._tokenize_pair(gt, pred)
            tokenizer_ms = (time.perf_counter() - t0) * 1000
            sample_bench["tokenizer"] = {
                "ms": tokenizer_ms,
                "tokens_a_count": len(tokens_a),
                "tokens_b_count": len(tokens_b),
            }
            timing_data["tokenizer"].append(tokenizer_ms)

            # Measure edit distance with Python implementation
            t0 = time.perf_counter()
            ed_python = mc_python._compute_edit_distance(tokens_a, tokens_b)
            ed_python_ms = (time.perf_counter() - t0) * 1000
            sample_bench["edit_distance_python"] = {
                "ms": ed_python_ms,
                "value": ed_python,
            }
            timing_data["edit_distance_python"].append(ed_python_ms)

            # Measure edit distance with C++ implementation
            t0 = time.perf_counter()
            ed_cpp = mc_cpp._compute_edit_distance(tokens_a, tokens_b)
            ed_cpp_ms = (time.perf_counter() - t0) * 1000
            sample_bench["edit_distance_cpp"] = {
                "ms": ed_cpp_ms,
                "value": ed_cpp,
            }
            timing_data["edit_distance_cpp"].append(ed_cpp_ms)

            # Verify that Python and C++ implementations produce consistent results
            if not math.isclose(ed_python, ed_cpp, rel_tol=RELATIVE_TOLERANCE):
                mismatches.append(id)
                _log.warning(
                    f"{id} | MISMATCH: python={ed_python:.8f} cpp={ed_cpp:.8f} "
                    f"diff={abs(ed_python - ed_cpp):.2e}"
                )

            sample_bench["match"] = {
                "within_tolerance": float(
                    math.isclose(ed_python, ed_cpp, rel_tol=RELATIVE_TOLERANCE)
                ),
            }

            report["files"][id] = sample_bench

            _log.info(
                f"{id} | python: {ed_python_ms:.2f}ms (val={ed_python:.6f}) | "
                f"cpp: {ed_cpp_ms:.2f}ms (val={ed_cpp:.6f}) | "
                f"tokenizer: {tokenizer_ms:.2f}ms"
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

        # Report mismatches
        total_files = len(report["files"])
        report["stats"]["tolerance_check"] = {
            "relative_tolerance": RELATIVE_TOLERANCE,
            "total_files": total_files,
            "mismatches": len(mismatches),
            "mismatch_ids": mismatches,
        }
        if mismatches:
            _log.warning(
                f"Found {len(mismatches)}/{total_files} mismatches exceeding "
                f"relative tolerance {RELATIVE_TOLERANCE}"
            )
        else:
            _log.info(
                f"All {total_files} files within relative tolerance {RELATIVE_TOLERANCE}"
            )

        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self._save_root / f"edit_distance_benchmark_report_{timestamp}.json"
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
    benchmarker = EditDistanceBenchmarker(save_root)
    benchmarker.benchmark(input_root)


if __name__ == "__main__":
    main()


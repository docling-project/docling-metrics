from statistics import mean, median, stdev
import time
from typing import Optional
from pydantic import BaseModel
from logging import Logger
from pathlib import Path
import subprocess
from benchmark.teds import TableTree, TEDScorer
from apted import APTED
from benchmark.teds import CustomConfig
import logging
from datetime import datetime

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
    match: bool


class BenchmarkReport(BaseModel):
    samples: dict[str, BenchmarkSample]  # id -> BenchmarkSample
    python_ms_stats: BenchmarkStats
    cpp_ms_stats: BenchmarkStats


class Benchmarker:
    def __init__(
        self,
        cpp_ted: Path,
        save_root: Path,
    ):
        r""" """
        self._cpp_teds = cpp_ted
        self._gt_prefix = "GT"
        self._pred_prefix = "pred"

        # Ensure save_root exists
        save_root.mkdir(parents=True, exist_ok=True)
        self._save_root = save_root

        # Benchmarking report
        # self._report: dict

    def benchmark(self, bracket_root: Path) -> Optional[BenchmarkReport]:
        r"""
        1. Match the ground truth and prediction files using the find_matches().
        2. Use the matched file pairs from step 1, load the files and pass their content in TableTree.from_bracket() to create TableTree instances.
        3. Pass the TableTree instances to the APTED class to get the TED score.
        4. Call the c++ implementation using the subprocess module. The input arguments must be:
           - First argument is the literal "file"
           - Second argument is the path to the ground truth bracket file prefixed with self._gt_prefix.
           - Third argument is the path to the prediction bracket file prefixed with self._pred_prefix.
        5. Print the output of the python and the C++ implementations.
        """
        # Step 1: Match ground truth and prediction files
        matches = self._find_matches(bracket_root)

        if not matches:
            _log.info("No matching files found.")
            return None

        # Process each matched pair
        benchmark_samples: dict[str, BenchmarkSample] = {}
        all_python_ms: list[float] = []
        all_cpp_ms: list[float] = []

        for i, (gt_file, pred_file) in enumerate(matches.items()):
            # Extract filename without GT prefix
            gt_filename = gt_file.stem
            file_id = gt_filename[len(self._gt_prefix) + 1 :]

            # Step 2: Load files and create TableTree instances
            with open(gt_file, "r") as f:
                gt_bracket_str: str = f.read()
            with open(pred_file, "r") as f:
                pred_bracket_str: str = f.read()

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

            # Step 3: Calculate TED score using Python implementation
            t0 = time.monotonic()
            python_distance = APTED(
                pred_tree, gt_tree, CustomConfig()
            ).compute_edit_distance()
            python_ms = (time.monotonic() - t0) * 1000
            all_python_ms.append(python_ms)
            python_teds = 1.0 - (float(python_distance) / n_nodes)

            # Step 4: Call C++ implementation
            cpp_teds = None
            cpp_ms = -1
            try:
                cmd = [str(self._cpp_teds), "file", str(gt_file), str(pred_file)]
                t0 = time.monotonic()
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                cpp_ms = (time.monotonic() - t0) * 1000
                all_cpp_ms.append(cpp_ms)

                if result.returncode == 0:
                    cpp_output = result.stdout.strip()
                    try:
                        # Parse the C++ output to extract distance from last line
                        # Expected format: "Distance TED:X" where X is the distance
                        lines = cpp_output.split("\n")
                        last_line = lines[-1]
                        # Extract the number after "Distance TED:"
                        cpp_distance = float(last_line.split(":")[1])
                        cpp_teds = 1.0 - (float(cpp_distance) / n_nodes)
                    except (ValueError, IndexError) as e:
                        # If parsing fails, log the error and output
                        _log.error(
                            "%s | C++ parsing failed: %s",
                            file_id,
                            str(e),
                        )
                else:
                    _log.error(
                        "%s | C++ error: %s",
                        file_id,
                        result.stderr.strip(),
                    )
            except subprocess.TimeoutExpired:
                _log.error("%s | C++ timeout", file_id)
            except Exception as e:
                _log.error("%s | C++ error: %s", file_id, str(e))

            # Create BenchmarkSample
            if cpp_teds is not None:
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
                )
                benchmark_samples[file_id] = sample

                _log.info(
                    "%d: %s | n_nodes: %d | Python: %.6f (%.2fms) | C++: %.6f (%.2fms) | %s",
                    i,
                    file_id,
                    n_nodes,
                    python_teds,
                    python_ms,
                    cpp_teds,
                    cpp_ms,
                    characterization,
                )
            else:
                _log.info(
                    "%d: %s | n_nodes: %d | Python: %.6f (%.2fms) | C++: N/A",
                    i,
                    file_id,
                    n_nodes,
                    python_teds,
                    python_ms,
                )

        # Create BenchmarkStats from timing data
        if not all_python_ms or not all_cpp_ms:
            _log.error("No valid benchmark data collected")
            return None

        python_ms_stats = BenchmarkStats(
            mean=mean(all_python_ms),
            median=median(all_python_ms),
            std=stdev(all_python_ms) if len(all_python_ms) > 1 else 0.0,
            max=max(all_python_ms),
            min=min(all_python_ms),
        )

        cpp_ms_stats = BenchmarkStats(
            mean=mean(all_cpp_ms),
            median=median(all_cpp_ms),
            std=stdev(all_cpp_ms) if len(all_cpp_ms) > 1 else 0.0,
            max=max(all_cpp_ms),
            min=min(all_cpp_ms),
        )

        # Create and return BenchmarkReport
        report = BenchmarkReport(
            samples=benchmark_samples,
            python_ms_stats=python_ms_stats,
            cpp_ms_stats=cpp_ms_stats,
        )

        # Save report as JSON

        # Log benchmark statistics
        _log.info(
            "Python stats | mean: %.2fms | median: %.2fms | std: %.2fms | min: %.2fms | max: %.2fms",
            python_ms_stats.mean,
            python_ms_stats.median,
            python_ms_stats.std,
            python_ms_stats.min,
            python_ms_stats.max,
        )
        _log.info(
            "C++ stats    | mean: %.2fms | median: %.2fms | std: %.2fms | min: %.2fms | max: %.2fms",
            cpp_ms_stats.mean,
            cpp_ms_stats.median,
            cpp_ms_stats.std,
            cpp_ms_stats.min,
            cpp_ms_stats.max,
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self._save_root / f"benchmark_report_{timestamp}.json"
        with open(report_path, "w") as f:
            f.write(report.model_dump_json(indent=2))
        _log.info("Benchmark report saved to: %s", report_path)

        return report

    def _find_matches(self, bracket_root: Path) -> dict[Path, Path]:
        r"""
        1. Scan the bracket_root for the ground truth and prediction files.
        2. Return a dictionary with the paths to the ground truth and prediction files.
        3. The ground truth files are the ones with the prefix "GT" and the prediction files are the ones with the prefix "pred".
        4. The keys of the dictionary are the paths to the ground truth files and the values are the paths to the prediction files.
        5. All files have an extension of ".bracket".
        6. Use the ground truth files as a pivot to match the prediction files.
        """
        matches = {}

        # Find all ground truth files with the GT prefix
        gt_files = sorted(
            bracket_root.glob(f"{self._gt_prefix}_*.bracket"), key=lambda p: p.stem
        )

        for gt_file in gt_files:
            # Extract the doc_id and table_id from the GT filename
            # Format: GT_{doc_id}_{table_id}.bracket
            gt_filename = gt_file.stem  # Remove .bracket extension
            # Remove the GT_ prefix
            suffix = gt_filename[len(self._gt_prefix) + 1 :]  # +1 for underscore

            # Construct the corresponding prediction filename
            pred_filename = f"{self._pred_prefix}_{suffix}.bracket"
            pred_file = bracket_root / pred_filename

            # Only add to matches if the prediction file exists
            if pred_file.exists():
                matches[gt_file] = pred_file

        return matches

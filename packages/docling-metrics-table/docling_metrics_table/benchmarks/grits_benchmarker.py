import argparse
import json
import logging
import time
from datetime import datetime
from logging import Logger
from pathlib import Path
from statistics import mean, median, stdev
from typing import Any, Optional

from docling_metrics_table.benchmarks.benchmarks_utils import (
    BenchmarkReport,
    BenchmarkSample,
    BenchmarkStats,
)
from docling_metrics_table.docling_metrics_table import (
    TableMetric,
    TableMetricCell,
    TableMetricCellsInputSample,
    TableMetricKind,
    TableMetricSampleEvaluation,
)

_log: Logger = logging.getLogger(__name__)


class GriTSBenchmarker:
    r"""
    Receive as input a json file with the GriTS cell data.
    """

    def __init__(
        self,
        save_root: Path,
    ):
        r""" """
        save_root.mkdir(parents=True, exist_ok=True)
        self._save_root = save_root
        self._grits_metric = TableMetric(metrics=[TableMetricKind.GRITS])

    def benchmark(
        self,
        input_json: Path,
    ) -> Optional[BenchmarkReport]:
        r"""
        Benchmark the GriTS implementation on a json dataset of table cells.
        """

        if not input_json.exists():
            raise FileNotFoundError(f"Input json file not found: {input_json}")

        with open(input_json, "r") as f:
            data: list[dict[str, Any]] = json.load(f)

        if len(data) == 0:
            _log.info("No samples found in %s", input_json)
            return None

        benchmark_samples: dict[str, BenchmarkSample] = {}
        all_python_ms: list[float] = []

        for i, item in enumerate(data):
            sample_id = str(item["id"])
            try:
                true_cells = [
                    TableMetricCell.model_validate(cell) for cell in item["true_cells"]
                ]
                pred_cells = [
                    TableMetricCell.model_validate(cell) for cell in item["pred_cells"]
                ]
                metric_input = TableMetricCellsInputSample(
                    id=sample_id,
                    cells_a=true_cells,
                    cells_b=pred_cells,
                )

                t0 = time.monotonic()
                sample_evaluation: TableMetricSampleEvaluation = (
                    self._grits_metric.evaluate_sample(metric_input)
                )
                python_ms = (time.monotonic() - t0) * 1000
                all_python_ms.append(python_ms)

                if sample_evaluation.grits is None:
                    raise ValueError("Expected GriTS evaluation for cells input")

                actual_grits_topology = sample_evaluation.grits.grits_topology
                actual_grits_content = sample_evaluation.grits.grits_content
                actual_grits_location = sample_evaluation.grits.grits_location
                if actual_grits_topology is None:
                    raise ValueError("Expected topology GriTS score for cells input")
                if actual_grits_content is None:
                    raise ValueError("Expected content GriTS score for cells input")
                if actual_grits_location is None:
                    raise ValueError("Expected location GriTS score for cells input")

                expected_grits_topology = float(item["grits_top"])
                expected_grits_content = float(item["grits_con"])
                expected_grits_location = float(item["grits_loc"])
                match = (
                    abs(actual_grits_topology - expected_grits_topology) < 1e-6
                    and abs(actual_grits_content - expected_grits_content) < 1e-6
                    and abs(actual_grits_location - expected_grits_location) < 1e-6
                )

                benchmark_samples[sample_id] = BenchmarkSample(
                    id=sample_id,
                    sample_len=len(true_cells),
                    python_grits_topology=actual_grits_topology,
                    python_grits_content=actual_grits_content,
                    python_grits_location=actual_grits_location,
                    python_grits_ms=python_ms,
                    match=match,
                )

                _log.info(
                    "%d: %s | n_cells: %d | GriTS-top: %.6f | GriTS-con: %.6f | GriTS-loc: %.6f | %.2fms | %s",
                    i,
                    sample_id,
                    len(true_cells),
                    actual_grits_topology,
                    actual_grits_content,
                    actual_grits_location,
                    python_ms,
                    "Match!" if match else "Differ",
                )
            except Exception as e:
                _log.error("%s | error: %s", sample_id, str(e))

        if not all_python_ms:
            _log.error("No valid benchmark data collected")
            return None

        python_ms_stats = BenchmarkStats(
            mean=mean(all_python_ms),
            median=median(all_python_ms),
            std=stdev(all_python_ms) if len(all_python_ms) > 1 else 0.0,
            max=max(all_python_ms),
            min=min(all_python_ms),
        )
        report = BenchmarkReport(
            samples=benchmark_samples,
            python_ms_stats=python_ms_stats,
        )

        _log.info(
            "%s | mean: %.2fms | median: %.2fms | std: %.2fms | min: %.2fms | max: %.2fms",
            "Python GriTS stats",
            python_ms_stats.mean,
            python_ms_stats.median,
            python_ms_stats.std,
            python_ms_stats.min,
            python_ms_stats.max,
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self._save_root / f"grits_benchmark_report_{timestamp}.json"
        with open(report_path, "w") as f:
            f.write(report.model_dump_json(indent=2))
        _log.info("Benchmark report saved to: %s", report_path)

        return report


def main():
    parser = argparse.ArgumentParser(description="GriTS Benchmark")
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        required=True,
        help="Json file with the GriTS cell data",
    )
    parser.add_argument(
        "-s",
        "--save_root",
        type=Path,
        required=True,
        help="Path to the directory to save generated data",
    )
    args = parser.parse_args()

    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_format)

    _log.info("Benchmark GriTS implementation")
    _log.info("Input file: %s", args.input)
    _log.info("Save dir: %s", args.save_root)
    benchmarker = GriTSBenchmarker(args.save_root)
    benchmarker.benchmark(args.input)


if __name__ == "__main__":
    main()

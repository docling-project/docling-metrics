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
    TableMetricTaskKind,
)

_log: Logger = logging.getLogger(__name__)

TASKS: tuple[TableMetricTaskKind, ...] = (
    TableMetricTaskKind.STRUCTURE,
    TableMetricTaskKind.CONTENT,
    TableMetricTaskKind.LOCATION,
)


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

    def _benchmark_task(
        self,
        sample_id: str,
        true_cells: list[TableMetricCell],
        pred_cells: list[TableMetricCell],
        task: TableMetricTaskKind,
    ) -> tuple[float, float]:
        metric_input = TableMetricCellsInputSample(
            id=sample_id,
            cells_a=true_cells,
            cells_b=pred_cells,
            tasks=[task],
        )

        t0 = time.monotonic()
        sample_evaluation: TableMetricSampleEvaluation = (
            self._grits_metric.evaluate_sample(metric_input)
        )
        python_ms = (time.monotonic() - t0) * 1000

        if sample_evaluation.grits is None:
            raise ValueError(f"Expected {task.value} GriTS evaluation for cells input")

        if task is TableMetricTaskKind.STRUCTURE:
            grits_score = sample_evaluation.grits.grits_topology
        elif task is TableMetricTaskKind.CONTENT:
            grits_score = sample_evaluation.grits.grits_content
        elif task is TableMetricTaskKind.LOCATION:
            grits_score = sample_evaluation.grits.grits_location
        else:
            raise ValueError(f"Unsupported task for GriTS benchmarking: {task}")

        if grits_score is None:
            raise ValueError(f"Expected {task.value} GriTS score for cells input")

        return grits_score, python_ms

    def benchmark(
        self,
        input_json: Path,
    ) -> Optional[BenchmarkReport]:
        r"""
        Benchmark the GriTS implementation on a json dataset of table cells.
        """
        with open(input_json, "r") as f:
            data: list[dict[str, Any]] = json.load(f)

        if len(data) == 0:
            _log.info("No samples found in %s", input_json)
            return None

        benchmark_samples: dict[str, BenchmarkSample] = {}
        all_python_ms_by_task: dict[TableMetricTaskKind, list[float]] = {
            task: [] for task in TASKS
        }
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

                grits_by_task: dict[TableMetricTaskKind, float] = {}
                python_ms_by_task: dict[TableMetricTaskKind, float] = {}
                for task in TASKS:
                    grits_score, python_task_ms = self._benchmark_task(
                        sample_id=sample_id,
                        true_cells=true_cells,
                        pred_cells=pred_cells,
                        task=task,
                    )
                    grits_by_task[task] = grits_score
                    python_ms_by_task[task] = python_task_ms
                    all_python_ms_by_task[task].append(python_task_ms)

                python_ms = sum(python_ms_by_task.values())
                all_python_ms.append(python_ms)

                expected_grits_by_task = {
                    TableMetricTaskKind.STRUCTURE: float(item["grits_top"]),
                    TableMetricTaskKind.CONTENT: float(item["grits_con"]),
                    TableMetricTaskKind.LOCATION: float(item["grits_loc"]),
                }
                match = all(
                    abs(grits_by_task[task] - expected_grits_by_task[task]) < 1e-6
                    for task in TASKS
                )

                benchmark_samples[sample_id] = BenchmarkSample(
                    id=sample_id,
                    sample_len=len(true_cells),
                    python_grits_topology=grits_by_task[TableMetricTaskKind.STRUCTURE],
                    python_grits_topology_ms=python_ms_by_task[
                        TableMetricTaskKind.STRUCTURE
                    ],
                    python_grits_content=grits_by_task[TableMetricTaskKind.CONTENT],
                    python_grits_content_ms=python_ms_by_task[
                        TableMetricTaskKind.CONTENT
                    ],
                    python_grits_location=grits_by_task[TableMetricTaskKind.LOCATION],
                    python_grits_location_ms=python_ms_by_task[
                        TableMetricTaskKind.LOCATION
                    ],
                    python_grits_ms=python_ms,
                    match=match,
                )

                _log.info(
                    "%d: %s | n_cells: %d | GriTS-top: %.6f (%.2fms) | GriTS-con: %.6f (%.2fms) | GriTS-loc: %.6f (%.2fms) | total: %.2fms | %s",
                    i,
                    sample_id,
                    len(true_cells),
                    grits_by_task[TableMetricTaskKind.STRUCTURE],
                    python_ms_by_task[TableMetricTaskKind.STRUCTURE],
                    grits_by_task[TableMetricTaskKind.CONTENT],
                    python_ms_by_task[TableMetricTaskKind.CONTENT],
                    grits_by_task[TableMetricTaskKind.LOCATION],
                    python_ms_by_task[TableMetricTaskKind.LOCATION],
                    python_ms,
                    "Match!" if match else "Differ",
                )
            except Exception as e:
                _log.error("%s | error: %s", sample_id, str(e))

        if not all_python_ms:
            _log.error("No valid benchmark data collected")
            return None

        python_ms_stats_by_task: dict[TableMetricTaskKind, BenchmarkStats] = {}
        for task in TASKS:
            task_times = all_python_ms_by_task[task]
            python_ms_stats_by_task[task] = BenchmarkStats(
                mean=mean(task_times),
                median=median(task_times),
                std=stdev(task_times) if len(task_times) > 1 else 0.0,
                max=max(task_times),
                min=min(task_times),
            )
        python_ms_stats = BenchmarkStats(
            mean=mean(all_python_ms),
            median=median(all_python_ms),
            std=stdev(all_python_ms) if len(all_python_ms) > 1 else 0.0,
            max=max(all_python_ms),
            min=min(all_python_ms),
        )
        report = BenchmarkReport(
            samples=benchmark_samples,
            python_grits_topology_ms_stats=python_ms_stats_by_task[
                TableMetricTaskKind.STRUCTURE
            ],
            python_grits_content_ms_stats=python_ms_stats_by_task[
                TableMetricTaskKind.CONTENT
            ],
            python_grits_location_ms_stats=python_ms_stats_by_task[
                TableMetricTaskKind.LOCATION
            ],
            python_grits_ms_stats=python_ms_stats,
        )

        for task in TASKS:
            _log.info(
                "%s | mean: %.2fms | median: %.2fms | std: %.2fms | min: %.2fms | max: %.2fms",
                f"Python GriTS {task.value} stats",
                python_ms_stats_by_task[task].mean,
                python_ms_stats_by_task[task].median,
                python_ms_stats_by_task[task].std,
                python_ms_stats_by_task[task].min,
                python_ms_stats_by_task[task].max,
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

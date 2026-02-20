import argparse
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from statistics import mean, median
from typing import Any

from docling_metrics_layout import LayoutMetrics
from docling_metrics_layout.benchmarks.tools import load_layout_samples
from docling_metrics_layout.layout_types import LayoutMetricSample

_log = logging.getLogger(__name__)


class Benchmarker:
    r"""
    Benchmark layout evaluation runtime on a COCO-format dataset.

    Measures the runtime of each private _evaluate_xxx method of LayoutMetrics:
      - _evaluate_pixel_sample  (per-sample)
      - _evaluate_map_sample    (per-sample)
      - _evaluate_pixel_dataset (dataset-level)
      - _evaluate_map_dataset   (dataset-level)
    """

    def __init__(self, save_root: Path, concurrency: int = 4) -> None:
        r""" """
        self._save_root = save_root
        self._save_root.mkdir(parents=True, exist_ok=True)
        self._concurrency = concurrency

    def benchmark(
        self,
        gt_coco_fn: Path,
        preds_coco_fn: Path,
        limit: int | None = None,
    ):
        r""" """
        _log.info("Convert COCO data to internal representation...")
        category_id_to_name, samples = load_layout_samples(gt_coco_fn, preds_coco_fn)
        if limit is not None:
            samples = samples[:limit]
        _log.info("Samples to evaluate: %d", len(samples))

        lm = LayoutMetrics(
            category_id_to_name=category_id_to_name,
            concurrency=self._concurrency,
        )

        report: dict[str, Any] = {
            "concurrency": self._concurrency,
            "stats": {},
            "samples": {},
            "dataset": {},
        }

        if False:
            self._evaluate_individual_samples(samples, lm, report)

        # Measure dataset-level pixel evaluation time
        _log.info("Benchmarking pixel-layout metrics for the entire dataset...")
        t0 = time.perf_counter()
        pixel_dataset_eval = lm._evaluate_pixel_dataset(samples)  # noqa: F841
        pixel_dataset_ms = (time.perf_counter() - t0) * 1000
        n = len(samples)
        report["dataset"]["size"] = n
        report["dataset"]["pixel_dataset"] = {
            "ms": pixel_dataset_ms,
            "average_ms": pixel_dataset_ms / n if n else 0.0,
            # Debug: Disable dumping the full metrics
            # "metrics": pixel_dataset_eval.model_dump(),
        }
        _log.info(
            "pixel_dataset: %.2fms for %d samples (%.4fms/sample)",
            pixel_dataset_ms,
            n,
            pixel_dataset_ms / n if n else 0.0,
        )

        # Measure dataset-level mAP evaluation time
        _log.info("Benchmarking mAP metrics for the entire dataset...")
        t0 = time.perf_counter()
        map_dataset_eval = lm._evaluate_map_dataset(samples)  # noqa: F841
        map_dataset_ms = (time.perf_counter() - t0) * 1000
        report["dataset"]["map_dataset"] = {
            "ms": map_dataset_ms,
            "average_ms": map_dataset_ms / n if n else 0.0,
            # Debug: Disable dumping the full metrics
            # "metrics": map_dataset_eval.model_dump(),
        }
        _log.info(
            "map_dataset: %.2fms for %d samples (%.4fms/sample)",
            map_dataset_ms,
            n,
            map_dataset_ms / n if n else 0.0,
        )

        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self._save_root / f"benchmark_report_{timestamp}.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, sort_keys=True)
        _log.info("Benchmark report saved to: %s", report_path)

    def _evaluate_individual_samples(
        self,
        samples: list[LayoutMetricSample],
        lm: LayoutMetrics,
        report: dict[str, Any],
    ):
        r""" """
        _log.info("Benchmarking metrics for individual samples...")

        # Collect per-sample timing data
        timing_data: dict[str, list[float]] = {
            "pixel_sample": [],
            "map_sample": [],
        }
        for sample in samples:
            id = sample.id
            sample_bench: dict[str, dict[str, float]] = {}

            # Measure pixel sample evaluation time
            t0 = time.perf_counter()
            lm._evaluate_pixel_sample(sample)
            pixel_sample_ms = (time.perf_counter() - t0) * 1000
            sample_bench["pixel_sample"] = {"ms": pixel_sample_ms}
            timing_data["pixel_sample"].append(pixel_sample_ms)

            # Measure mAP sample evaluation time
            t0 = time.perf_counter()
            lm._evaluate_map_sample(sample)
            map_sample_ms = (time.perf_counter() - t0) * 1000
            sample_bench["map_sample"] = {"ms": map_sample_ms}
            timing_data["map_sample"].append(map_sample_ms)

            report["samples"][id] = sample_bench
            _log.info(
                "%s | pixel_sample: %.2fms | map_sample: %.2fms",
                id,
                pixel_sample_ms,
                map_sample_ms,
            )

        # Compute statistics for per-sample methods
        for task_name, times in timing_data.items():
            if times:
                report["stats"][task_name] = {
                    "min": min(times),
                    "max": max(times),
                    "mean": mean(times),
                    "median": median(times),
                }
                _log.info(
                    "%s stats | min: %.2fms | max: %.2fms | mean: %.2fms | median: %.2fms",
                    task_name,
                    min(times),
                    max(times),
                    mean(times),
                    median(times),
                )
        return report


def main():
    parser = argparse.ArgumentParser(description="Layout Metrics Benchmark")
    parser.add_argument(
        "-G",
        "--gt_coco",
        type=Path,
        required=True,
        help="Path to the COCO ground-truth annotations JSON file",
    )
    parser.add_argument(
        "-p",
        "--preds_coco",
        type=Path,
        required=True,
        help="Path to the COCO predictions JSON file",
    )
    parser.add_argument(
        "-s",
        "--save_root",
        type=Path,
        required=True,
        help="Path to the directory to save generated data",
    )
    parser.add_argument(
        "-l",
        "--limit",
        type=int,
        default=None,
        help="Maximum number of samples to benchmark (default: all)",
    )
    parser.add_argument(
        "-c",
        "--concurrency",
        type=int,
        default=4,
        help="Number of concurrent workers for pixel evaluation (default: 4)",
    )
    args = parser.parse_args()

    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_format)
    logging.getLogger("torchmetrics").setLevel(logging.WARNING)
    logging.getLogger("faster_coco_eval").setLevel(logging.WARNING)

    _log.info("Benchmark LayoutMetrics implementations")
    benchmarker = Benchmarker(args.save_root, concurrency=args.concurrency)
    benchmarker.benchmark(
        gt_coco_fn=args.gt_coco,
        preds_coco_fn=args.preds_coco,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()

import logging
import random
import statistics
from pathlib import Path
from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np

from docling_metrics_layout.layout_types import DatasetStatistics

_log = logging.getLogger(__name__)


def stats_to_table(
    dataset_stats: DatasetStatistics, metric_name: str
) -> Tuple[List[List[str]], List[str]]:
    """Convert dataset statistics to a formatted table."""
    headers = [
        f"{metric_name}",
        "prob [%]",
        "acc [%]",
        "1-acc [%]",
        "total",
    ]
    cumsum: float = 0.0

    table = []
    if dataset_stats.total > 0:
        for i in range(len(dataset_stats.bins) - 1):
            table.append(
                [
                    f"({dataset_stats.bins[i + 0]:.3f}, {dataset_stats.bins[i + 1]:.3f}]",
                    f"{100.0 * float(dataset_stats.hist[i]) / float(dataset_stats.total):.2f}",
                    f"{100.0 * cumsum:.2f}",
                    f"{100.0 * (1.0 - cumsum):.2f}",
                    f"{dataset_stats.hist[i]}",
                ]
            )
            cumsum += float(dataset_stats.hist[i]) / float(dataset_stats.total)
    return table, headers


def stats_to_histogram(dataset_stats: DatasetStatistics, figname: Path, name: str = ""):
    """Save dataset statistics as a histogram figure."""
    # Calculate bin widths
    bin_widths = [
        dataset_stats.bins[i + 1] - dataset_stats.bins[i]
        for i in range(len(dataset_stats.bins) - 1)
    ]
    bin_middle = [
        (dataset_stats.bins[i + 1] + dataset_stats.bins[i]) / 2.0
        for i in range(len(dataset_stats.bins) - 1)
    ]

    # Plot histogram
    fignum = int(1000 * random.random())
    plt.figure(fignum)
    plt.bar(bin_middle, dataset_stats.hist, width=bin_widths, edgecolor="black")

    plt.xlabel("Score")
    plt.ylabel("Frequency")
    plt.title(
        f"{name} (mean: {dataset_stats.mean:.2f}, median: {dataset_stats.median:.2f}, std: {dataset_stats.std:.2f}, total: {dataset_stats.total})"
    )

    _log.info(f"Saving figure to {figname}")
    plt.savefig(figname)


def compute_stats(
    values: List[float], max_value_is_one: bool = True, nr_bins: int = 20
) -> DatasetStatistics:
    total: int = len(values)

    mean: float = statistics.mean(values) if len(values) > 0 else -1
    median: float = statistics.median(values) if len(values) > 0 else -1
    std: float = statistics.stdev(values) if len(values) > 1 else 0.0
    _log.debug(
        f"Compute statistics: total: {total}, mean: {mean}, median: {median}, std: {std}"
    )

    max_value = 1.0
    if not max_value_is_one and len(values) > 0:
        max_value = max(values)

    # Compute the histogram
    hist, bins = np.histogram(values, bins=nr_bins, range=(0, max_value))
    _log.debug(f"Compute statistics: hist: {len(hist)}, #-bins: {len(bins)}")

    return DatasetStatistics(
        total=total, mean=mean, median=median, std=std, hist=hist, bins=bins
    )

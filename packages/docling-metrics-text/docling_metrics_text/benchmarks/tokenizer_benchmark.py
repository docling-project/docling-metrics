import argparse
import logging
from pathlib import Path

from docling_metrics_text import EditDistanceMetric

_log = logging.getLogger(__name__)


class TokenizerBenchmarker:
    def __init__(self, save_root: Path):
        self._save_root = save_root
        self._ed_metric = EditDistanceMetric()

        self._save_root.mkdir(parents=True, exist_ok=True)

    def benchmark(self, input_root: Path):
        r"""
        Compare the exactness and runtime between the NLTK and our implementation of the TreeBank tokenizer
        """
        # TODO


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
    benchmarker = TokenizerBenchmarker(save_root)
    benchmarker.benchmark(input_root)


if __name__ == "__main__":
    main()

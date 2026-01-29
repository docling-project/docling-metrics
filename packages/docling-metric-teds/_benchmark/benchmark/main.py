import argparse
from pathlib import Path
import logging

from benchmark.benchmark import CLIBenchmarker
from benchmark.dataset import ParquetDataset

_log = logging.getLogger(__name__)

CPP_TED = "/Users/nli/TEDS-metric/TEDS-metric/build/ted"


def main():
    parser = argparse.ArgumentParser(description="TEDS Benchmark")
    parser.add_argument(
        "-o",
        "--operation",
        type=str,
        required=True,
        help="Operation to perform. One of [export, benchmark]",
    )
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

    # Handle operation argument
    if args.operation == "export":
        _log.info("Export parquet dataset")
        ds: ParquetDataset = ParquetDataset(save_root=args.save_root)
        ds.export_teds_str(ds_path=input_root)
    elif args.operation == "benchmark":
        _log.info("Benchmark Python vs C++ TEDs implementations")
        benchmarker = CLIBenchmarker(CPP_TED, save_root)
        benchmarker.benchmark(input_root)
    else:
        _log.error("Invalid operation: %s", args.operation)


if __name__ == "__main__":
    main()

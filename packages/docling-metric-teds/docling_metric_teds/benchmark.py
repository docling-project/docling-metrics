import argparse
from statistics import mean, median, stdev
import time
from typing import Optional
from pydantic import BaseModel
from logging import Logger
from pathlib import Path
from apted import APTED, Config
from apted.helpers import Tree
from Levenshtein import distance
import logging
from datetime import datetime

from docling_metric_teds.docling_metric_teds import TEDSMetric, TEDSMetricSampleEvaluation, TEDSMetricInputSample 

_log: Logger = logging.getLogger(__name__)


class CustomConfig(Config):
    @staticmethod
    def maximum(*sequences):
        """Get maximum possible value"""
        return max(map(len, sequences))

    def normalized_distance(self, *sequences):
        """Get distance from 0 to 1"""
        return float(distance.levenshtein(*sequences)) / self.maximum(*sequences)

    def rename(self, node1, node2):
        """Compares attributes of trees"""
        if (
            (node1.tag != node2.tag)
            or (node1.colspan != node2.colspan)
            or (node1.rowspan != node2.rowspan)
        ):
            return 1.0
        if node1.tag in ["td", "th"]:
            if node1.content or node2.content:
                return self.normalized_distance(node1.content, node2.content)
        return 0.0


class TableTree(Tree):
    def __init__(self, tag, colspan=None, rowspan=None, content=None, *children):
        self.tag = tag
        self.colspan = colspan
        self.rowspan = rowspan
        self.content = content
        self.children = list(children)

    def bracket(self):
        """Show tree using brackets notation"""
        if self.tag in ["td", "th"]:
            result = '"tag": %s, "colspan": %d, "rowspan": %d, "text": %s' % (
                self.tag,
                self.colspan,
                self.rowspan,
                self.content,
            )
        else:
            result = '"tag": %s' % self.tag
        for child in self.children:
            result += child.bracket()
        return "{{{}}}".format(result)

    @staticmethod
    def from_bracket(bracket_str):
        """Parse tree from bracket notation string

        Args:
            bracket_str: String in bracket notation format, e.g.:
                {"tag": table{"tag": tbody{"tag": tr{"tag": td, "colspan": 1, "rowspan": 1, "text": []}}}}

        Returns:
            TableTree: Parsed tree structure
        """
        import re
        import ast

        def parse_node(s, pos):
            """Recursively parse a node from bracket notation

            Args:
                s: The full bracket string
                pos: Current position in the string

            Returns:
                tuple: (parsed_node, new_position)
            """
            # Skip whitespace
            while pos < len(s) and s[pos].isspace():
                pos += 1

            # Expect opening {
            if pos >= len(s) or s[pos] != "{":
                raise ValueError(
                    f"Expected '{{' at position {pos}, found: {s[pos : pos + 10]}"
                )
            pos += 1

            # Parse the tag attribute
            tag_match = re.match(r'"tag":\s*(\w+)', s[pos:])
            if not tag_match:
                raise ValueError(f"Could not find tag at position {pos}")

            tag = tag_match.group(1)
            pos += tag_match.end()

            # Check if this is a td/th node by looking for colspan
            colspan = None
            rowspan = None
            content = None

            # Look ahead to see if we have colspan/rowspan (indicates td/th node)
            lookahead = s[pos : pos + 100]
            colspan_match = re.match(r',\s*"colspan":\s*(\d+)', lookahead)

            if colspan_match:
                # This is a td/th node
                pos += colspan_match.end()
                colspan = int(colspan_match.group(1))

                # Parse rowspan
                rowspan_match = re.match(r',\s*"rowspan":\s*(\d+)', s[pos:])
                if rowspan_match:
                    pos += rowspan_match.end()
                    rowspan = int(rowspan_match.group(1))

                # Parse text content
                text_match = re.match(r',\s*"text":\s*(\[.*?\])', s[pos:])
                if text_match:
                    pos += text_match.end()
                    try:
                        content = ast.literal_eval(text_match.group(1))
                    except:
                        content = []
                else:
                    content = []

                node = TableTree(tag, colspan, rowspan, content)
            else:
                # This is a structural node (table, tbody, tr, etc.)
                node = TableTree(tag, None, None, None)

            # Parse children
            while pos < len(s):
                # Skip whitespace
                while pos < len(s) and s[pos].isspace():
                    pos += 1

                if pos >= len(s):
                    raise ValueError("Unexpected end of string")

                # Check for closing brace
                if s[pos] == "}":
                    pos += 1
                    break

                # Check for child node
                if s[pos] == "{":
                    child, pos = parse_node(s, pos)
                    node.children.append(child)
                else:
                    # Skip any other characters (shouldn't happen in valid input)
                    pos += 1

            return node, pos

        # Parse the root node
        root, _ = parse_node(bracket_str, 0)
        return root


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


# TODO:
# 1. Wrap the call of APTED in a function that encapsulates the TED to TEDS computation
# 2. Call the TEDSMetric instead of any C++ code
class Benchmarker:
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

            # Step 2: Call APTED
            t0 = time.monotonic()
            python_teds = self._apted_teds(gt_bracket_str, pred_bracket_str)
            python_ms = (time.monotonic() - t0) * 1000
            all_python_ms.append(python_ms)

            # Step 3: Call docling-meetric-teds
            cpp_teds = None
            cpp_ms = -1
            try:
                t0 = time.monotonic()
                metric_input: TEDSMetricInputSample = TEDSMetricInputSample(
                    id=file_id,
                    gt_bracket=gt_bracket_str,
                    pred_bracket=pred_bracket_str,
                )
                sample_evaluaton: TEDSMetricSampleEvaluation = self._teds_metric.evaluate_sample(
                    metric_input
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
            except Exception as e:
                _log.error("%s | C++ error: %s", file_id, str(e))

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
    
    def _apted_teds(self, gt_bracket_str: str, pred_bracket_str: str) -> float:
        r"""
        """
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

import hashlib
import itertools
import xml.etree.ElementTree as ET
from collections import OrderedDict, defaultdict
from difflib import SequenceMatcher
from typing import Any

import numpy as np


class LCSCache:
    def __init__(self, max_cache_size):
        r""" """
        self._max_cache_size = max_cache_size
        self._lcs_cache: OrderedDict[bytes, float] = OrderedDict()

        # Performance counters
        self._hits = 0
        self._misses = 0

    def _make_key(self, str1: str, str2: str) -> bytes:
        r"""The key must be symmeteric over string1, string2"""
        if str1 <= str2:
            ordered_strings = (str1, str2)
        else:
            ordered_strings = (str2, str1)

        cache_key = "\0".join(ordered_strings).encode("utf-8")
        return hashlib.blake2b(cache_key, digest_size=16).digest()

    def get(self, str1: str, str2: str) -> float | None:
        r"""Get an LCS value or None if not in cache"""
        cache_key = self._make_key(str1, str2)
        cached_value = self._lcs_cache.pop(cache_key, None)
        if cached_value is None:
            self._misses += 1
            return None

        self._lcs_cache[cache_key] = cached_value
        self._hits += 1
        return cached_value

    def set(self, str1: str, str2: str, value: float):
        cache_key = self._make_key(str1, str2)
        self._lcs_cache.pop(cache_key, None)
        self._lcs_cache[cache_key] = value

        while len(self._lcs_cache) > self._max_cache_size:
            self._lcs_cache.popitem(last=False)

    def counters(self) -> dict[str, int]:
        return {
            "hits": self._hits,
            "misses": self._misses,
            "cache_size": len(self._lcs_cache),
        }


class GriTSMetric:
    r"""Namespace for GriTS utilities."""

    def __init__(self, max_cache_size):
        r""" """
        self._lcs_cache = LCSCache(max_cache_size=max_cache_size)

    def cache_counters(self) -> dict[str, int]:
        return self._lcs_cache.counters()

    def _compute_fscore(
        self, num_true_positives: float, num_true: int, num_positives: int
    ) -> tuple[float, float, float]:
        if num_positives > 0:
            precision = num_true_positives / num_positives
        else:
            precision = 1.0

        if num_true > 0:
            recall = num_true_positives / num_true
        else:
            recall = 1.0

        if precision + recall > 0:
            fscore = 2 * precision * recall / (precision + recall)
        else:
            fscore = 0.0

        return fscore, precision, recall

    def _initialize_dp(
        self, sequence1_length: int, sequence2_length: int
    ) -> tuple[np.ndarray, np.ndarray]:
        scores = np.zeros((sequence1_length + 1, sequence2_length + 1))
        pointers = np.zeros((sequence1_length + 1, sequence2_length + 1))

        for seq1_idx in range(1, sequence1_length + 1):
            pointers[seq1_idx, 0] = -1

        for seq2_idx in range(1, sequence2_length + 1):
            pointers[0, seq2_idx] = 1

        return scores, pointers

    def _traceback(self, pointers: np.ndarray) -> tuple[list[int], list[int]]:
        seq1_idx = pointers.shape[0] - 1
        seq2_idx = pointers.shape[1] - 1
        aligned_sequence1_indices = []
        aligned_sequence2_indices = []

        while not (seq1_idx == 0 and seq2_idx == 0):
            if pointers[seq1_idx, seq2_idx] == -1:
                seq1_idx -= 1
            elif pointers[seq1_idx, seq2_idx] == 1:
                seq2_idx -= 1
            else:
                seq1_idx -= 1
                seq2_idx -= 1
                aligned_sequence1_indices.append(seq1_idx)
                aligned_sequence2_indices.append(seq2_idx)

        aligned_sequence1_indices.reverse()
        aligned_sequence2_indices.reverse()
        return aligned_sequence1_indices, aligned_sequence2_indices

    def _align_1d(
        self,
        sequence1: list[tuple[int, int]],
        sequence2: list[tuple[int, int]],
        reward_lookup: dict[tuple[int, int, int, int], float],
    ) -> float:
        sequence1_length = len(sequence1)
        sequence2_length = len(sequence2)

        scores, pointers = self._initialize_dp(sequence1_length, sequence2_length)

        for seq1_idx in range(1, sequence1_length + 1):
            for seq2_idx in range(1, sequence2_length + 1):
                reward = reward_lookup[
                    sequence1[seq1_idx - 1] + sequence2[seq2_idx - 1]
                ]
                diag_score = scores[seq1_idx - 1, seq2_idx - 1] + reward
                skip_seq2_score = scores[seq1_idx, seq2_idx - 1]
                skip_seq1_score = scores[seq1_idx - 1, seq2_idx]

                max_score = max(diag_score, skip_seq1_score, skip_seq2_score)
                scores[seq1_idx, seq2_idx] = max_score
                if diag_score == max_score:
                    pointers[seq1_idx, seq2_idx] = 0
                elif skip_seq1_score == max_score:
                    pointers[seq1_idx, seq2_idx] = -1
                else:
                    pointers[seq1_idx, seq2_idx] = 1

        return float(scores[-1, -1])

    def _align_2d_outer(
        self,
        true_shape: tuple[int, int],
        pred_shape: tuple[int, int],
        reward_lookup: dict[tuple[int, int, int, int], float],
    ) -> tuple[list[int], list[int], float]:
        scores, pointers = self._initialize_dp(true_shape[0], pred_shape[0])

        for row_idx in range(1, true_shape[0] + 1):
            for col_idx in range(1, pred_shape[0] + 1):
                reward = self._align_1d(
                    [(row_idx - 1, tcol) for tcol in range(true_shape[1])],
                    [(col_idx - 1, prow) for prow in range(pred_shape[1])],
                    reward_lookup,
                )
                diag_score = scores[row_idx - 1, col_idx - 1] + reward
                same_row_score = scores[row_idx, col_idx - 1]
                same_col_score = scores[row_idx - 1, col_idx]

                max_score = max(diag_score, same_col_score, same_row_score)
                scores[row_idx, col_idx] = max_score
                if diag_score == max_score:
                    pointers[row_idx, col_idx] = 0
                elif same_col_score == max_score:
                    pointers[row_idx, col_idx] = -1
                else:
                    pointers[row_idx, col_idx] = 1

        aligned_true_indices, aligned_pred_indices = self._traceback(pointers)
        return aligned_true_indices, aligned_pred_indices, float(scores[-1, -1])

    def _factored_2dmss(
        self,
        true_cell_grid: np.ndarray,
        pred_cell_grid: np.ndarray,
        reward_function: Any,
    ) -> tuple[float, float, float, float]:
        precomputed_rewards: dict[tuple[int, int, int, int], float] = {}
        transpose_rewards: dict[tuple[int, int, int, int], float] = {}

        for trow, tcol, prow, pcol in itertools.product(
            range(true_cell_grid.shape[0]),
            range(true_cell_grid.shape[1]),
            range(pred_cell_grid.shape[0]),
            range(pred_cell_grid.shape[1]),
        ):
            reward = reward_function(
                true_cell_grid[trow, tcol], pred_cell_grid[prow, pcol]
            )
            precomputed_rewards[(trow, tcol, prow, pcol)] = reward
            transpose_rewards[(tcol, trow, pcol, prow)] = reward

        num_pos = pred_cell_grid.shape[0] * pred_cell_grid.shape[1]
        num_true = true_cell_grid.shape[0] * true_cell_grid.shape[1]

        true_row_nums, pred_row_nums, row_pos_match_score = self._align_2d_outer(
            true_cell_grid.shape[:2], pred_cell_grid.shape[:2], precomputed_rewards
        )
        true_column_nums, pred_column_nums, col_pos_match_score = self._align_2d_outer(
            true_cell_grid.shape[:2][::-1],
            pred_cell_grid.shape[:2][::-1],
            transpose_rewards,
        )

        pos_match_score_upper_bound = min(row_pos_match_score, col_pos_match_score)
        upper_bound_score, _, _ = self._compute_fscore(
            pos_match_score_upper_bound, num_true, num_pos
        )

        positive_match_score = 0.0
        for true_row_num, pred_row_num in zip(true_row_nums, pred_row_nums):
            for true_column_num, pred_column_num in zip(
                true_column_nums, pred_column_nums
            ):
                positive_match_score += precomputed_rewards[
                    (true_row_num, true_column_num, pred_row_num, pred_column_num)
                ]

        fscore, precision, recall = self._compute_fscore(
            positive_match_score, num_true, num_pos
        )
        return fscore, precision, recall, upper_bound_score

    def _lcs_similarity(self, string1: str, string2: str) -> float:
        r""" """
        if len(string1) == 0 and len(string2) == 0:
            return 1.0

        cached_value = self._lcs_cache.get(string1, string2)
        if cached_value is not None:
            return cached_value

        matcher = SequenceMatcher(None, string1, string2)
        lcs = "".join(
            string1[block.a : (block.a + block.size)]
            for block in matcher.get_matching_blocks()
        )
        normalized_lcs = 2 * len(lcs) / (len(string1) + len(string2))

        self._lcs_cache.set(string1, string2, normalized_lcs)
        return normalized_lcs

    def _rect_area(self, rect: list[float]) -> float:
        return max(0, rect[2] - rect[0]) * max(0, rect[3] - rect[1])

    def _iou(self, bbox1: list[float], bbox2: list[float]) -> float:
        left = max(bbox1[0], bbox2[0])
        top = max(bbox1[1], bbox2[1])
        right = min(bbox1[2], bbox2[2])
        bottom = min(bbox1[3], bbox2[3])

        intersection = [left, top, right, bottom]
        intersection_area = self._rect_area(intersection)
        if intersection_area == 0:
            return 0.0

        union_area = self._rect_area(bbox1) + self._rect_area(bbox2) - intersection_area
        if union_area <= 0:
            return 0.0

        return intersection_area / union_area

    def _cells_to_grid(self, cells: list[dict[str, Any]], key: str) -> list[list[Any]]:
        if len(cells) == 0:
            return [[]]

        num_rows = max(max(cell["row_nums"]) for cell in cells) + 1
        num_columns = max(max(cell["column_nums"]) for cell in cells) + 1
        cell_grid = np.zeros((num_rows, num_columns)).tolist()

        for cell in cells:
            for row_num in cell["row_nums"]:
                for column_num in cell["column_nums"]:
                    cell_grid[row_num][column_num] = cell[key]

        return cell_grid

    def _cells_to_relspan_grid(
        self, cells: list[dict[str, Any]]
    ) -> list[list[list[int]]]:
        if len(cells) == 0:
            return [[]]

        num_rows = max(max(cell["row_nums"]) for cell in cells) + 1
        num_columns = max(max(cell["column_nums"]) for cell in cells) + 1
        cell_grid = np.zeros((num_rows, num_columns)).tolist()

        for cell in cells:
            min_row_num = min(cell["row_nums"])
            min_column_num = min(cell["column_nums"])
            max_row_num = max(cell["row_nums"]) + 1
            max_column_num = max(cell["column_nums"]) + 1
            for row_num in cell["row_nums"]:
                for column_num in cell["column_nums"]:
                    cell_grid[row_num][column_num] = [
                        min_column_num - column_num,
                        min_row_num - row_num,
                        max_column_num - column_num,
                        max_row_num - row_num,
                    ]

        return cell_grid

    def _grits_top(
        self, true_relative_span_grid: np.ndarray, pred_relative_span_grid: np.ndarray
    ) -> tuple[float, float, float, float]:
        return self._factored_2dmss(
            true_relative_span_grid, pred_relative_span_grid, self._iou
        )

    def _grits_con(
        self, true_text_grid: np.ndarray, pred_text_grid: np.ndarray
    ) -> tuple[float, float, float, float]:
        return self._factored_2dmss(
            true_text_grid, pred_text_grid, self._lcs_similarity
        )

    def _grits_loc(
        self, true_bbox_grid: np.ndarray, pred_bbox_grid: np.ndarray
    ) -> tuple[float, float, float, float]:
        return self._factored_2dmss(true_bbox_grid, pred_bbox_grid, self._iou)

    def grits_from_html(
        self,
        true_html: str,
        pred_html: str,
        enable_topology: bool,
        enable_content: bool,
    ) -> dict[str, float | int]:
        metrics: dict[str, float | int] = {}

        true_cells = self.html_to_cells(true_html)
        pred_cells = self.html_to_cells(pred_html)

        if enable_topology:
            true_topology_grid = np.array(self._cells_to_relspan_grid(true_cells))
            pred_topology_grid = np.array(self._cells_to_relspan_grid(pred_cells))
            (
                metrics["grits_top"],
                metrics["grits_precision_top"],
                metrics["grits_recall_top"],
                metrics["grits_top_upper_bound"],
            ) = self._grits_top(true_topology_grid, pred_topology_grid)

        if enable_content:
            true_text_grid = np.array(
                self._cells_to_grid(true_cells, key="cell_text"), dtype=object
            )
            pred_text_grid = np.array(
                self._cells_to_grid(pred_cells, key="cell_text"), dtype=object
            )
            (
                metrics["grits_con"],
                metrics["grits_precision_con"],
                metrics["grits_recall_con"],
                metrics["grits_con_upper_bound"],
            ) = self._grits_con(true_text_grid, pred_text_grid)

        return metrics

    def grits_from_cells(
        self,
        true_cells: list[dict[str, Any]],
        pred_cells: list[dict[str, Any]],
        enable_topology: bool,
        enable_content: bool,
        enable_location: bool,
    ) -> dict[str, float | int]:
        metrics: dict[str, float | int] = {}

        if enable_topology:
            true_topology_grid = np.array(self._cells_to_relspan_grid(true_cells))
            pred_topology_grid = np.array(self._cells_to_relspan_grid(pred_cells))
            (
                metrics["grits_top"],
                metrics["grits_precision_top"],
                metrics["grits_recall_top"],
                metrics["grits_top_upper_bound"],
            ) = self._grits_top(true_topology_grid, pred_topology_grid)

        if enable_content:
            true_text_grid = np.array(
                self._cells_to_grid(true_cells, key="cell_text"), dtype=object
            )
            pred_text_grid = np.array(
                self._cells_to_grid(pred_cells, key="cell_text"), dtype=object
            )
            (
                metrics["grits_con"],
                metrics["grits_precision_con"],
                metrics["grits_recall_con"],
                metrics["grits_con_upper_bound"],
            ) = self._grits_con(true_text_grid, pred_text_grid)

        if enable_location:
            true_bbox_grid = np.array(
                self._cells_to_grid(true_cells, key="bbox"), dtype=object
            )
            pred_bbox_grid = np.array(
                self._cells_to_grid(pred_cells, key="bbox"), dtype=object
            )
            (
                metrics["grits_loc"],
                metrics["grits_precision_loc"],
                metrics["grits_recall_loc"],
                metrics["grits_loc_upper_bound"],
            ) = self._grits_loc(true_bbox_grid, pred_bbox_grid)

        return metrics

    @staticmethod
    def cells_to_html(cells: list[dict[str, Any]]) -> str:
        """
        Serialize table cells into a canonical HTML table.

        The input is expected to use the evaluation/postprocess/GriTS cell schema:
        ``row_nums`` and ``column_nums`` define the occupied grid locations,
        ``cell_text`` holds the text content, and ``header`` marks header cells.

        For compatibility with ``html_to_cells()``, this serializer also accepts the
        smaller parser schema where the header flag is stored in
        ``is_column_header``. The emitted HTML is canonicalized for the parser in
        this module: reparsing it with ``html_to_cells()`` yields the same cell
        topology, header flags, and text content.
        """
        if len(cells) == 0:
            return str(ET.tostring(ET.Element("table"), encoding="unicode"))

        normalized_cells = []
        for cell in cells:
            normalized_cells.append(
                {
                    "row_nums": sorted(cell["row_nums"]),
                    "column_nums": sorted(cell["column_nums"]),
                    "is_column_header": bool(
                        cell.get("header", cell.get("is_column_header", False))
                    ),
                    "cell_text": cell.get("cell_text", ""),
                }
            )

        normalized_cells.sort(
            key=lambda cell: (min(cell["row_nums"]), min(cell["column_nums"]))
        )

        cells_starting_by_row = defaultdict(list)
        for cell in normalized_cells:
            cells_starting_by_row[min(cell["row_nums"])].append(cell)

        table = ET.Element("table")
        tbody = ET.SubElement(table, "tbody")
        num_rows = max(max(cell["row_nums"]) for cell in normalized_cells) + 1
        for row_num in range(num_rows):
            row = ET.SubElement(tbody, "tr")
            row_cells = sorted(
                cells_starting_by_row.get(row_num, []),
                key=lambda cell: min(cell["column_nums"]),
            )
            for cell in row_cells:
                attrib = {}
                colspan = len(cell["column_nums"])
                if colspan > 1:
                    attrib["colspan"] = str(colspan)
                rowspan = len(cell["row_nums"])
                if rowspan > 1:
                    attrib["rowspan"] = str(rowspan)
                tag = "th" if cell["is_column_header"] else "td"
                element = ET.SubElement(row, tag, attrib=attrib)
                element.text = cell["cell_text"]

        return str(ET.tostring(table, encoding="unicode", short_empty_elements=False))

    @staticmethod
    def html_to_cells(table_html: str) -> list[dict[str, Any]]:
        tree = ET.fromstring(table_html)
        table_cells = []

        occupied_columns_by_row: defaultdict[int, set[int]] = defaultdict(set)
        current_row = -1
        stack = [(tree, False)]

        while stack:
            current, in_header = stack.pop()

            if current.tag == "tr":
                current_row += 1

            if current.tag in {"td", "th"}:
                colspan = int(current.attrib.get("colspan", 1))
                rowspan = int(current.attrib.get("rowspan", 1))
                row_nums = list(range(current_row, current_row + rowspan))

                try:
                    max_occupied_column = max(occupied_columns_by_row[current_row])
                    current_column = min(
                        set(range(max_occupied_column + 2)).difference(
                            occupied_columns_by_row[current_row]
                        )
                    )
                except ValueError:
                    current_column = 0

                column_nums = list(range(current_column, current_column + colspan))
                for row_num in row_nums:
                    occupied_columns_by_row[row_num].update(column_nums)

                table_cells.append(
                    {
                        "row_nums": row_nums,
                        "column_nums": column_nums,
                        "is_column_header": current.tag == "th" or in_header,
                        "cell_text": " ".join(current.itertext()),
                    }
                )

            children = list(current)
            for child in reversed(children):
                stack.append((child, in_header or current.tag in {"th", "thead"}))

        return table_cells

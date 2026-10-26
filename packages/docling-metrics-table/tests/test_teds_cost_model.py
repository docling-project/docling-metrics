import random

import pytest
from apted import APTED
from docling_metrics_table.docling_metrics_table import (
    TableMetric,
    TableMetricBracketInputSample,
    TableMetricHTMLInputSample,
    TableMetricKind,
    TEDSCostModel,
)
from docling_metrics_table.utils.teds import CustomConfig, TableTree, TEDScorer
from lxml import html


def _table(*rows: list[str]) -> str:
    cells = ["".join(f"<td>{cell}</td>" for cell in row) for row in rows]
    return "<table>" + "".join(f"<tr>{row}</tr>" for row in cells) + "</table>"


def _tree(html_str: str) -> TableTree:
    return TEDScorer().html_to_table_tree(html.fromstring(html_str), convert_cell=True)


def _tree_size(tree: TableTree) -> int:
    return 1 + sum(_tree_size(child) for child in tree.children)


def _cell_tree(tag: str, colspan: int, rowspan: int, text: str) -> TableTree:
    cell = TableTree(tag, colspan, rowspan, list(text))
    return TableTree("table", None, None, None, TableTree("tr", None, None, None, cell))


def _distances(
    gt: TableTree, pred: TableTree, cost_model: TEDSCostModel
) -> tuple[float, float]:
    r"""
    Edit distance of the C++ metric and of apted for the same two trees. The C++ side only reports
    the score, so its distance is recovered with the normalization it applies.
    """
    metric = TableMetric(metrics=[TableMetricKind.TEDS], teds_cost_model=cost_model)
    evaluation = metric.evaluate_sample(
        TableMetricBracketInputSample(
            id="t", bracket_a=pred.bracket(), bracket_b=gt.bracket()
        )
    )
    assert evaluation.teds is not None
    size = max(evaluation.teds.tree_a_size, evaluation.teds.tree_b_size)
    assert size == max(_tree_size(gt), _tree_size(pred))
    cpp = (1.0 - evaluation.teds.teds) * size
    return cpp, APTED(pred, gt, CustomConfig()).compute_edit_distance()


def _assert_same_distance(gt: TableTree, pred: TableTree) -> float:
    cpp, expected = _distances(gt, pred, TEDSCostModel.LEVENSHTEIN)
    assert cpp == pytest.approx(expected, abs=1e-9)
    return cpp


_HTML_CASES = {
    "identical": (_table(["abc", "d"]), _table(["abc", "d"])),
    "one_char_off": (_table(["abcdef"]), _table(["abcdxf"])),
    "completely_different": (_table(["abcdef"]), _table(["uvwxyz"])),
    "different_length": (_table(["abc"]), _table(["abcdefgh"])),
    "empty_vs_text": (_table([""]), _table(["abc"])),
    "text_vs_empty": (_table(["abc"]), _table([""])),
    "both_empty": (_table([""]), _table([""])),
    "colspan_mismatch": (
        "<table><tr><td colspan='2'>ab</td></tr></table>",
        "<table><tr><td>ab</td></tr></table>",
    ),
    "rowspan_mismatch": (
        "<table><tr><td rowspan='2'>ab</td></tr></table>",
        "<table><tr><td rowspan='3'>ab</td></tr></table>",
    ),
    "cjk": (_table(["日本語のテキスト"]), _table(["日本话のテキスト"])),
    "combining": (_table(["école"]), _table(["école"])),
    "emoji": (_table(["a😀b"]), _table(["a😁b"])),
    "escaped_repr_chars": (
        _table(["a\tb​c'd\"e"]),
        _table(["a\tb​c'd\"x"]),
    ),
    "braces_backslashes": (
        _table(["a{b}\\c", "{"]),
        _table(["a{x}\\c", "}\\\\"]),
    ),
    "nested_markup": (
        _table(["a<b>x</b>c"]),
        _table(["a<b>y</b>c"]),
    ),
    "nested_markup_vs_plain": (_table(["a<b>x</b>c"]), _table(["axc"])),
    "missing_row": (_table(["a", "b"], ["c", "d"]), _table(["a", "b"])),
    "extra_row": (_table(["a", "b"]), _table(["a", "b"], ["c", "d"])),
    "missing_cell": (_table(["abc", "def"]), _table(["abc"])),
    "row_with_edits": (
        _table(["abc", "def"], ["ghi", "jkl"]),
        _table(["abx", "def"], ["gh", "zzz"]),
    ),
}


@pytest.mark.parametrize("name", _HTML_CASES)
def test_levenshtein_distance_matches_apted(name: str) -> None:
    gt, pred = _HTML_CASES[name]
    _assert_same_distance(_tree(gt), _tree(pred))


def test_levenshtein_cost_values() -> None:
    # A single rename of the cell: the cost is the normalized Levenshtein distance
    one_off = _assert_same_distance(
        _tree(_table(["abcdef"])), _tree(_table(["abcdxf"]))
    )
    assert one_off == pytest.approx(1 / 6)
    different = _assert_same_distance(
        _tree(_table(["abcdef"])), _tree(_table(["uvwxyz"]))
    )
    assert different == pytest.approx(1.0)
    both_empty = _assert_same_distance(_tree(_table([""])), _tree(_table([""])))
    assert both_empty == 0.0


def test_levenshtein_th_vs_td() -> None:
    # The HTML conversion folds th into td, so this needs trees built by hand
    cost = _assert_same_distance(
        _cell_tree("td", 1, 1, "abc"), _cell_tree("th", 1, 1, "abc")
    )
    assert cost == pytest.approx(1.0)


def test_levenshtein_distance_random() -> None:
    rng = random.Random(7)
    alphabet = "ab{}\\'\"\u00e9\u65e5\u200b"

    def cell() -> str:
        return "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 6)))

    for _ in range(30):
        rows = [[cell() for _ in range(rng.randint(1, 3))] for _ in range(2)]
        pred = [[cell() for _ in row] for row in rows]
        _assert_same_distance(_tree(_table(*rows)), _tree(_table(*pred)))


def test_cost_models_differ_on_graded_cells() -> None:
    gt = _table(["abcdef", "ghijkl"])
    one_off = _table(["abcdxf", "ghijkl"])
    different = _table(["uvwxyz", "ghijkl"])

    def teds(cost_model: TEDSCostModel, pred: str) -> float:
        metric = TableMetric(metrics=[TableMetricKind.TEDS], teds_cost_model=cost_model)
        sample = TableMetricHTMLInputSample(id="t", html_a=gt, html_b=pred)
        evaluation = metric.evaluate_sample(sample)
        assert evaluation.teds is not None
        return evaluation.teds.teds

    # Unit cost: one wrong character costs as much as a completely wrong cell
    assert teds(TEDSCostModel.UNIT, one_off) == teds(TEDSCostModel.UNIT, different)
    # Levenshtein cost: grades them
    assert teds(TEDSCostModel.LEVENSHTEIN, one_off) > teds(
        TEDSCostModel.LEVENSHTEIN, different
    )
    # Unit is the default
    default = TableMetric(metrics=[TableMetricKind.TEDS])
    sample = TableMetricHTMLInputSample(id="t", html_a=gt, html_b=one_off)
    default_teds = default.evaluate_sample(sample).teds
    assert default_teds is not None
    assert default_teds.teds == teds(TEDSCostModel.UNIT, one_off)


def test_unknown_cost_model_is_rejected() -> None:
    from docling_metrics_table import docling_metric_table_cpp

    with pytest.raises(ValueError):
        docling_metric_table_cpp.TEDSManager("nope")


@pytest.mark.parametrize("cost_model", list(TEDSCostModel))
@pytest.mark.parametrize("structure_only", [True, False])
def test_header_aware(cost_model: TEDSCostModel, structure_only: bool) -> None:
    headed = "<table><tr><th>a</th><th>b</th></tr><tr><td>c</td><td>d</td></tr></table>"
    swapped = headed.replace("<th>b</th>", "<td>b</td>")
    metric = TableMetric(metrics=[TableMetricKind.TEDS], teds_cost_model=cost_model)

    def teds(pred: str, header_aware: bool) -> float:
        sample = TableMetricHTMLInputSample(
            id="t",
            html_a=headed,
            html_b=pred,
            structure_only=structure_only,
            header_aware=header_aware,
        )
        evaluation = metric.evaluate_sample(sample)
        assert evaluation.teds is not None
        return evaluation.teds.teds

    def py_teds(pred: str, header_aware: bool) -> float:
        return TEDScorer().teds(
            html.fromstring(headed), html.fromstring(pred), structure_only, header_aware
        )

    for score in (teds, py_teds):
        assert score(swapped, header_aware=False) == 1.0
        assert score(swapped, header_aware=True) < 1.0
        assert score(headed, header_aware=True) == 1.0

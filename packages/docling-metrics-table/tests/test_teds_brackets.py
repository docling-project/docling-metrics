import signal
import subprocess
import sys
import textwrap

import pytest
from docling_metrics_table.utils.teds import TEDScorer


def _structural_bracket_stats(bracket: str) -> tuple[int, int, int]:
    r"""
    Count the structural brackets of a bracket notation string.

    Mirrors the escape rule of the C++ tokenizer (BracketNotationParser::get_tokens): a bracket
    that is preceded by the escape character belongs to a label and not to the tree structure.

    Returns:
    -------
    Tuple with (number of bracket pairs, minimum nesting depth, final nesting depth).
    A well formed tree has one bracket pair per node, a minimum depth of 0 and a final depth of 0.
    """
    pairs = 0
    depth = 0
    min_depth = 0
    previous = ""
    for char in bracket:
        if previous != "\\":
            if char == "{":
                depth += 1
                pairs += 1
            elif char == "}":
                depth -= 1
                min_depth = min(min_depth, depth)
        previous = char
    return pairs, min_depth, depth


# Imports and assertion helpers for the isolated interpreters started by `_run_isolated`.
_ISOLATED_PREAMBLE = """
from docling_metrics_table import docling_metric_table_cpp
from docling_metrics_table.docling_metrics_table import (
    TableMetric,
    TableMetricHTMLInputSample,
    TableMetricKind,
)


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def mark(step):
    print("passed: " + step, flush=True)

"""


def _run_isolated(name: str, data: str, body: str) -> str | None:
    r"""
    Run `body` in a fresh interpreter and return a report if it failed, None otherwise.

    Malformed bracket notation currently segfaults inside the C++ extension. A SIGSEGV is not a
    Python exception, so running these checks in the pytest process would take the whole session
    down and hide the results of every other test. The child reports its progress on stdout, so a
    crash still tells us which check it survived.
    """
    script = _ISOLATED_PREAMBLE + textwrap.dedent(data) + textwrap.dedent(body)
    process = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=180,
    )
    report = f"--- stdout ---\n{process.stdout}--- stderr ---\n{process.stderr}"
    if process.returncode < 0:
        signal_name = signal.Signals(-process.returncode).name
        return f"[{name}] The child interpreter died on {signal_name}\n{report}"
    if process.returncode != 0:
        return (
            f"[{name}] The child interpreter exited with {process.returncode}\n{report}"
        )
    return None


def test_teds_matching_brackets():
    r"""
    Cell text that contains the structure characters of the bracket notation.

    The braces of a table cell must stay inside the label of their node. Today they are copied
    unescaped into the bracket notation, so a cell such as `}}}}}}{{{{{{` has matching braces, it
    passes the counter based validation of the C++ parser and then crashes it with a SIGSEGV. Cells
    with fewer braces do not crash but silently produce a different tree and therefore a wrong
    score.
    """
    # Simple hard-coded tables. Every one of them has 5 nodes: table, tbody, tr, td, td.
    expected_tree_size = 5
    html_data = {
        "GT_HTML": "<table><tbody><tr><td>ok</td><td>fine</td></tr></tbody></table>",
        # Matching but not properly nested braces: the SIGSEGV reproducer. There are more closing
        # braces than open nodes, so the parser pops its node stack below the root.
        "CRASH_HTML": "<table><tbody><tr><td>}}}}}}{{{{{{</td><td>fine</td></tr></tbody></table>",
        # Same shape and same cell text length, without braces.
        "CONTROL_HTML": "<table><tbody><tr><td>ABCDEFGHIJKL</td><td>fine</td></tr></tbody></table>",
        # Properly nested braces: no crash, but the tree silently changes.
        "SILENT_HTML": "<table><tbody><tr><td>{</td><td>}</td></tr></tbody></table>",
        "SILENT_CONTROL_HTML": "<table><tbody><tr><td>a</td><td>b</td></tr></tbody></table>",
    }

    # Every part is run and reported, so that one failure does not hide the others.
    failures: list[str] = []

    def record(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    def record_isolated(name: str, data: str, body: str) -> None:
        report = _run_isolated(name, data, body)
        if report is not None:
            failures.append(report)

    # Part 1: The Python serializer must not leak the braces of a cell into the tree structure.
    teds_scorer = TEDScorer()
    for name, html_str in html_data.items():
        bracket = teds_scorer.html_to_bracket(html_str)
        pairs, min_depth, final_depth = _structural_bracket_stats(bracket)
        record(
            pairs == expected_tree_size,
            f"[serializer] Wrong number of nodes in the bracket of {name}. Expected {expected_tree_size}, got {pairs}: {bracket}",
        )
        record(
            min_depth == 0,
            f"[serializer] The nesting depth of the bracket of {name} drops below 0: {bracket}",
        )
        record(
            final_depth == 0,
            f"[serializer] Unbalanced bracket for {name}, final nesting depth is {final_depth}: {bracket}",
        )

    # The braces of the cell text must be escaped, as documented in bracket_notation_parser.h
    crash_bracket = teds_scorer.html_to_bracket(html_data["CRASH_HTML"])
    escaped_left = crash_bracket.count("\\{")
    escaped_right = crash_bracket.count("\\}")
    record(
        escaped_left == 6,
        f"[serializer] Expected 6 escaped left braces in the cell text, got {escaped_left}: {crash_bracket}",
    )
    record(
        escaped_right == 6,
        f"[serializer] Expected 6 escaped right braces in the cell text, got {escaped_right}: {crash_bracket}",
    )

    # The cell text is irrelevant for the structure-only representation.
    record(
        teds_scorer.html_to_bracket(html_data["GT_HTML"], structure_only=True)
        == teds_scorer.html_to_bracket(html_data["CRASH_HTML"], structure_only=True),
        "[serializer] The cell text changed the structure-only bracket notation",
    )

    # Part 2: Malformed bracket notation must be reported as an error and never crash the process.
    record_isolated(
        "bracket notation",
        "",
        """
        malformed_brackets = [
            "}{",             # matching braces, wrong nesting
            "{x}{y}",         # two roots
            "{x",             # unclosed root
            "x}",             # no root
            "",               # nothing at all
            "{a}}{b{c}}{d",   # matching braces, pops below the root
            "{a" + chr(92),   # trailing escape character
        ]
        teds_manager = docling_metric_table_cpp.TEDSManager()
        for malformed in malformed_brackets:
            evaluation = teds_manager.evaluate_sample("b", "{a}", malformed)
            check(
                evaluation.error_id != 0,
                "Accepted malformed input B: " + repr(malformed),
            )
            mark("input B " + repr(malformed))

            evaluation = teds_manager.evaluate_sample("a", malformed, "{a}")
            check(
                evaluation.error_id != 0,
                "Accepted malformed input A: " + repr(malformed),
            )
            mark("input A " + repr(malformed))

        # The C++ parser keeps its node stack as a member and reuses it for every sample, so the
        # same manager must still evaluate a valid sample correctly after all of the above.
        evaluation = teds_manager.evaluate_sample("valid", "{a}", "{a}")
        check(evaluation.error_id == 0, "Rejected valid input: " + evaluation.error_msg)
        check(
            evaluation.teds == 1.0,
            "Wrong TEDS for identical trees: " + str(evaluation.teds),
        )
        mark("valid input after malformed ones")
        """,
    )

    # Part 3: The same through the public HTML API.
    record_isolated(
        "html input",
        "".join(f"{name} = {html_str!r}\n" for name, html_str in html_data.items()),
        """
        table_metric = TableMetric(metrics=[TableMetricKind.TEDS])

        def evaluate(sample_id, html_a, html_b, structure_only=False):
            sample = TableMetricHTMLInputSample(
                id=sample_id,
                html_a=html_a,
                html_b=html_b,
                structure_only=structure_only,
            )
            return table_metric.evaluate_sample(sample).teds

        def check_tree_sizes(step, evaluation):
            check(
                evaluation.tree_a_size == 5,
                step + ": wrong tree A size " + str(evaluation.tree_a_size),
            )
            check(
                evaluation.tree_b_size == 5,
                step + ": wrong tree B size " + str(evaluation.tree_b_size),
            )

        # Braces in the cell text must neither crash nor add nodes to the tree.
        crash = evaluate("crash", GT_HTML, CRASH_HTML)
        check_tree_sizes("braces in cell text", crash)
        mark("braces in cell text")

        # The rename cost of the C++ cost model is a unit cost, so a table that differs from the
        # ground truth only in its cell text gets the same score, whatever that text is.
        control = evaluate("control", GT_HTML, CONTROL_HTML)
        check_tree_sizes("brace free control", control)
        check(
            crash.teds == control.teds,
            "Braces changed the TEDS score: "
            + str(crash.teds)
            + " != "
            + str(control.teds),
        )
        mark("braces score like ordinary characters")

        identical = evaluate("identical", CRASH_HTML, CRASH_HTML)
        check_tree_sizes("identical tables", identical)
        check(
            identical.teds == 1.0,
            "Wrong TEDS for identical tables: " + str(identical.teds),
        )
        mark("identical tables with braces")

        # Properly nested braces do not crash, they silently build a different tree.
        silent = evaluate("silent", GT_HTML, SILENT_HTML)
        check_tree_sizes("nested braces", silent)
        silent_control = evaluate("silent_control", GT_HTML, SILENT_CONTROL_HTML)
        check(
            silent.teds == silent_control.teds,
            "Nested braces changed the TEDS score: "
            + str(silent.teds)
            + " != "
            + str(silent_control.teds),
        )
        mark("nested braces")

        # Without the cell text both tables are identical.
        structure = evaluate("structure", GT_HTML, CRASH_HTML, structure_only=True)
        check_tree_sizes("structure only", structure)
        check(
            structure.teds == 1.0,
            "Wrong structure-only TEDS: " + str(structure.teds),
        )
        mark("structure only")
        """,
    )

    if failures:
        pytest.fail("\n\n".join(failures), pytrace=False)


if __name__ == "__main__":
    test_teds_matching_brackets()

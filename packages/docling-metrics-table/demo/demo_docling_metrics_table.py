from docling_metrics_table import (
    TableMetric,
    TableMetricBracketInputSample,
    TableMetricHTMLInputSample,
    TableMetricSampleEvaluation,
)

# Input sample in bracket notation
bracket_sample = TableMetricBracketInputSample(
    id="s1",
    bracket_a="{x{a}{b}}",
    bracket_b="{x{a}{c}}",
)

table_metric = TableMetric()
bracket_sample_evaluation: TableMetricSampleEvaluation = table_metric.evaluate_sample(
    bracket_sample
)
print(f"TEDS with bracket input: {bracket_sample_evaluation}")


# Input sample in HTML notation
html_a = r"""
<table>
    <tr>
        <td colspan="2">This cell spans two columns with some dummy text</td>
    </tr>
    <tr>
        <td>Cell 2-1: More dummy text here</td>
        <td>Cell 2-2: Additional content</td>
    </tr>
</table>
"""

html_b = r"""
<table>
    <tr>
        <td>Dummy text</td>
        <td>Cell 1-2: Regular cell content</td>
    </tr>
    <tr>
        <td>Cell 2-1: More dummy text here</td>
        <td>Cell 2-2: Additional content</td>
    </tr>
</table>
"""

html_sample = TableMetricHTMLInputSample(
    id="s1",
    html_a=html_a,
    html_b=html_b,
    structure_only=False,
)
html_evaluation: TableMetricSampleEvaluation = table_metric.evaluate_sample(html_sample)
print(f"TEDS with HTML input: {html_evaluation}")

from docling_metrics_text import (
    TextMetrics,
    TextPairEvaluation,
    TextPairSample,
)

# Example 1: Compare two similar texts
sample_1 = TextPairSample(
    id="s1",
    text_a="The quick brown fox jumps over the lazy dog.",
    text_b="The fast brown fox leaps over the lazy dog.",
)

text_metrics = TextMetrics()
evaluation_1: TextPairEvaluation = text_metrics.evaluate_sample(sample_1)
print(f"Sample 1 - Similar texts:\n{evaluation_1}\n")


# Example 2: Compare two very different texts
sample_2 = TextPairSample(
    id="s2",
    text_a="Machine learning is a subset of artificial intelligence.",
    text_b="The weather forecast predicts rain tomorrow afternoon.",
)

evaluation_2: TextPairEvaluation = text_metrics.evaluate_sample(sample_2)
print(f"Sample 2 - Different texts:\n{evaluation_2}\n")

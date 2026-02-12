import nltk
from docling_metrics_core.base_types import (
    BaseInputSample,
    BaseMetric,
    BaseSampleResult,
)
from nltk import edit_distance, word_tokenize

# Download the NLTK data
nltk.download("popular", quiet=True)
nltk.download("punkt_tab", quiet=True)


class TextPairSample(BaseInputSample):
    text_a: str
    text_b: str


class EditDistanceSampleEvaluation(BaseSampleResult):
    edit_distance: float


class EditDistanceMetric(BaseMetric):
    r"""
    Edit distance metric is normalized Levenshtein over the TreeBank tokens of the 2 texts
    """

    def __init__(self) -> None:
        r""" """

    def evaluate_sample(
        self,
        sample: TextPairSample,
    ) -> EditDistanceSampleEvaluation:
        tokens_a = word_tokenize(sample.text_a)
        tokens_b = word_tokenize(sample.text_b)
        ed_metric = edit_distance(tokens_a, tokens_b)
        result = EditDistanceSampleEvaluation(id=sample.id, edit_distance=ed_metric)
        return result

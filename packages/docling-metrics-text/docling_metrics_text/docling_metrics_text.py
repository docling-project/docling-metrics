from typing import Iterable

import evaluate
import nltk
from docling_metrics_core.base_types import (
    BaseAggregateResult,
    BaseInputSample,
    BaseMetric,
    BaseSampleResult,
)
from nltk import edit_distance, word_tokenize
from nltk.metrics import f_measure, precision, recall
from nltk.translate import meteor_score


class TextPairSample(BaseInputSample):
    text_a: str
    text_b: str


class TextPairEvaluation(BaseSampleResult):
    f1_score: float
    precision_score: float
    recall_score: float
    edit_distance_score: float
    bleu_score: float
    meteor_score: float


class TextDatasetEvaluation(BaseAggregateResult):
    pass


class TextMetrics(BaseMetric):
    r"""
    Various text metrics
    """

    def __init__(self) -> None:
        r""" """
        # Download the NLTK data
        nltk.download("popular", quiet=True)
        nltk.download("punkt_tab", quiet=True)

        self._bleu_eval = evaluate.load("bleu")

    def evaluate_sample(
        self,
        sample: TextPairSample,
    ) -> TextPairEvaluation:
        r"""
        Compute text metrics for the input sample
        """
        # Tokenize the inputs
        tokens_a = self._word_tokenize(sample.text_a)
        tokens_b = self._word_tokenize(sample.text_b)
        tokens_a_set = set(tokens_a)
        tokens_b_set = set(tokens_b)

        # Compute metrics
        f1_score = f_measure(tokens_a_set, tokens_b_set) or -1.0
        precision_score = precision(tokens_a_set, tokens_b_set) or -1.0
        recall_score = recall(tokens_a_set, tokens_b_set) or -1.0

        # edit_distance_score is a normalized Levenshtein distance
        edit_distance_score = edit_distance(tokens_a, tokens_b) / max(
            len(tokens_a), len(tokens_b)
        )
        meteor = meteor_score.meteor_score([tokens_a], tokens_b)

        # BLEU implementation
        result = self._bleu_eval.compute(
            predictions=[sample.text_a], references=[[sample.text_b]]
        )
        bleu_score = -1 if result is None else result["bleu"]

        result = TextPairEvaluation(
            id=sample.id,
            f1_score=f1_score,
            precision_score=precision_score,
            recall_score=recall_score,
            edit_distance_score=edit_distance_score,
            meteor_score=meteor,
            bleu_score=bleu_score,
        )
        return result

    def aggregate(self, results: Iterable[TextPairSample]):
        """Trivial implementation"""
        return None

    def evaluate_dataset(
        self, sample_pairs: Iterable[TextPairSample]
    ) -> TextDatasetEvaluation:
        """Trivial implementation"""
        return TextDatasetEvaluation(sample_count=0)

    def _word_tokenize(self, text: str) -> list[str]:
        r"""Tokenize the input string using the TreeBank tokenizer"""
        # TODO: Replace with the C++ implemenation when ready
        return word_tokenize(text)

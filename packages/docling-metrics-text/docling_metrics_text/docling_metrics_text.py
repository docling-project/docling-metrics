import logging
from enum import Enum
from typing import Iterable
from uuid import uuid4

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

from . import docling_metrics_text_cpp  # type: ignore

_log = logging.getLogger(__name__)


class TextMetricsMode(str, Enum):
    PYTHON = "Python"
    CPP = "C++"


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

    def __init__(
        self, mode: TextMetricsMode = TextMetricsMode.CPP, error_score: float = -1
    ) -> None:
        r""" """
        self._error_score = (
            error_score  # Returned value in case the score cannot be computed
        )
        self._mode = mode

        # Download the NLTK data
        nltk.download("popular", quiet=True)
        nltk.download("punkt_tab", quiet=True)

        self._bleu_eval = evaluate.load(
            "bleu", experiment_id=str(uuid4()), keep_in_memory=True
        )

        if self._mode == TextMetricsMode.CPP:
            self._text_manager = docling_metrics_text_cpp.TextManager()

    def evaluate_sample(
        self,
        sample: TextPairSample,
    ) -> TextPairEvaluation:
        r"""
        Python implementation to compute text metrics for the input sample
        """
        # Tokenize the inputs
        tokens_a, tokens_b, tokens_a_set, tokens_b_set = self._tokenize_pair(
            sample.text_a, sample.text_b
        )

        # Compute metrics
        f1_score = self._compute_f1(tokens_a_set, tokens_b_set)
        precision_score = self._compute_precision(tokens_a_set, tokens_b_set)
        recall_score = self._compute_recall(tokens_a_set, tokens_b_set)
        edit_distance_score = self._compute_edit_distance(tokens_a, tokens_b)
        meteor_score_value = self._compute_meteor(tokens_a, tokens_b)
        bleu_score = self._compute_bleu(sample.text_a, sample.text_b)

        result = TextPairEvaluation(
            id=sample.id,
            f1_score=f1_score,
            precision_score=precision_score,
            recall_score=recall_score,
            edit_distance_score=edit_distance_score,
            meteor_score=meteor_score_value,
            bleu_score=bleu_score,
        )
        return result

    def aggregate(self, results: Iterable[TextPairEvaluation]):
        """Trivial implementation"""
        return None

    def evaluate_dataset(
        self, sample_pairs: Iterable[TextPairSample]
    ) -> TextDatasetEvaluation:
        """Trivial implementation"""
        return TextDatasetEvaluation(sample_count=0)

    def _word_tokenize(self, text: str) -> list[str]:
        r"""Tokenize the input string using the TreeBank tokenizer"""
        return word_tokenize(text)

    def _tokenize_pair(
        self, text_a: str, text_b: str
    ) -> tuple[list[str], list[str], set[str], set[str]]:
        r"""
        Tokenize a pair of texts and create sets for efficient comparison.

        Args:
            text_a: First text to tokenize
            text_b: Second text to tokenize

        Returns:
            Tuple of (tokens_a, tokens_b, tokens_a_set, tokens_b_set)
        """
        tokens_a = self._word_tokenize(text_a)
        tokens_b = self._word_tokenize(text_b)
        tokens_a_set = set(tokens_a)
        tokens_b_set = set(tokens_b)
        return tokens_a, tokens_b, tokens_a_set, tokens_b_set

    def _compute_f1(self, tokens_a_set: set[str], tokens_b_set: set[str]) -> float:
        r"""
        Compute F1 score between two token sets.

        Args:
            tokens_a_set: First set of tokens
            tokens_b_set: Second set of tokens

        Returns:
            F1 score, or self._error_score if computation fails
        """
        try:
            score = f_measure(tokens_a_set, tokens_b_set)
            return self._error_score if score is None else score
        except Exception:
            return self._error_score

    def _compute_precision(
        self, tokens_a_set: set[str], tokens_b_set: set[str]
    ) -> float:
        r"""
        Compute precision score between two token sets.

        Args:
            tokens_a_set: First set of tokens (reference)
            tokens_b_set: Second set of tokens (prediction)

        Returns:
            Precision score, or self._error_score if computation fails
        """
        try:
            score = precision(tokens_a_set, tokens_b_set)
            return self._error_score if score is None else score
        except Exception:
            return self._error_score

    def _compute_recall(self, tokens_a_set: set[str], tokens_b_set: set[str]) -> float:
        r"""
        Compute recall score between two token sets.

        Args:
            tokens_a_set: First set of tokens (reference)
            tokens_b_set: Second set of tokens (prediction)

        Returns:
            Recall score, or self._error_score if computation fails
        """
        try:
            score = recall(tokens_a_set, tokens_b_set)
            return self._error_score if score is None else score
        except Exception:
            return self._error_score

    def _compute_edit_distance(self, tokens_a: list[str], tokens_b: list[str]) -> float:
        r"""
        Compute normalized edit distance (Levenshtein distance) between two token lists.

        Args:
            tokens_a: First list of tokens
            tokens_b: Second list of tokens

        Returns:
            Normalized edit distance score (0.0 = identical, 1.0 = completely different)
        """
        try:
            if self._mode == TextMetricsMode.CPP:
                return self._text_manager.edit_distance(tokens_a, tokens_b)

            levenshtein = edit_distance(tokens_a, tokens_b)
            max_length = max(len(tokens_a), len(tokens_b))
            distance = levenshtein / max_length if max_length > 0 else 0.0
            return distance
        except Exception:
            return self._error_score

    def _compute_meteor(self, tokens_a: list[str], tokens_b: list[str]) -> float:
        r"""
        Compute METEOR score between two token lists.

        Args:
            tokens_a: First list of tokens (reference)
            tokens_b: Second list of tokens (hypothesis)

        Returns:
            METEOR score
        """
        try:
            return meteor_score.meteor_score([tokens_a], tokens_b)
        except Exception:
            return self._error_score

    def _compute_bleu(self, text_a: str, text_b: str) -> float:
        r"""
        Compute BLEU score between two texts.

        BLEU is undefined when the prediction or the reference has no tokens.
        The brevity penalty divides by the reference length and by the length
        ratio, so the underlying implementation raises ZeroDivisionError. That
        case is detected up front and reported as self._error_score with a
        warning, so that an undefined score is never mistaken for a computed one.

        Args:
            text_a: First text (prediction)
            text_b: Second text (reference)

        Returns:
            BLEU score, or self._error_score if the score is undefined or the
            computation fails
        """
        # The BLEU tokenizer (mteval-v13a) only inserts whitespace around
        # punctuation, so a text without whitespace-delimited tokens has no BLEU
        # tokens either. Check both sides before calling into `evaluate`.
        n_tokens_a = len(text_a.split())
        n_tokens_b = len(text_b.split())
        if n_tokens_a == 0 or n_tokens_b == 0:
            _log.warning(
                "BLEU is undefined for this sample (prediction has %d tokens, "
                "reference has %d tokens), returning error_score=%s",
                n_tokens_a,
                n_tokens_b,
                self._error_score,
            )
            return self._error_score

        try:
            result = self._bleu_eval.compute(
                predictions=[text_a], references=[[text_b]]
            )
        except Exception:
            # Last resort: never hide the failure, but keep the sample scored.
            _log.warning(
                "BLEU computation failed, returning error_score=%s",
                self._error_score,
                exc_info=True,
            )
            return self._error_score
        return self._error_score if result is None else result["bleu"]

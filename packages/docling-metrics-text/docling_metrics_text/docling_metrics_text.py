from docling_metrics_core.base_types import (
    BaseInputSample,
    BaseSampleResult,
)

from . import docling_metrics_text_cpp  # type: ignore


class EditDistanceSampleEvaluation(BaseSampleResult):
    edit_distance: float


# TODO: Change the signature of the base class
# class EditDistanceMetric(BaseMetric):
class EditDistanceMetric:
    r"""
    Expose the C++ edit distance metric as a Python module.
    """

    def __init__(self) -> None:
        r""" """
        self._manager = docling_metrics_text_cpp.TextManager()

    def evaluate_sample(
        self,
        sample: BaseInputSample,
    ) -> EditDistanceSampleEvaluation:
        # TODO: Add the implementation
        id = sample.id
        edit_distance = -1
        result = EditDistanceSampleEvaluation(id=id, edit_distance=edit_distance)
        return result

    def _tokenize(self, text: str, convert_parentheses: bool = False) -> list[str]:
        r"""
        Tokenize the given string
        """
        return self._manager.tokenize(text, convert_parentheses)

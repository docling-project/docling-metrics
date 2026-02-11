from docling_metrics_core.base_types import (
    BaseMetric,
)

from . import docling_metrics_text_cpp


class TextMetric(BaseMetric):
    r"""
    Expose the C++ text metrics as a Python module.
    """

    def __init__(self) -> None:
        r""" """
        self._manager = docling_metrics_text_cpp.TextManager()

    def _tokenize(self, text: str) -> list[str]:
        r"""
        Tokenize the given string
        """
        return self._manager.tokenize(text)

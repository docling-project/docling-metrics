from docling_metrics_text.docling_metrics_text import (
    EditDistanceMetric,
)

TEXT = "Good muffins cost $3.88 (roughly 3,36 euros)\nin New York.  Please buy me\ntwo of them.\nThanks."
TOKENS = [
    "Good",
    "muffins",
    "cost",
    "$",
    "3.88",
    "(",
    "roughly",
    "3,36",
    "euros",
    ")",
    "in",
    "New",
    "York.",
    "Please",
    "buy",
    "me",
    "two",
    "of",
    "them.",
    "Thanks",
    ".",
]
TOKENS_WITHOUT_PARENTHESES = [
    "Good",
    "muffins",
    "cost",
    "$",
    "3.88",
    "-LRB-",
    "roughly",
    "3,36",
    "euros",
    "-RRB-",
    "in",
    "New",
    "York.",
    "Please",
    "buy",
    "me",
    "two",
    "of",
    "them.",
    "Thanks",
    ".",
]


def test_tokenizer():
    r""" """
    ed_metric = EditDistanceMetric()

    tokens = ed_metric._tokenize(TEXT)
    assert tokens == TOKENS

    tokens_without_parentheses = ed_metric._tokenize(TEXT, convert_parentheses=True)
    assert tokens_without_parentheses == TOKENS_WITHOUT_PARENTHESES

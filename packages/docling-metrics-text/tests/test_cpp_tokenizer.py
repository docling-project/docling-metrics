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

MD_FILE_DIR = "data/md"
TOKENS_DATA = "data/nltk_tokens.json"


def test_tokenizer():
    r""" """
    ed_metric = EditDistanceMetric()

    tokens = ed_metric._tokenize(TEXT)
    assert tokens == TOKENS

    tokens_without_parentheses = ed_metric._tokenize(TEXT, convert_parentheses=True)
    assert tokens_without_parentheses == TOKENS_WITHOUT_PARENTHESES

    # Load expected tokens from JSON
    import json
    from pathlib import Path

    test_dir = Path(__file__).parent
    tokens_file = test_dir / TOKENS_DATA
    md_dir = test_dir / MD_FILE_DIR

    with open(tokens_file, "r", encoding="utf-8") as f:
        expected_tokens_data = json.load(f)

    # Test each MD file
    for md_file in md_dir.glob("*.md"):
        md_filename = md_file.name

        # Read MD file content
        with open(md_file, "r", encoding="utf-8") as f:
            md_content = f.read()

        # Get expected NLTK tokens from JSON
        assert md_filename in expected_tokens_data, f"Missing tokens for {md_filename}"
        expected_tokens = expected_tokens_data[md_filename]["nltk_tokens"]

        # Tokenize using C++ implementation
        actual_tokens = ed_metric._tokenize(md_content)

        # Compare tokens
        assert actual_tokens == expected_tokens, (
            f"Token mismatch for {md_filename}:\n"
            f"Expected {len(expected_tokens)} tokens, got {len(actual_tokens)}\n"
            f"First difference at index {next((i for i, (e, a) in enumerate(zip(expected_tokens, actual_tokens)) if e != a), min(len(expected_tokens), len(actual_tokens)))}"
        )

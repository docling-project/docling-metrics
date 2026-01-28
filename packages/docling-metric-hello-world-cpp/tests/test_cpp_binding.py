#
# Copyright IBM Inc. All rights reserved.
#
# SPDX-License-Identifier: MIT
#

"""Tests for the C++ bindings."""

from docling_metric_hello_world_cpp._hello_world_cpp import evaluate_sample


def test_cpp_evaluate_sample_returns_one() -> None:
    assert evaluate_sample("s1", "foo", "bar") == 1.0

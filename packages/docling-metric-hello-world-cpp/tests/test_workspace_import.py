#
# Copyright IBM Inc. All rights reserved.
#
# SPDX-License-Identifier: MIT
#

"""Workspace import test for the C++ hello world package."""

from docling_metric_hello_world_cpp import HelloWorldMetric


def test_importable() -> None:
    assert HelloWorldMetric is not None

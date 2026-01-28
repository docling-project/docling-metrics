#
# Copyright IBM Inc. All rights reserved.
#
# SPDX-License-Identifier: MIT
#

"""Tests for CI configuration."""

from pathlib import Path


def test_ci_references_wheels_workflow() -> None:
    ci = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "wheels.yml" in ci

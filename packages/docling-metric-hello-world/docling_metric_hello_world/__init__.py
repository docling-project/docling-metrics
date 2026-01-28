#
# Copyright IBM Inc. All rights reserved.
#
# SPDX-License-Identifier: MIT
#

"""A hello-world example metric implementation for Docling metrics."""

from docling_metric_hello_world.hello_world_metric import (
    HelloWorldAggregateResult,
    HelloWorldMetric,
    HelloWorldSampleResult,
    StringInputSample,
)

__all__ = [
    "HelloWorldAggregateResult",
    "HelloWorldMetric",
    "HelloWorldSampleResult",
    "StringInputSample",
]

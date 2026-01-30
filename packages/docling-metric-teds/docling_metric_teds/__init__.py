"""Expose the C++ package"""

import docling_metric_teds_cpp

TEDSampleEvaluation = docling_metric_teds_cpp.TEDSampleEvaluation
TEDSDatasetEvaluation = docling_metric_teds_cpp.TEDSDatasetEvaluation
TEDSManager = docling_metric_teds_cpp.TEDSManager

__all__ = [
    "TEDSampleEvaluation",
    "TEDSDatasetEvaluation",
    "TEDSManager",
]

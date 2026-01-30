"""C++ package."""

import docling_metric_teds_cpp  # type: ignore[import-not-found]

TEDSSampleEvaluation = docling_metric_teds_cpp.TEDSSampleEvaluation
TEDSDatasetEvaluation = docling_metric_teds_cpp.TEDSDatasetEvaluation
TEDSManager = docling_metric_teds_cpp.TEDSManager

__all__ = [
    "TEDSDatasetEvaluation",
    "TEDSManager",
    "TEDSSampleEvaluation",
]

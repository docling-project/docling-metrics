from pydantic import BaseModel


class BenchmarkStats(BaseModel):
    mean: float
    median: float
    std: float
    max: float
    min: float


class BenchmarkSample(BaseModel):
    id: str
    sample_len: int
    python_teds: float | None = None
    python_teds_ms: float | None = None
    python_grits_topology: float | None = None
    python_grits_topology_ms: float | None = None
    python_grits_content: float | None = None
    python_grits_content_ms: float | None = None
    python_grits_location: float | None = None
    python_grits_location_ms: float | None = None
    python_grits_ms: float | None = None

    cpp_teds: float | None = None
    cpp_teds_ms: float | None = None
    html_to_bracket_ms: float | None = None
    match: bool | None = None


class BenchmarkReport(BaseModel):
    samples: dict[str, BenchmarkSample]  # id -> BenchmarkSample
    python_teds_ms_stats: BenchmarkStats
    python_grits_ms_stats: BenchmarkStats
    cpp_ms_stats: BenchmarkStats | None = None
    html_to_bracket_ms_stats: BenchmarkStats | None = None

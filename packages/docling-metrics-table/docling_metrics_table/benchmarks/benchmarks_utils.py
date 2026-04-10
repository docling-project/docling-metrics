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
    python_teds: float
    python_teds_ms: float
    python_grits: float
    python_grits_ms: float
    cpp_teds: float
    cpp_teds_ms: float
    html_to_bracket_ms: (
        float  # This includes converting both inputs from HTML to bracket
    )
    match: bool


class BenchmarkReport(BaseModel):
    samples: dict[str, BenchmarkSample]  # id -> BenchmarkSample
    python_ms_stats: BenchmarkStats
    cpp_ms_stats: BenchmarkStats
    html_to_bracket_ms_stats: BenchmarkStats

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class ServiceEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service_name: str
    inactive_exit_timestamp: int
    execstart_timestamp: int
    activation_latency_seconds: float
    activation_phase: str


class SummaryStatistics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_services: int
    average_latency_seconds: Optional[float]
    max_latency_seconds: Optional[float]
    min_latency_seconds: Optional[float]


class Summary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_services: int
    number_of_boot_phase_only_services: int
    number_of_post_boot_services: int
    overall_statistics: SummaryStatistics


class AnalysisResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hostname: str
    username: str
    analyzed_at: datetime
    boot_completion_boundary_timestamp: int
    services: List[ServiceEntry]
    summary: Summary
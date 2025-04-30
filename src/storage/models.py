# Data models
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field

class RegionInfo(BaseModel):
    """Region information model."""
    source: str = Field(default="unknown", description="Source region of the client")
    target: str = Field(default="unknown", description="Target region of the service")

class RawMessage(BaseModel):
    """Raw message model."""
    raw_message: str = Field(..., description="Raw message string")
    parsed_message: Dict[str, Any] = Field(default_factory=dict, description="Parsed message object")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Message metadata")

class NormalizedJob(BaseModel):
    """Normalized job model."""
    source: str = Field(..., description="Source service name")
    timestamp: str = Field(..., description="ISO-8601 timestamp when received")
    job_id: str = Field(..., description="Job identifier")
    mining_pool: str = Field(default="unknown", description="Name of the mining pool")
    difficulty: float = Field(default=0.0, description="Mining difficulty")
    prev_block_hash: str = Field(default="", description="Previous block hash")
    coinbase_tx: str = Field(default="", description="Coinbase transaction")
    merkle_branches: List[str] = Field(default_factory=list, description="Merkle branches array")
    version: str = Field(default="", description="Block version")
    bits: str = Field(default="", description="Difficulty bits")
    time: int = Field(default=0, description="Block time")
    height: Optional[int] = Field(default=None, description="Block height")
    clean_jobs: bool = Field(default=False, description="Clean jobs flag")
    region: RegionInfo = Field(default_factory=RegionInfo, description="Region information")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Source-specific fields")
    stored_at: Optional[str] = Field(default=None, description="ISO-8601 timestamp when stored in database")

class JobMatch(BaseModel):
    """Job match model."""
    timestamp: str = Field(..., description="ISO-8601 timestamp when match was detected")
    primary_job: NormalizedJob = Field(..., description="Primary job that was matched")
    matches: List[NormalizedJob] = Field(..., description="Matching jobs from other services")
    propagation_times: Dict[str, Optional[float]] = Field(default_factory=dict, description="Propagation times between services in seconds")
    stored_at: Optional[str] = Field(default=None, description="ISO-8601 timestamp when stored in database")

class ServiceStats(BaseModel):
    """Service statistics model."""
    job_count: int = Field(default=0, description="Number of jobs from this service")
    pools_count: int = Field(default=0, description="Number of unique pools observed")
    heights_count: int = Field(default=0, description="Number of unique heights observed")
    job_rate_per_minute: float = Field(default=0.0, description="Jobs per minute")
    latest_job: Optional[Dict[str, Any]] = Field(default=None, description="Latest job from this service")

class PoolStats(BaseModel):
    """Pool statistics model."""
    job_count: int = Field(default=0, description="Number of jobs from this pool")
    services_count: int = Field(default=0, description="Number of services that observed this pool")
    heights_count: int = Field(default=0, description="Number of unique heights from this pool")
    avg_jobs_per_height: float = Field(default=0.0, description="Average jobs per height")
    latest_job: Optional[Dict[str, Any]] = Field(default=None, description="Latest job from this pool")

class HeightStats(BaseModel):
    """Height statistics model."""
    job_count: int = Field(default=0, description="Number of jobs for this height")
    services_count: int = Field(default=0, description="Number of services that observed this height")
    pools_count: int = Field(default=0, description="Number of pools that produced jobs for this height")
    services: List[str] = Field(default_factory=list, description="Services that observed this height")
    pools: List[str] = Field(default_factory=list, description="Pools that produced jobs for this height")
    first_seen: str = Field(..., description="ISO-8601 timestamp when first seen")
    last_seen: str = Field(..., description="ISO-8601 timestamp when last seen")
    time_range_seconds: float = Field(default=0.0, description="Time range between first and last observation in seconds")

class PropagationStats(BaseModel):
    """Propagation statistics model."""
    mean: float = Field(..., description="Mean propagation time in seconds")
    median: float = Field(..., description="Median propagation time in seconds")
    min: float = Field(..., description="Minimum propagation time in seconds")
    max: float = Field(..., description="Maximum propagation time in seconds")
    stddev: float = Field(..., description="Standard deviation of propagation times in seconds")
    sample_count: int = Field(..., description="Number of samples used for statistics")

class AgreementStats(BaseModel):
    """Agreement statistics model."""
    agreement_counts: Dict[str, int] = Field(default_factory=dict, description="Counts of agreements between services")
    agreement_rates: Dict[str, float] = Field(default_factory=dict, description="Rates of agreement between services")
    total_agreements: int = Field(default=0, description="Total number of agreements detected")
    recent_agreements: List[Dict[str, Any]] = Field(default_factory=list, description="Recent agreement events")

class ProcessingStats(BaseModel):
    """Processing statistics model."""
    count: int = Field(default=0, description="Number of jobs processed")
    mean: Optional[float] = Field(default=None, description="Mean processing time in seconds")
    median: Optional[float] = Field(default=None, description="Median processing time in seconds")
    min: Optional[float] = Field(default=None, description="Minimum processing time in seconds")
    max: Optional[float] = Field(default=None, description="Maximum processing time in seconds")
    stddev: Optional[float] = Field(default=None, description="Standard deviation of processing times in seconds")

class ComprehensiveStats(BaseModel):
    """Comprehensive statistics model."""
    service_stats: Dict[str, ServiceStats] = Field(default_factory=dict, description="Statistics by service")
    pool_stats: Dict[str, PoolStats] = Field(default_factory=dict, description="Statistics by pool")
    height_stats: List[Dict[str, Any]] = Field(default_factory=list, description="Statistics by height")
    agreement_stats: AgreementStats = Field(default_factory=AgreementStats, description="Agreement statistics")
    processing_stats: ProcessingStats = Field(default_factory=ProcessingStats, description="Processing statistics")
    job_frequency_by_pool: Dict[str, float] = Field(default_factory=dict, description="Job frequency by pool")
    version_distribution: Dict[str, Dict[str, int]] = Field(default_factory=dict, description="Block version distribution by service")
    top_pools: List[Dict[str, Any]] = Field(default_factory=list, description="Top pools by job count")
    total_jobs: int = Field(default=0, description="Total number of jobs processed")
    time_window_seconds: float = Field(..., description="Time window in seconds")
    timestamp: str = Field(..., description="ISO-8601 timestamp of the statistics snapshot")
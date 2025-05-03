# For dashboard display
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)

# Response Models

class RegionInfo(BaseModel):
    """Region information response model."""
    source: str = Field(default="unknown", description="Source region of the client")
    target: str = Field(default="unknown", description="Target region of the service")

class JobResponse(BaseModel):
    """Normalized job response model."""
    id: Optional[str] = Field(default=None, description="Database ID of the job")
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
    
    @validator("id", pre=True)
    def convert_id(cls, v):
        """Convert MongoDB ObjectID to string."""
        if hasattr(v, "__str__"):
            return str(v)
        return v

class JobListResponse(BaseModel):
    """List of jobs response model."""
    jobs: List[JobResponse] = Field(default_factory=list, description="List of jobs")
    count: int = Field(..., description="Total count of jobs")
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=50, description="Number of items per page")
    total_pages: int = Field(default=1, description="Total number of pages")

class MatchedJobResponse(BaseModel):
    """Matched job response model."""
    job: JobResponse = Field(..., description="Job information")
    propagation_time: Optional[float] = Field(default=None, description="Propagation time in seconds")

class JobMatchResponse(BaseModel):
    """Job match response model."""
    id: Optional[str] = Field(default=None, description="Database ID of the match")
    timestamp: str = Field(..., description="ISO-8601 timestamp when match was detected")
    primary_job: JobResponse = Field(..., description="Primary job that was matched")
    matched_jobs: List[MatchedJobResponse] = Field(default_factory=list, description="Matching jobs from other services")
    propagation_stats: Dict[str, float] = Field(default_factory=dict, description="Propagation time statistics")

class JobMatchListResponse(BaseModel):
    """List of job matches response model."""
    matches: List[JobMatchResponse] = Field(default_factory=list, description="List of job matches")
    count: int = Field(..., description="Total count of matches")
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=50, description="Number of items per page")
    total_pages: int = Field(default=1, description="Total number of pages")

class ServiceStatsResponse(BaseModel):
    """Service statistics response model."""
    job_count: int = Field(default=0, description="Number of jobs from this service")
    pools_count: int = Field(default=0, description="Number of unique pools observed")
    heights_count: int = Field(default=0, description="Number of unique heights observed")
    job_rate_per_minute: float = Field(default=0.0, description="Jobs per minute")
    latest_job: Optional[Dict[str, Any]] = Field(default=None, description="Latest job from this service")

class PoolStatsResponse(BaseModel):
    """Pool statistics response model."""
    name: str = Field(..., description="Mining pool name")
    job_count: int = Field(default=0, description="Number of jobs from this pool")
    services_count: int = Field(default=0, description="Number of services that observed this pool")
    heights_count: int = Field(default=0, description="Number of unique heights from this pool")
    avg_jobs_per_height: float = Field(default=0.0, description="Average jobs per height")

class HeightStatsResponse(BaseModel):
    """Height statistics response model."""
    height: int = Field(..., description="Block height")
    job_count: int = Field(default=0, description="Number of jobs for this height")
    services_count: int = Field(default=0, description="Number of services that observed this height")
    pools_count: int = Field(default=0, description="Number of pools that produced jobs for this height")
    services: List[str] = Field(default_factory=list, description="Services that observed this height")
    pools: List[str] = Field(default_factory=list, description="Pools that produced jobs for this height")
    first_seen: str = Field(..., description="ISO-8601 timestamp when first seen")
    last_seen: str = Field(..., description="ISO-8601 timestamp when last seen")
    time_range_seconds: float = Field(default=0.0, description="Time range between first and last observation in seconds")

class PropagationStatsResponse(BaseModel):
    """Propagation statistics response model."""
    service_pair: str = Field(..., description="Service pair (e.g., 'service1-service2')")
    mean: float = Field(..., description="Mean propagation time in seconds")
    median: float = Field(..., description="Median propagation time in seconds")
    min: float = Field(..., description="Minimum propagation time in seconds")
    max: float = Field(..., description="Maximum propagation time in seconds")
    stddev: float = Field(..., description="Standard deviation of propagation times in seconds")
    sample_count: int = Field(..., description="Number of samples used for statistics")

class PropagationHistoryPoint(BaseModel):
    """Propagation time history data point."""
    timestamp: str = Field(..., description="ISO-8601 timestamp")
    value: float = Field(..., description="Propagation time in seconds")

class PropagationHistoryResponse(BaseModel):
    """Propagation time history response model."""
    service_pair: str = Field(..., description="Service pair (e.g., 'service1-service2')")
    data: List[PropagationHistoryPoint] = Field(default_factory=list, description="Propagation time history data")
    stats: Optional[PropagationStatsResponse] = Field(default=None, description="Current propagation statistics")

class ClientStatusResponse(BaseModel):
    """Client status response model."""
    service: str = Field(..., description="Service name")
    status: str = Field(..., description="Connection status (active/inactive)")
    jobs_received: int = Field(default=0, description="Number of jobs received")
    pools_observed: int = Field(default=0, description="Number of pools observed")
    last_activity: Optional[float] = Field(default=None, description="Timestamp of last activity")

class ClientStatusListResponse(BaseModel):
    """List of client statuses response model."""
    clients: List[ClientStatusResponse] = Field(default_factory=list, description="List of client statuses")
    timestamp: str = Field(..., description="ISO-8601 timestamp of the status snapshot")

class ComprehensiveStatsResponse(BaseModel):
    """Comprehensive statistics response model."""
    service_stats: Dict[str, ServiceStatsResponse] = Field(default_factory=dict, description="Statistics by service")
    top_pools: List[PoolStatsResponse] = Field(default_factory=list, description="Top pools by job count")
    latest_heights: List[HeightStatsResponse] = Field(default_factory=list, description="Statistics for latest heights")
    propagation_stats: Dict[str, PropagationStatsResponse] = Field(default_factory=dict, description="Propagation statistics")
    job_counts: Dict[str, int] = Field(default_factory=dict, description="Job counts by various dimensions")
    timestamp: str = Field(..., description="ISO-8601 timestamp of the statistics snapshot")

class ErrorResponse(BaseModel):
    """API error response model."""
    detail: str = Field(..., description="Error detail message")
    status_code: int = Field(..., description="HTTP status code")
    timestamp: str = Field(..., description="ISO-8601 timestamp of the error")

# Serializer Functions

def serialize_job(job: Dict[str, Any]) -> JobResponse:
    """
    Serialize a job from the database to the API response format.
    
    Args:
        job: Job document from the database
        
    Returns:
        Serialized job response
    """
    # Extract region info
    region_info = RegionInfo(
        source=job.get("region", {}).get("source", "unknown"),
        target=job.get("region", {}).get("target", "unknown")
    )
    
    # Create response
    return JobResponse(
        id=job.get("_id"),
        source=job.get("source", ""),
        timestamp=job.get("timestamp", ""),
        job_id=job.get("job_id", ""),
        mining_pool=job.get("mining_pool", "unknown"),
        difficulty=job.get("difficulty", 0.0),
        prev_block_hash=job.get("prev_block_hash", ""),
        coinbase_tx=job.get("coinbase_tx", ""),
        merkle_branches=job.get("merkle_branches", []),
        version=job.get("version", ""),
        bits=job.get("bits", ""),
        time=job.get("time", 0),
        height=job.get("height"),
        clean_jobs=job.get("clean_jobs", False),
        region=region_info
    )

def serialize_jobs(
    jobs: List[Dict[str, Any]], 
    count: int, 
    page: int = 1, 
    page_size: int = 50
) -> JobListResponse:
    """
    Serialize a list of jobs from the database to the API response format.
    
    Args:
        jobs: List of job documents from the database
        count: Total count of jobs
        page: Current page number
        page_size: Number of items per page
        
    Returns:
        Serialized job list response
    """
    serialized_jobs = [serialize_job(job) for job in jobs]
    total_pages = (count + page_size - 1) // page_size if count > 0 else 1
    
    return JobListResponse(
        jobs=serialized_jobs,
        count=count,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

def serialize_job_match(match: Dict[str, Any]) -> JobMatchResponse:
    """
    Serialize a job match from the database to the API response format.
    
    Args:
        match: Job match document from the database
        
    Returns:
        Serialized job match response
    """
    # Serialize primary job
    primary_job = serialize_job(match.get("primary_job", {}))
    
    # Serialize matched jobs
    matched_jobs = []
    for job in match.get("matches", []):
        serialized_job = serialize_job(job)
        
        # Get propagation time if available
        propagation_time = None
        if "propagation_times" in match and job.get("source") in match["propagation_times"]:
            propagation_time = match["propagation_times"][job.get("source")]
        
        matched_jobs.append(MatchedJobResponse(
            job=serialized_job,
            propagation_time=propagation_time
        ))
    
    # Create response
    return JobMatchResponse(
        id=match.get("_id"),
        timestamp=match.get("timestamp", ""),
        primary_job=primary_job,
        matched_jobs=matched_jobs,
        propagation_stats={} # Can be populated later if needed
    )

def serialize_job_matches(
    matches: List[Dict[str, Any]], 
    count: int, 
    page: int = 1, 
    page_size: int = 50
) -> JobMatchListResponse:
    """
    Serialize a list of job matches from the database to the API response format.
    
    Args:
        matches: List of job match documents from the database
        count: Total count of matches
        page: Current page number
        page_size: Number of items per page
        
    Returns:
        Serialized job match list response
    """
    serialized_matches = [serialize_job_match(match) for match in matches]
    total_pages = (count + page_size - 1) // page_size if count > 0 else 1
    
    return JobMatchListResponse(
        matches=serialized_matches,
        count=count,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

def serialize_service_stats(service: str, stats: Dict[str, Any]) -> ServiceStatsResponse:
    """
    Serialize service statistics to the API response format.
    
    Args:
        service: Service name
        stats: Service statistics from the analyzer
        
    Returns:
        Serialized service statistics response
    """
    return ServiceStatsResponse(
        job_count=stats.get("job_count", 0),
        pools_count=stats.get("pools_count", 0),
        heights_count=stats.get("heights_count", 0),
        job_rate_per_minute=stats.get("job_rate_per_minute", 0.0),
        latest_job=stats.get("latest_job")
    )

def serialize_pool_stats(pool: str, stats: Dict[str, Any]) -> PoolStatsResponse:
    """
    Serialize pool statistics to the API response format.
    
    Args:
        pool: Pool name
        stats: Pool statistics from the analyzer
        
    Returns:
        Serialized pool statistics response
    """
    return PoolStatsResponse(
        name=pool,
        job_count=stats.get("job_count", 0),
        services_count=stats.get("services_count", 0),
        heights_count=stats.get("heights_count", 0),
        avg_jobs_per_height=stats.get("avg_jobs_per_height", 0.0)
    )

def serialize_height_stats(height: int, stats: Dict[str, Any]) -> HeightStatsResponse:
    """
    Serialize height statistics to the API response format.
    
    Args:
        height: Block height
        stats: Height statistics from the analyzer
        
    Returns:
        Serialized height statistics response
    """
    return HeightStatsResponse(
        height=height,
        job_count=stats.get("job_count", 0),
        services_count=stats.get("services_count", 0),
        pools_count=stats.get("pools_count", 0),
        services=stats.get("services", []),
        pools=stats.get("pools", []),
        first_seen=stats.get("first_seen", ""),
        last_seen=stats.get("last_seen", ""),
        time_range_seconds=stats.get("time_range_seconds", 0.0)
    )

def serialize_propagation_stats(service_pair: str, stats: Dict[str, Any]) -> PropagationStatsResponse:
    """
    Serialize propagation statistics to the API response format.
    
    Args:
        service_pair: Service pair (e.g., 'service1-service2')
        stats: Propagation statistics from the analyzer
        
    Returns:
        Serialized propagation statistics response
    """
    return PropagationStatsResponse(
        service_pair=service_pair,
        mean=stats.get("mean", 0.0),
        median=stats.get("median", 0.0),
        min=stats.get("min", 0.0),
        max=stats.get("max", 0.0),
        stddev=stats.get("stddev", 0.0),
        sample_count=stats.get("sample_count", 0)
    )

def serialize_propagation_history(
    service_pair: str,
    history_data: List[Dict[str, Any]],
    stats: Optional[Dict[str, Any]] = None
) -> PropagationHistoryResponse:
    """
    Serialize propagation history data to the API response format.
    
    Args:
        service_pair: Service pair (e.g., 'service1-service2')
        history_data: Propagation history data from the analyzer
        stats: Current propagation statistics
        
    Returns:
        Serialized propagation history response
    """
    # Convert history data to response format
    data_points = [
        PropagationHistoryPoint(
            timestamp=point.get("timestamp", ""),
            value=point.get("value", 0.0)
        )
        for point in history_data
    ]
    
    # Serialize propagation stats if provided
    stats_response = None
    if stats:
        stats_response = serialize_propagation_stats(service_pair, stats)
    
    return PropagationHistoryResponse(
        service_pair=service_pair,
        data=data_points,
        stats=stats_response
    )

def serialize_client_status(service: str, status: Dict[str, Any]) -> ClientStatusResponse:
    """
    Serialize client status to the API response format.
    
    Args:
        service: Service name
        status: Client status information
        
    Returns:
        Serialized client status response
    """
    return ClientStatusResponse(
        service=service,
        status="active" if status.get("latest_job_time") else "inactive",
        jobs_received=status.get("recent_job_count", 0),
        pools_observed=status.get("pools_observed", 0),
        last_activity=status.get("latest_job_time")
    )

def serialize_client_statuses(statuses: Dict[str, Dict[str, Any]]) -> ClientStatusListResponse:
    """
    Serialize a list of client statuses to the API response format.
    
    Args:
        statuses: Dictionary mapping services to their status information
        
    Returns:
        Serialized client status list response
    """
    client_statuses = [
        serialize_client_status(service, status)
        for service, status in statuses.items()
    ]
    
    return ClientStatusListResponse(
        clients=client_statuses,
        timestamp=datetime.utcnow().isoformat()
    )

def serialize_comprehensive_stats(stats: Dict[str, Any]) -> ComprehensiveStatsResponse:
    """
    Serialize comprehensive statistics to the API response format.
    
    Args:
        stats: Comprehensive statistics from the analyzer
        
    Returns:
        Serialized comprehensive statistics response
    """
    # Serialize service stats
    service_stats = {}
    for service, service_data in stats.get("service_stats", {}).items():
        service_stats[service] = serialize_service_stats(service, service_data)
    
    # Serialize top pools
    top_pools = []
    for pool_data in stats.get("top_pools", []):
        pool_name = pool_data.pop("pool", "unknown")
        top_pools.append(serialize_pool_stats(pool_name, pool_data))
    
    # Serialize height stats
    latest_heights = []
    for height_data in stats.get("height_stats", []):
        height = height_data.pop("height", 0)
        latest_heights.append(serialize_height_stats(height, height_data))
    
    # Serialize propagation stats
    propagation_stats = {}
    for pair, prop_data in stats.get("propagation", {}).get("average", {}).items():
        pair_stats = {
            "mean": stats.get("propagation", {}).get("average", {}).get(pair, 0.0),
            "median": stats.get("propagation", {}).get("median", {}).get(pair, 0.0),
            "min": stats.get("propagation", {}).get("min", {}).get(pair, 0.0),
            "max": stats.get("propagation", {}).get("max", {}).get(pair, 0.0),
            "sample_count": 0  # This might need to be populated from elsewhere
        }
        propagation_stats[pair] = serialize_propagation_stats(pair, pair_stats)
    
    # Compile job counts
    job_counts = {
        "total": stats.get("total_jobs", 0)
    }
    
    return ComprehensiveStatsResponse(
        service_stats=service_stats,
        top_pools=top_pools,
        latest_heights=latest_heights,
        propagation_stats=propagation_stats,
        job_counts=job_counts,
        timestamp=stats.get("timestamp", datetime.utcnow().isoformat())
    )

def create_error_response(detail: str, status_code: int) -> ErrorResponse:
    """
    Create an error response.
    
    Args:
        detail: Error detail message
        status_code: HTTP status code
        
    Returns:
        Error response
    """
    return ErrorResponse(
        detail=detail,
        status_code=status_code,
        timestamp=datetime.utcnow().isoformat()
    )
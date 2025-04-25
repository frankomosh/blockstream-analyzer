# For dashboard display
import logging
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

logger = logging.getLogger(__name__)

app = FastAPI(title="Stratum Monitor API")

# Global references to components (set during start_api_server)
comparator = None
db = None

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

@app.get("/api/stats")
async def get_stats():
    """Get current statistics."""
    if not comparator:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return comparator.get_statistics()

@app.get("/api/jobs")
async def get_jobs(
    source: Optional[str] = Query(None, description="Filter by source service"),
    pool: Optional[str] = Query(None, description="Filter by mining pool"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of jobs")
):
    """Get recent jobs."""
    if not db:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    jobs = await db.get_recent_jobs(source=source, pool=pool, limit=limit)
    return {"jobs": jobs, "count": len(jobs)}

@app.get("/api/pools")
async def get_pools(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of pools")
):
    """Get top mining pools by job count."""
    if not db:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    pools = await db.get_pools_by_job_count(limit=limit)
    return {"pools": pools}

@app.get("/api/propagation/{source_pair}")
async def get_propagation(
    source_pair: str,
    hours: int = Query(24, ge=1, le=168, description="Hours of history")
):
    """Get propagation time history for a source pair."""
    if not db:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    history = await db.get_propagation_history(source_pair=source_pair, hours=hours)
    
    # Format for chart display
    chart_data = [
        {"timestamp": ts.isoformat(), "propagation_time": prop_time}
        for ts, prop_time in history
    ]
    
    return {"source_pair": source_pair, "data": chart_data}

@app.get("/api/clients")
async def get_client_status():
    """Get current status of WebSocket clients."""
    global comparator
    if not comparator:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    stats = comparator.get_statistics()
    sources = stats.get("sources", {})
    
    return {
        "clients": [
            {
                "service": service,
                "status": "active" if source_data.get("latest_job_time") else "inactive",
                "jobs_received": source_data.get("recent_job_count", 0),
                "pools_observed": source_data.get("pools_observed", 0),
                "last_activity": source_data.get("latest_job_time")
            }
            for service, source_data in sources.items()
        ]
    }

async def start_api_server(
    host: str = "0.0.0.0",
    port: int = 8080,
    comparator_instance: Any = None,
    db_instance: Any = None,
    origins: List[str] = None
):
    """
    Start the API server.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        comparator_instance: JobComparator instance
        db_instance: DatabaseManager instance
        origins: CORS origins to allow
    """
    global comparator, db
    comparator = comparator_instance
    db = db_instance
    
    # Configure CORS
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()
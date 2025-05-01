# Database maintainance tasks
"""
Database maintenance script for the stratum monitor.

This script performs maintenance operations on the database:
- Removes old data to prevent database bloat
- Optimizes indexes
- Aggregates historical data for long-term storage
"""

import asyncio
import argparse
import logging
import sys
import os
import yaml
from datetime import datetime, timedelta
from typing import Dict, Any

# Add parent directory to path to import project modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.storage.db import DatabaseManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("db_maintenance.log")
    ]
)
logger = logging.getLogger(__name__)

async def cleanup_old_data(db: DatabaseManager, days_to_keep: int):
    """
    Clean up old data.
    
    Args:
        db: Database manager
        days_to_keep: Number of days of data to keep
    """
    logger.info(f"Cleaning up data older than {days_to_keep} days")
    await db.cleanup_old_data(days_to_keep=days_to_keep)

async def aggregate_historical_data(db: DatabaseManager, days_to_aggregate: int):
    """
    Aggregate historical data for long-term storage.
    
    Args:
        db: Database manager
        days_to_aggregate: Number of days of data to aggregate
    """
    logger.info(f"Aggregating data from the last {days_to_aggregate} days")
    
    # Calculate cutoff timestamp
    cutoff = datetime.utcnow() - timedelta(days=days_to_aggregate)
    cutoff_str = cutoff.isoformat()
    
    try:
        # Aggregate job counts by day and service
        job_counts_by_service = await aggregate_job_counts_by_service(db, cutoff_str)
        logger.info(f"Aggregated job counts by service: {len(job_counts_by_service)} entries")
        
        # Aggregate job counts by day and pool
        job_counts_by_pool = await aggregate_job_counts_by_pool(db, cutoff_str)
        logger.info(f"Aggregated job counts by pool: {len(job_counts_by_pool)} entries")
        
        # Aggregate match counts by day and service pair
        match_counts_by_pair = await aggregate_match_counts_by_pair(db, cutoff_str)
        logger.info(f"Aggregated match counts by service pair: {len(match_counts_by_pair)} entries")
        
        # Store aggregated data
        await store_aggregated_data(db, {
            "timestamp": datetime.utcnow().isoformat(),
            "period_start": cutoff_str,
            "period_end": datetime.utcnow().isoformat(),
            "job_counts_by_service": job_counts_by_service,
            "job_counts_by_pool": job_counts_by_pool,
            "match_counts_by_pair": match_counts_by_pair
        })
        
        logger.info("Aggregated data stored successfully")
        
    except Exception as e:
        logger.error(f"Error aggregating historical data: {e}")

async def aggregate_job_counts_by_service(db: DatabaseManager, cutoff_str: str) -> Dict[str, Dict[str, int]]:
    """
    Aggregate job counts by day and service.
    
    Args:
        db: Database manager
        cutoff_str: Cutoff timestamp as ISO string
        
    Returns:
        Dictionary mapping days to dictionaries mapping services to counts
    """
    collection = db.collections["normalized_jobs"]
    if not collection:
        return {}
    
    try:
        pipeline = [
            {"$match": {"timestamp": {"$gte": cutoff_str}}},
            {"$group": {
                "_id": {
                    "date": {"$substr": ["$timestamp", 0, 10]},
                    "service": "$source"
                },
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id.date": 1}}
        ]
        
        result = await collection.aggregate(pipeline).to_list(length=None)
        
        # Reorganize into day -> service -> count format
        aggregated = {}
        for doc in result:
            date = doc["_id"]["date"]
            service = doc["_id"]["service"]
            count = doc["count"]
            
            if date not in aggregated:
                aggregated[date] = {}
            
            aggregated[date][service] = count
        
        return aggregated
        
    except Exception as e:
        logger.error(f"Error aggregating job counts by service: {e}")
        return {}

async def aggregate_job_counts_by_pool(db: DatabaseManager, cutoff_str: str) -> Dict[str, Dict[str, int]]:
    """
    Aggregate job counts by day and pool.
    
    Args:
        db: Database manager
        cutoff_str: Cutoff timestamp as ISO string
        
    Returns:
        Dictionary mapping days to dictionaries mapping pools to counts
    """
    collection = db.collections["normalized_jobs"]
    if not collection:
        return {}
    
    try:
        pipeline = [
            {"$match": {"timestamp": {"$gte": cutoff_str}}},
            {"$group": {
                "_id": {
                    "date": {"$substr": ["$timestamp", 0, 10]},
                    "pool": "$mining_pool"
                },
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id.date": 1}}
        ]
        
        result = await collection.aggregate(pipeline).to_list(length=None)
        
        # Reorganize into day -> pool -> count format
        aggregated = {}
        for doc in result:
            date = doc["_id"]["date"]
            pool = doc["_id"]["pool"]
            count = doc["count"]
            
            if date not in aggregated:
                aggregated[date] = {}
            
            aggregated[date][pool] = count
        
        return aggregated
        
    except Exception as e:
        logger.error(f"Error aggregating job counts by pool: {e}")
        return {}

async def aggregate_match_counts_by_pair(db: DatabaseManager, cutoff_str: str) -> Dict[str, Dict[str, int]]:
    """
    Aggregate match counts by day and service pair.
    
    Args:
        db: Database manager
        cutoff_str: Cutoff timestamp as ISO string
        
    Returns:
        Dictionary mapping days to dictionaries mapping service pairs to counts
    """
    collection = db.collections["job_matches"]
    if not collection:
        return {}
    
    try:
        # First, get all matches
        pipeline = [
            {"$match": {"timestamp": {"$gte": cutoff_str}}},
            {"$project": {
                "date": {"$substr": ["$timestamp", 0, 10]},
                "primary_source": "$primary_job.source",
                "match_sources": {"$map": {
                    "input": "$matches",
                    "as": "match",
                    "in": "$$match.source"
                }}
            }}
        ]
        
        result = await collection.aggregate(pipeline).to_list(length=None)
        
        # Manually count pairs
        aggregated = {}
        for doc in result:
            date = doc["date"]
            primary_source = doc["primary_source"]
            
            if date not in aggregated:
                aggregated[date] = {}
            
            for match_source in doc["match_sources"]:
                # Create a sorted pair key
                pair = "-".join(sorted([primary_source, match_source]))
                
                # Increment count
                if pair not in aggregated[date]:
                    aggregated[date][pair] = 0
                
                aggregated[date][pair] += 1
        
        return aggregated
        
    except Exception as e:
        logger.error(f"Error aggregating match counts by pair: {e}")
        return {}

async def store_aggregated_data(db: DatabaseManager, aggregated_data: Dict[str, Any]):
    """
    Store aggregated data.
    
    Args:
        db: Database manager
        aggregated_data: Aggregated data to store
    """
    # Create aggregated_data collection if it doesn't exist
    if "aggregated_data" not in db.collections:
        db.collections["aggregated_data"] = db.db.aggregated_data
    
    try:
        await db.collections["aggregated_data"].insert_one(aggregated_data)
    except Exception as e:
        logger.error(f"Error storing aggregated data: {e}")

async def optimize_indexes(db: DatabaseManager):
    """
    Optimize database indexes.
    
    Args:
        db: Database manager
    """
    logger.info("Optimizing database indexes")
    
    try:
        # MongoDB doesn't need explicit index optimization like some databases
        # This is primarily a placeholder for future optimizations (if needed)
        pass
    except Exception as e:
        logger.error(f"Error optimizing indexes: {e}")

async def run_maintenance(config: Dict[str, Any]):
    """
    Run maintenance tasks.
    
    Args:
        config: Configuration dictionary
    """
    # Create database manager
    db = DatabaseManager(
        connection_string=config.get("database", {}).get("connection_string", "mongodb://localhost:27017"),
        database_name=config.get("database", {}).get("database_name", "stratum_monitor")
    )
    
    # Initialize database
    await db.initialize()
    
    try:
        # Clean up old data
        days_to_keep = config.get("maintenance", {}).get("days_to_keep", 30)
        await cleanup_old_data(db, days_to_keep)
        
        # Aggregate historical data
        days_to_aggregate = config.get("maintenance", {}).get("days_to_aggregate", 7)
        await aggregate_historical_data(db, days_to_aggregate)
        
        # Optimize indexes
        await optimize_indexes(db)
        
    finally:
        # Close database connection
        await db.close()

def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return {}

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Database maintenance for stratum monitor")
    parser.add_argument("--config", default="../config/settings.yml", help="Path to configuration file")
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Run maintenance
    asyncio.run(run_maintenance(config))

if __name__ == "__main__":
    main()
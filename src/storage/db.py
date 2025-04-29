# Database connection management
import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

import motor.motor_asyncio
from pymongo import ASCENDING, DESCENDING

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database operations for the stratum monitor."""
    
    def __init__(self, connection_string: str = "mongodb://localhost:27017", database_name: str = "stratum_monitor"):
        """
        Initialize the database manager.
        
        Args:
            connection_string: MongoDB connection string
            database_name: Name of the database to use
        """
        self.connection_string = connection_string
        self.database_name = database_name
        self.client = None
        self.db = None
        self.collections = {
            "raw_messages": None,
            "normalized_jobs": None,
            "job_matches": None,
            "stats": None
        }
    
    async def initialize(self):
        """Initialize database connection and collections."""
        try:
            # Connect to MongoDB
            self.client = motor.motor_asyncio.AsyncIOMotorClient(self.connection_string)
            self.db = self.client[self.database_name]
            
            # Initialize collections
            self.collections["raw_messages"] = self.db.raw_messages
            self.collections["normalized_jobs"] = self.db.normalized_jobs
            self.collections["job_matches"] = self.db.job_matches
            self.collections["stats"] = self.db.stats
            
            # Create indexes
            await self._create_indexes()
            
            logger.info(f"Database initialized: {self.database_name}")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    async def _create_indexes(self):
        """Create indexes for collections."""
        # Raw messages indexes
        await self.collections["raw_messages"].create_index([
            ("metadata.service_name", ASCENDING),
            ("metadata.received_timestamp", DESCENDING)
        ])
        
        # Normalized jobs indexes
        await self.collections["normalized_jobs"].create_index([
            ("source", ASCENDING),
            ("timestamp", DESCENDING)
        ])
        
        await self.collections["normalized_jobs"].create_index([
            ("mining_pool", ASCENDING),
            ("timestamp", DESCENDING)
        ])
        
        await self.collections["normalized_jobs"].create_index([
            ("height", DESCENDING)
        ])
        
        await self.collections["normalized_jobs"].create_index([
            ("job_id", ASCENDING),
            ("source", ASCENDING)
        ])
        
        # Job matches indexes
        await self.collections["job_matches"].create_index([
            ("timestamp", DESCENDING)
        ])
        
        await self.collections["job_matches"].create_index([
            ("primary_job.mining_pool", ASCENDING),
            ("timestamp", DESCENDING)
        ])
        
        # Stats indexes
        await self.collections["stats"].create_index([
            ("timestamp", DESCENDING)
        ])
        
        logger.info("Database indexes created")
    
    async def store_raw_message(self, message: Dict[str, Any]) -> str:
        """
        Store a raw message.
        
        Args:
            message: Raw message with metadata
            
        Returns:
            ID of the inserted document
        """
        if not self.collections["raw_messages"]:
            logger.error("Database not initialized")
            return ""
            
        try:
            # Add timestamp if not present
            if "metadata" not in message:
                message["metadata"] = {}
            if "stored_at" not in message["metadata"]:
                message["metadata"]["stored_at"] = datetime.utcnow().isoformat()
            
            # Insert message
            result = await self.collections["raw_messages"].insert_one(message)
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Error storing raw message: {e}")
            return ""
    
    async def store_normalized_job(self, job: Dict[str, Any]) -> str:
        """
        Store a normalized job.
        
        Args:
            job: Normalized job data
            
        Returns:
            ID of the inserted document
        """
        if not self.collections["normalized_jobs"]:
            logger.error("Database not initialized")
            return ""
            
        try:
            # Add storage timestamp
            job["stored_at"] = datetime.utcnow().isoformat()
            
            # Insert job
            result = await self.collections["normalized_jobs"].insert_one(job)
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Error storing normalized job: {e}")
            return ""
    
    async def store_job_match(self, match: Dict[str, Any]) -> str:
        """
        Store a job match.
        
        Args:
            match: Job match data
            
        Returns:
            ID of the inserted document
        """
        if not self.collections["job_matches"]:
            logger.error("Database not initialized")
            return ""
            
        try:
            # Add storage timestamp if not present
            if "stored_at" not in match:
                match["stored_at"] = datetime.utcnow().isoformat()
            
            # Insert match
            result = await self.collections["job_matches"].insert_one(match)
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Error storing job match: {e}")
            return ""
    
    async def store_stats(self, stats: Dict[str, Any]) -> str:
        """
        Store statistics snapshot.
        
        Args:
            stats: Statistics data
            
        Returns:
            ID of the inserted document
        """
        if not self.collections["stats"]:
            logger.error("Database not initialized")
            return ""
            
        try:
            # Add timestamp
            stats["timestamp"] = datetime.utcnow().isoformat()
            
            # Insert stats
            result = await self.collections["stats"].insert_one(stats)
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Error storing stats: {e}")
            return ""
    
    async def get_recent_jobs(
        self, 
        source: Optional[str] = None, 
        pool: Optional[str] = None,
        height: Optional[int] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get recent jobs, optionally filtered by source, pool, or height.
        
        Args:
            source: Source service to filter by
            pool: Mining pool to filter by
            height: Block height to filter by
            limit: Maximum number of jobs to return
            
        Returns:
            List of job documents
        """
        if not self.collections["normalized_jobs"]:
            logger.error("Database not initialized")
            return []
            
        try:
            # Build filter
            filter_query = {}
            if source:
                filter_query["source"] = source
            if pool:
                filter_query["mining_pool"] = pool
            if height is not None:
                filter_query["height"] = height
            
            # Get jobs
            cursor = self.collections["normalized_jobs"].find(
                filter_query
            ).sort("timestamp", DESCENDING).limit(limit)
            
            return await cursor.to_list(length=limit)
            
        except Exception as e:
            logger.error(f"Error getting recent jobs: {e}")
            return []
    
    async def get_job_matches(
        self,
        pool: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get recent job matches, optionally filtered by pool.
        
        Args:
            pool: Mining pool to filter by
            limit: Maximum number of matches to return
            
        Returns:
            List of job match documents
        """
        if not self.collections["job_matches"]:
            logger.error("Database not initialized")
            return []
            
        try:
            # Build filter
            filter_query = {}
            if pool:
                filter_query["primary_job.mining_pool"] = pool
            
            # Get matches
            cursor = self.collections["job_matches"].find(
                filter_query
            ).sort("timestamp", DESCENDING).limit(limit)
            
            return await cursor.to_list(length=limit)
            
        except Exception as e:
            logger.error(f"Error getting job matches: {e}")
            return []
    
    async def get_latest_stats(self) -> Optional[Dict[str, Any]]:
        """
        Get the latest statistics snapshot.
        
        Returns:
            Latest statistics document or None if not found
        """
        if not self.collections["stats"]:
            logger.error("Database not initialized")
            return None
            
        try:
            # Get latest stats
            stats = await self.collections["stats"].find_one(
                sort=[("timestamp", DESCENDING)]
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting latest stats: {e}")
            return None
    
    async def get_stats_history(
        self,
        field_path: str,
        hours: int = 24,
        interval_minutes: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get history of a specific statistics field.
        
        Args:
            field_path: Path to the field in the stats document (dot notation)
            hours: Number of hours of history to retrieve
            interval_minutes: Interval between data points in minutes
            
        Returns:
            List of {timestamp, value} documents
        """
        if not self.collections["stats"]:
            logger.error("Database not initialized")
            return []
            
        try:
            # Calculate cutoff timestamp
            cutoff = datetime.utcnow().replace(
                microsecond=0
            ).replace(
                minute=(datetime.utcnow().minute // interval_minutes) * interval_minutes,
                second=0
            ) - datetime.timedelta(hours=hours)
            cutoff_str = cutoff.isoformat()
            
            # Build aggregation pipeline
            pipeline = [
                {"$match": {"timestamp": {"$gte": cutoff_str}}},
                {"$project": {
                    "timestamp": 1,
                    "value": f"${field_path}"
                }},
                {"$match": {"value": {"$exists": True}}},
                # Group by time bucket
                {"$group": {
                    "_id": {
                        "$toDate": {
                            "$subtract": [
                                {"$toDate": "$timestamp"},
                                {"$mod": [
                                    {"$toLong": {"$toDate": "$timestamp"}},
                                    interval_minutes * 60 * 1000
                                ]}
                            ]
                        }
                    },
                    "value": {"$avg": "$value"}
                }},
                {"$sort": {"_id": 1}}
            ]
            
            cursor = self.collections["stats"].aggregate(pipeline)
            results = await cursor.to_list(length=None)
            
            # Format for chart display
            return [
                {"timestamp": doc["_id"].isoformat(), "value": doc["value"]}
                for doc in results
            ]
            
        except Exception as e:
            logger.error(f"Error getting stats history: {e}")
            return []
    
    async def get_pools_by_job_count(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top mining pools by job count.
        
        Args:
            limit: Maximum number of pools to return
            
        Returns:
            List of {pool, count} documents
        """
        if not self.collections["normalized_jobs"]:
            logger.error("Database not initialized")
            return []
            
        try:
            # Aggregate job counts by pool
            pipeline = [
                {"$group": {"_id": "$mining_pool", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": limit},
                {"$project": {"pool": "$_id", "count": 1, "_id": 0}}
            ]
            
            cursor = self.collections["normalized_jobs"].aggregate(pipeline)
            return await cursor.to_list(length=limit)
            
        except Exception as e:
            logger.error(f"Error getting pools by job count: {e}")
            return []
    
    async def get_service_activity(
        self,
        hours: int = 24,
        interval_minutes: int = 15
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get service activity over time.
        
        Args:
            hours: Number of hours of history to retrieve
            interval_minutes: Interval between data points in minutes
            
        Returns:
            Dictionary mapping services to lists of {timestamp, count} documents
        """
        if not self.collections["normalized_jobs"]:
            logger.error("Database not initialized")
            return {}
            
        try:
            # Calculate cutoff timestamp
            cutoff = datetime.utcnow().replace(
                microsecond=0
            ).replace(
                minute=(datetime.utcnow().minute // interval_minutes) * interval_minutes,
                second=0
            ) - datetime.timedelta(hours=hours)
            cutoff_str = cutoff.isoformat()
            
            # Build aggregation pipeline
            pipeline = [
                {"$match": {"timestamp": {"$gte": cutoff_str}}},
                {"$group": {
                    "_id": {
                        "service": "$source",
                        "time_bucket": {
                            "$toDate": {
                                "$subtract": [
                                    {"$toDate": "$timestamp"},
                                    {"$mod": [
                                        {"$toLong": {"$toDate": "$timestamp"}},
                                        interval_minutes * 60 * 1000
                                    ]}
                                ]
                            }
                        }
                    },
                    "count": {"$sum": 1}
                }},
                {"$sort": {"_id.time_bucket": 1}}
            ]
            
            cursor = self.collections["normalized_jobs"].aggregate(pipeline)
            results = await cursor.to_list(length=None)
            
            # Group by service
            service_activity = {}
            for doc in results:
                service = doc["_id"]["service"]
                if service not in service_activity:
                    service_activity[service] = []
                
                service_activity[service].append({
                    "timestamp": doc["_id"]["time_bucket"].isoformat(),
                    "count": doc["count"]
                })
            
            return service_activity
            
        except Exception as e:
            logger.error(f"Error getting service activity: {e}")
            return {}
    
    async def cleanup_old_data(self, days_to_keep: int = 7):
        """
        Clean up old data.
        
        Args:
            days_to_keep: Number of days of data to keep
        """
        if not self.db:
            logger.error("Database not initialized")
            return
            
        try:
            # Calculate cutoff timestamp
            cutoff = datetime.utcnow() - datetime.timedelta(days=days_to_keep)
            cutoff_str = cutoff.isoformat()
            
            # Delete old raw messages
            result = await self.collections["raw_messages"].delete_many({
                "metadata.received_at": {"$lt": cutoff_str}
            })
            logger.info(f"Deleted {result.deleted_count} old raw messages")
            
            # Delete old normalized jobs
            result = await self.collections["normalized_jobs"].delete_many({
                "timestamp": {"$lt": cutoff_str}
            })
            logger.info(f"Deleted {result.deleted_count} old normalized jobs")
            
            # Delete old job matches
            result = await self.collections["job_matches"].delete_many({
                "timestamp": {"$lt": cutoff_str}
            })
            logger.info(f"Deleted {result.deleted_count} old job matches")
            
            # Delete old stats
            result = await self.collections["stats"].delete_many({
                "timestamp": {"$lt": cutoff_str}
            })
            logger.info(f"Deleted {result.deleted_count} old stats")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    async def close(self):
        """Close database connection."""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")
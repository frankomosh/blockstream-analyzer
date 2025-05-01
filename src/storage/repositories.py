# Data access layer
import logging
from typing import Dict, Any, List, Optional, Tuple, Generic, TypeVar
from datetime import datetime, timedelta

from .db import DatabaseManager
from .models import (
    NormalizedJob, JobMatch, ServiceStats, PoolStats, 
    HeightStats, PropagationStats, AgreementStats
)

logger = logging.getLogger(__name__)

T = TypeVar('T')

class BaseRepository(Generic[T]):
    """Base repository for database operations."""
    
    def __init__(self, db_manager: DatabaseManager, collection_name: str):
        """
        Initialize the repository.
        
        Args:
            db_manager: Database manager instance
            collection_name: Name of the collection this repository handles
        """
        self.db = db_manager
        self.collection_name = collection_name
    
    async def _get_collection(self):
        """Get the MongoDB collection."""
        if not self.db.collections.get(self.collection_name):
            logger.error(f"Collection {self.collection_name} not initialized")
            return None
        return self.db.collections[self.collection_name]
    
    async def find_one(self, filter_query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find a single document matching the filter.
        
        Args:
            filter_query: Query filter
            
        Returns:
            Matching document or None if not found
        """
        collection = await self._get_collection()
        if not collection:
            return None
        
        try:
            return await collection.find_one(filter_query)
        except Exception as e:
            logger.error(f"Error in find_one: {e}")
            return None
    
    async def find_many(
        self, 
        filter_query: Dict[str, Any],
        sort_field: str = None,
        sort_direction: int = -1,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Find documents matching the filter.
        
        Args:
            filter_query: Query filter
            sort_field: Field to sort by
            sort_direction: Sort direction (1 for ascending, -1 for descending)
            limit: Maximum number of documents to return
            
        Returns:
            List of matching documents
        """
        collection = await self._get_collection()
        if not collection:
            return []
        
        try:
            cursor = collection.find(filter_query)
            
            if sort_field:
                cursor = cursor.sort(sort_field, sort_direction)
            
            cursor = cursor.limit(limit)
            
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error in find_many: {e}")
            return []
    
    async def insert_one(self, document: Dict[str, Any]) -> Optional[str]:
        """
        Insert a single document.
        
        Args:
            document: Document to insert
            
        Returns:
            ID of the inserted document, or None if insertion failed
        """
        collection = await self._get_collection()
        if not collection:
            return None
        
        try:
            result = await collection.insert_one(document)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error in insert_one: {e}")
            return None
    
    async def update_one(
        self,
        filter_query: Dict[str, Any],
        update: Dict[str, Any],
        upsert: bool = False
    ) -> bool:
        """
        Update a single document.
        
        Args:
            filter_query: Query filter
            update: Update operation
            upsert: Whether to insert if not found
            
        Returns:
            True if update was successful, False otherwise
        """
        collection = await self._get_collection()
        if not collection:
            return False
        
        try:
            result = await collection.update_one(filter_query, update, upsert=upsert)
            return result.acknowledged
        except Exception as e:
            logger.error(f"Error in update_one: {e}")
            return False
    
    async def delete_many(self, filter_query: Dict[str, Any]) -> int:
        """
        Delete documents matching the filter.
        
        Args:
            filter_query: Query filter
            
        Returns:
            Number of documents deleted
        """
        collection = await self._get_collection()
        if not collection:
            return 0
        
        try:
            result = await collection.delete_many(filter_query)
            return result.deleted_count
        except Exception as e:
            logger.error(f"Error in delete_many: {e}")
            return 0
    
    async def count(self, filter_query: Dict[str, Any] = None) -> int:
        """
        Count documents matching the filter.
        
        Args:
            filter_query: Query filter
            
        Returns:
            Number of matching documents
        """
        collection = await self._get_collection()
        if not collection:
            return 0
        
        try:
            return await collection.count_documents(filter_query or {})
        except Exception as e:
            logger.error(f"Error in count: {e}")
            return 0


class NormalizedJobRepository(BaseRepository[NormalizedJob]):
    """Repository for normalized jobs."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize the repository."""
        super().__init__(db_manager, "normalized_jobs")
    
    async def get_by_id(self, job_id: str, source: str) -> Optional[Dict[str, Any]]:
        """
        Get a job by ID and source.
        
        Args:
            job_id: Job ID
            source: Source service
            
        Returns:
            Job document or None if not found
        """
        return await self.find_one({"job_id": job_id, "source": source})
    
    async def get_by_height(self, height: int, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get jobs for a specific block height.
        
        Args:
            height: Block height
            limit: Maximum number of jobs to return
            
        Returns:
            List of job documents
        """
        return await self.find_many(
            {"height": height},
            sort_field="timestamp",
            sort_direction=-1,
            limit=limit
        )
    
    async def get_by_pool(self, pool: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get jobs for a specific mining pool.
        
        Args:
            pool: Mining pool name
            limit: Maximum number of jobs to return
            
        Returns:
            List of job documents
        """
        return await self.find_many(
            {"mining_pool": pool},
            sort_field="timestamp",
            sort_direction=-1,
            limit=limit
        )
    
    async def get_by_source(self, source: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get jobs from a specific source service.
        
        Args:
            source: Source service name
            limit: Maximum number of jobs to return
            
        Returns:
            List of job documents
        """
        return await self.find_many(
            {"source": source},
            sort_field="timestamp",
            sort_direction=-1,
            limit=limit
        )
    
    async def get_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent jobs from all sources.
        
        Args:
            limit: Maximum number of jobs to return
            
        Returns:
            List of job documents
        """
        return await self.find_many(
            {},
            sort_field="timestamp",
            sort_direction=-1,
            limit=limit
        )
    
    async def get_unique_pools(self) -> List[str]:
        """
        Get list of unique mining pools.
        
        Returns:
            List of pool names
        """
        collection = await self._get_collection()
        if not collection:
            return []
        
        try:
            result = await collection.distinct("mining_pool")
            return result
        except Exception as e:
            logger.error(f"Error getting unique pools: {e}")
            return []
    
    async def get_unique_heights(self, limit: int = 10) -> List[int]:
        """
        Get list of unique block heights, sorted descending.
        
        Args:
            limit: Maximum number of heights to return
            
        Returns:
            List of heights
        """
        collection = await self._get_collection()
        if not collection:
            return []
        
        try:
            # Get all heights
            all_heights = await collection.distinct("height")
            
            # Filter out None values and sort
            heights = [h for h in all_heights if h is not None]
            heights.sort(reverse=True)
            
            return heights[:limit]
        except Exception as e:
            logger.error(f"Error getting unique heights: {e}")
            return []
    
    async def get_job_counts_by_pool(self) -> Dict[str, int]:
        """
        Get job counts grouped by mining pool.
        
        Returns:
            Dictionary mapping pool names to job counts
        """
        collection = await self._get_collection()
        if not collection:
            return {}
        
        try:
            pipeline = [
                {"$group": {"_id": "$mining_pool", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            
            result = await collection.aggregate(pipeline).to_list(length=None)
            return {doc["_id"]: doc["count"] for doc in result}
        except Exception as e:
            logger.error(f"Error getting job counts by pool: {e}")
            return {}
    
    async def get_job_counts_by_source(self) -> Dict[str, int]:
        """
        Get job counts grouped by source service.
        
        Returns:
            Dictionary mapping source names to job counts
        """
        collection = await self._get_collection()
        if not collection:
            return {}
        
        try:
            pipeline = [
                {"$group": {"_id": "$source", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            
            result = await collection.aggregate(pipeline).to_list(length=None)
            return {doc["_id"]: doc["count"] for doc in result}
        except Exception as e:
            logger.error(f"Error getting job counts by source: {e}")
            return {}


class JobMatchRepository(BaseRepository[JobMatch]):
    """Repository for job matches."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize the repository."""
        super().__init__(db_manager, "job_matches")
    
    async def get_recent_matches(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent job matches.
        
        Args:
            limit: Maximum number of matches to return
            
        Returns:
            List of job match documents
        """
        return await self.find_many(
            {},
            sort_field="timestamp",
            sort_direction=-1,
            limit=limit
        )
    
    async def get_matches_by_pool(self, pool: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get matches for a specific mining pool.
        
        Args:
            pool: Mining pool name
            limit: Maximum number of matches to return
            
        Returns:
            List of job match documents
        """
        return await self.find_many(
            {"primary_job.mining_pool": pool},
            sort_field="timestamp",
            sort_direction=-1,
            limit=limit
        )
    
    async def get_propagation_times(
        self, 
        service_pair: str,
        hours: int = 24
    ) -> List[Tuple[datetime, float]]:
        """
        Get propagation times for a specific service pair.
        
        Args:
            service_pair: Service pair in format "service1-service2"
            hours: Number of hours of history
            
        Returns:
            List of (timestamp, propagation_time) tuples
        """
        collection = await self._get_collection()
        if not collection:
            return []
        
        # Parse service pair
        services = service_pair.split("-")
        if len(services) != 2:
            logger.error(f"Invalid service pair format: {service_pair}")
            return []
        
        # Calculate cutoff timestamp
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        cutoff_str = cutoff.isoformat()
        
        try:
            # Find matches between these services
            matches = await self.find_many(
                {
                    "timestamp": {"$gte": cutoff_str},
                    "$or": [
                        # Match when primary job is from service1 and there's a match from service2
                        {
                            "primary_job.source": services[0],
                            f"propagation_times.{services[1]}": {"$exists": True}
                        },
                        # Match when primary job is from service2 and there's a match from service1
                        {
                            "primary_job.source": services[1],
                            f"propagation_times.{services[0]}": {"$exists": True}
                        }
                    ]
                },
                sort_field="timestamp",
                sort_direction=1
            )
            
            # Extract timestamp and propagation time
            result = []
            for match in matches:
                ts = datetime.fromisoformat(match["timestamp"])
                prop_time = None
                
                if match["primary_job"]["source"] == services[0] and services[1] in match["propagation_times"]:
                    prop_time = match["propagation_times"][services[1]]
                elif match["primary_job"]["source"] == services[1] and services[0] in match["propagation_times"]:
                    prop_time = match["propagation_times"][services[0]]
                
                if prop_time is not None:
                    result.append((ts, prop_time))
            
            return result
        except Exception as e:
            logger.error(f"Error getting propagation times: {e}")
            return []
    
    async def get_match_counts_by_service_pair(self) -> Dict[str, int]:
        """
        Get match counts grouped by service pair.
        
        Returns:
            Dictionary mapping service pairs to match counts
        """
        collection = await self._get_collection()
        if not collection:
            return {}
        
        try:
            # This is more complex in MongoDB and would require custom aggregation
            # For now, we try to retrieve recent matches and count them in Python
            matches = await self.get_recent_matches(limit=1000)
            
            pair_counts = {}
            for match in matches:
                primary_source = match["primary_job"]["source"]
                
                for matched_job in match.get("matches", []):
                    if "source" not in matched_job:
                        continue
                    
                    matched_source = matched_job["source"]
                    
                    # Create a sorted pair key
                    pair = "-".join(sorted([primary_source, matched_source]))
                    
                    # Increment count
                    pair_counts[pair] = pair_counts.get(pair, 0) + 1
            
            return pair_counts
        except Exception as e:
            logger.error(f"Error getting match counts by service pair: {e}")
            return {}


class StatsRepository(BaseRepository[Dict[str, Any]]):
    """Repository for statistics snapshots."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize the repository."""
        super().__init__(db_manager, "stats")
    
    async def get_latest_stats(self) -> Optional[Dict[str, Any]]:
        """
        Get the latest statistics snapshot.
        
        Returns:
            Statistics document or None if not found
        """
        result = await self.find_many(
            {},
            sort_field="timestamp",
            sort_direction=-1,
            limit=1
        )
        
        return result[0] if result else None
    
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
        collection = await self._get_collection()
        if not collection:
            return []
        
        try:
            # Calculate cutoff timestamp
            cutoff = datetime.utcnow().replace(
                microsecond=0
            ).replace(
                minute=(datetime.utcnow().minute // interval_minutes) * interval_minutes,
                second=0
            ) - timedelta(hours=hours)
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
            
            result = await collection.aggregate(pipeline).to_list(length=None)
            
            # Format for chart display
            return [
                {"timestamp": doc["_id"].isoformat(), "value": doc["value"]}
                for doc in result
            ]
            
        except Exception as e:
            logger.error(f"Error getting stats history: {e}")
            return []
    
    async def get_service_activity_history(
        self,
        hours: int = 24,
        interval_minutes: int = 15
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get service activity over time from stats history.
        
        Args:
            hours: Number of hours of history to retrieve
            interval_minutes: Interval between data points in minutes
            
        Returns:
            Dictionary mapping services to lists of {timestamp, count} documents
        """
        collection = await self._get_collection()
        if not collection:
            return {}
        
        try:
            # Calculate cutoff timestamp
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            cutoff_str = cutoff.isoformat()
            
            # Retrieve stats documents with service data
            stats_docs = await self.find_many(
                {
                    "timestamp": {"$gte": cutoff_str},
                    "sources": {"$exists": True}
                },
                sort_field="timestamp",
                sort_direction=1
            )
            
            # Extract service activity data
            service_activity = {}
            
            for doc in stats_docs:
                timestamp = doc.get("timestamp")
                if not timestamp:
                    continue
                
                # Round timestamp to interval
                dt = datetime.fromisoformat(timestamp)
                dt = dt.replace(
                    minute=(dt.minute // interval_minutes) * interval_minutes,
                    second=0,
                    microsecond=0
                )
                rounded_ts = dt.isoformat()
                
                # Extract service data
                sources = doc.get("sources", {})
                for service, service_data in sources.items():
                    job_count = service_data.get("recent_job_count", 0)
                    
                    if service not in service_activity:
                        service_activity[service] = []
                    
                    # Add data point
                    service_activity[service].append({
                        "timestamp": rounded_ts,
                        "count": job_count
                    })
            
            return service_activity
            
        except Exception as e:
            logger.error(f"Error getting service activity history: {e}")
            return {}


class RawMessageRepository(BaseRepository[Dict[str, Any]]):
    """Repository for raw messages."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize the repository."""
        super().__init__(db_manager, "raw_messages")
    
    async def get_recent_messages(self, service: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent raw messages.
        
        Args:
            service: Optional service name to filter by
            limit: Maximum number of messages to return
            
        Returns:
            List of raw message documents
        """
        filter_query = {}
        if service:
            filter_query["metadata.service_name"] = service
        
        return await self.find_many(
            filter_query,
            sort_field="metadata.received_timestamp",
            sort_direction=-1,
            limit=limit
        )
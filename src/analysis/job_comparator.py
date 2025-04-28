# Compare jobs across services
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Set, Tuple, Optional

from .timing_analyzer import TimingAnalyzer
from .region_analyzer import RegionAnalyzer
from .stats_calculator import StatsCalculator

logger = logging.getLogger(__name__)

class JobComparator:
    """Compares and analyzes jobs from different stratum monitoring services."""
    
    def __init__(
        self,
        time_window: float = 300.0,
        window_size: int = 200,
        analyzers_enabled: Dict[str, bool] = None
    ):
        """
        Initialize the job comparator.
        
        Args:
            time_window: Time window in seconds for considering jobs related (default: 5 minutes)
            window_size: Number of jobs to keep in analysis window
            analyzers_enabled: Dictionary of analyzers to enable/disable
        """
        self.time_window = time_window
        self.window_size = window_size
        
        # Set default analyzers if not provided
        if analyzers_enabled is None:
            analyzers_enabled = {
                "timing": True,
                "region": True,
                "stats": True
            }
        
        # Initialize analyzers
        self.analyzers = {}
        if analyzers_enabled.get("timing", True):
            self.analyzers["timing"] = TimingAnalyzer(window_size=window_size)
        if analyzers_enabled.get("region", True):
            self.analyzers["region"] = RegionAnalyzer(window_size=window_size)
        if analyzers_enabled.get("stats", True):
            self.analyzers["stats"] = StatsCalculator(time_window=time_window)
        
        # Job cache for lookup and matching
        self.recent_jobs = {
            "miningpool.observer": [],
            "stratum.work": [],
            "mempool.space": []
        }
        
        # Tracking matches between services
        self.job_matches = []
        
        # Statistics
        self.pools_seen = set()
        self.heights_seen = set()
        self.processing_stats = {
            "jobs_processed": 0,
            "matches_found": 0,
            "last_processed": None,
            "avg_processing_time": 0
        }
    
    async def process_job(self, job: Dict[str, Any]):
        """
        Process a normalized job and analyze it.
        
        Args:
            job: Normalized job data
        
        Returns:
            List of matches found, if any
        """
        start_time = time.time()
        
        source = job.get("source")
        if not source or source not in self.recent_jobs:
            logger.warning(f"Unknown source: {source}")
            return []
        
        # Update stats tracking
        self.processing_stats["jobs_processed"] += 1
        self.processing_stats["last_processed"] = datetime.utcnow().isoformat()
        
        mining_pool = job.get("mining_pool", "unknown")
        height = job.get("height")
        
        if mining_pool:
            self.pools_seen.add(mining_pool)
        if height:
            self.heights_seen.add(height)
        
        # Store job with processing timestamp
        job_timestamp = time.time()
        job["_processed_at"] = job_timestamp
        self.recent_jobs[source].append(job)
        
        # Trim old jobs outside time window
        self._clean_old_jobs()
        
        # Find matching jobs from other services
        matches = await self._find_matching_jobs(job)
        
        # Process job in all enabled analyzers
        for analyzer_name, analyzer in self.analyzers.items():
            try:
                if analyzer_name == "timing":
                    analyzer.add_job(job, job_timestamp)
                elif analyzer_name == "region":
                    analyzer.add_job(job, job_timestamp)
                elif analyzer_name == "stats":
                    processing_time = time.time() - start_time
                    analyzer.add_job(job, processing_time)
                    
                    # If matches found, record agreement
                    if matches:
                        services = [source] + [match.get("source") for match in matches]
                        analyzer.add_job_agreement({
                            "services": services,
                            "job_id": job.get("job_id"),
                            "timestamp": datetime.utcnow().isoformat()
                        })
            except Exception as e:
                logger.error(f"Error processing job in {analyzer_name} analyzer: {e}")
        
        # Update average processing time
        end_time = time.time()
        processing_time = end_time - start_time
        self._update_avg_processing_time(processing_time)
        
        return matches
    
    async def _find_matching_jobs(self, job: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find matching jobs from other services.
        
        Args:
            job: Job to find matches for
            
        Returns:
            List of matching jobs from other services
        """
        source = job.get("source")
        matches = []
        
        # We'll use a combination of factors to determine matches
        # 1. Same job_id and pool (strongest indicator)
        # 2. Same prev_block_hash, height, and similar timestamp (strong indicator)
        # 3. Same merkle root (derived from coinbase + branches) (moderate indicator)
        
        for other_source, jobs in self.recent_jobs.items():
            if other_source == source:
                continue  # Skip same source
                
            for other_job in jobs:
                # Calculate match score
                score = 0
                
                # Same job_id and pool is a strong match
                if (job.get("job_id") == other_job.get("job_id") and 
                    job.get("mining_pool") == other_job.get("mining_pool")):
                    score += 10
                
                # Same prev_block_hash is a strong indicator
                if job.get("prev_block_hash") == other_job.get("prev_block_hash"):
                    score += 8
                
                # Same height is a good indicator
                if job.get("height") and job.get("height") == other_job.get("height"):
                    score += 5
                
                # Same version, bits, time are moderate indicators
                if job.get("version") == other_job.get("version"):
                    score += 2
                if job.get("bits") == other_job.get("bits"):
                    score += 2
                if job.get("time") == other_job.get("time"):
                    score += 2
                
                # If score is high enough, consider it a match
                if score >= 10:
                    matches.append(other_job)
                    break  # Only take the best match from each service
        
        # If we found matches, record the match
        if matches:
            match_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "primary_job": job,
                "matches": matches,
                "propagation_times": self._calculate_propagation_times(job, matches)
            }
            self.job_matches.append(match_data)
            
            # Keep only the last window_size matches
            if len(self.job_matches) > self.window_size:
                self.job_matches = self.job_matches[-self.window_size:]
                
            self.processing_stats["matches_found"] += 1
        
        return matches
    
    def _calculate_propagation_times(
        self, 
        primary_job: Dict[str, Any],
        matches: List[Dict[str, Any]]
    ) -> Dict[str, Optional[float]]:
        """
        Calculate propagation times between job observations.
        
        Args:
            primary_job: The reference job
            matches: List of matching jobs from other services
            
        Returns:
            Dictionary of service names to propagation times in seconds
        """
        result = {}
        
        primary_time = primary_job.get("_processed_at")
        if not primary_time:
            return {}
            
        for match in matches:
            match_time = match.get("_processed_at")
            if not match_time:
                result[match.get("source")] = None
                continue
                
            # Propagation time (absolute value since we don't know which came first)
            prop_time = abs(match_time - primary_time)
            result[match.get("source")] = prop_time
            
        return result
    
    def _clean_old_jobs(self):
        """Remove jobs outside the time window."""
        now = time.time()
        cutoff = now - self.time_window
        
        for source in self.recent_jobs:
            self.recent_jobs[source] = [
                job for job in self.recent_jobs[source]
                if job.get("_processed_at", 0) >= cutoff
            ]
    
    def _update_avg_processing_time(self, processing_time: float):
        """
        Update the average processing time.
        
        Args:
            processing_time: Processing time for the current job
        """
        current_avg = self.processing_stats["avg_processing_time"]
        jobs_processed = self.processing_stats["jobs_processed"]
        
        # Calculate new average
        if jobs_processed <= 1:
            new_avg = processing_time
        else:
            new_avg = ((current_avg * (jobs_processed - 1)) + processing_time) / jobs_processed
        
        self.processing_stats["avg_processing_time"] = new_avg
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about jobs.
        
        Returns:
            Dictionary of statistics
        """
        stats = {
            "sources": {},
            "processing": self.processing_stats.copy(),
            "current_heights": sorted(list(self.heights_seen), reverse=True)[:5],
            "pool_count": len(self.pools_seen)
        }
        
        # Source statistics
        for source, jobs in self.recent_jobs.items():
            stats["sources"][source] = {
                "recent_job_count": len(jobs),
                "pools_observed": len(set(job.get("mining_pool", "unknown") for job in jobs)),
                "latest_job_time": max([job.get("_processed_at", 0) for job in jobs]) if jobs else None
            }
        
        # Add analyzer-specific statistics
        for analyzer_name, analyzer in self.analyzers.items():
            if analyzer_name == "timing":
                stats["timing"] = analyzer.get_timing_report()
            elif analyzer_name == "region":
                stats["region"] = analyzer.get_region_metrics()
            elif analyzer_name == "stats":
                stats["general"] = analyzer.get_comprehensive_stats()
        
        # Add match statistics
        stats["matches"] = {
            "total": len(self.job_matches),
            "recent": self.job_matches[-5:] if self.job_matches else []
        }
        
        return stats
    
    def get_analyzers(self) -> Dict[str, Any]:
        """
        Get the analyzers.
        
        Returns:
            Dictionary of analyzers
        """
        return self.analyzers
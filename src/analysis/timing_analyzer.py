# Analyze timing differences
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional
from collections import defaultdict
import numpy as np

logger = logging.getLogger(__name__)

class TimingAnalyzer:
    """Analyzes timing differences between stratum monitoring services."""
    
    def __init__(self, window_size: int = 200):
        """
        Initialize the timing analyzer.
        
        Args:
            window_size: Number of jobs to keep in the analysis window
        """
        self.window_size = window_size
        
        # Job timing data by service
        self.service_job_times = {
            "miningpool.observer": [],
            "stratum.work": [],
            "mempool.space": []
        }
        
        # Matched job timing data
        self.job_matches = []
        
        # Propagation time statistics
        self.propagation_stats = defaultdict(lambda: {
            "times": [],
            "mean": None,
            "median": None,
            "min": None,
            "max": None,
            "stddev": None
        })
        
        # Inter-arrival time statistics by service
        self.inter_arrival_stats = {
            "miningpool.observer": {"times": [], "mean": None, "median": None},
            "stratum.work": {"times": [], "mean": None, "median": None},
            "mempool.space": {"times": [], "mean": None, "median": None}
        }
    
    def add_job(self, job: Dict[str, Any], received_timestamp: float):
        """
        Add a job to the timing analysis.
        
        Args:
            job: Normalized job data
            received_timestamp: Timestamp when job was received
        """
        source = job.get("source")
        if not source or source not in self.service_job_times:
            logger.warning(f"Unknown source: {source}")
            return
        
        # Add job timing data
        job_timing = {
            "job_id": job.get("job_id"),
            "mining_pool": job.get("mining_pool", "unknown"),
            "height": job.get("height"),
            "timestamp": job.get("timestamp"),
            "received_at": received_timestamp,
            "prev_block_hash": job.get("prev_block_hash"),
            "job": job  # Store reference to full job
        }
        
        # Add to service job times
        self.service_job_times[source].append(job_timing)
        
        # Trim old jobs if window is exceeded
        if len(self.service_job_times[source]) > self.window_size:
            self.service_job_times[source] = self.service_job_times[source][-self.window_size:]
        
        # Calculate inter-arrival time if we have previous jobs
        if len(self.service_job_times[source]) > 1:
            prev_job = self.service_job_times[source][-2]
            current_job = self.service_job_times[source][-1]
            
            inter_arrival = current_job["received_at"] - prev_job["received_at"]
            self.inter_arrival_stats[source]["times"].append(inter_arrival)
            
            # Keep only the last window_size inter-arrival times
            if len(self.inter_arrival_stats[source]["times"]) > self.window_size:
                self.inter_arrival_stats[source]["times"] = self.inter_arrival_stats[source]["times"][-self.window_size:]
        
        # Check for matching jobs from other services
        self._check_for_matches(job_timing, source)
        
        # Update statistics
        self._update_statistics()
    
    def _check_for_matches(self, job_timing: Dict[str, Any], source: str):
        """
        Check for matching jobs from other services.
        
        Args:
            job_timing: Timing data for the job
            source: Source service
        """
        # Find matches based on job_id, prev_block_hash, and height
        matches = []
        
        for other_source, jobs in self.service_job_times.items():
            if other_source == source:
                continue  # Skip same source
            
            # Look for a match in this service's jobs
            for other_job in jobs:
                # Consider it a match if same job_id and mining_pool,
                # or same prev_block_hash and height (if available)
                is_match = False
                
                # Match by job_id and pool
                if (job_timing["job_id"] == other_job["job_id"] and 
                    job_timing["mining_pool"] == other_job["mining_pool"]):
                    is_match = True
                
                # Match by prev_block_hash and height (if both available)
                elif (job_timing["prev_block_hash"] and job_timing["height"] and
                      job_timing["prev_block_hash"] == other_job["prev_block_hash"] and
                      job_timing["height"] == other_job["height"]):
                    is_match = True
                
                if is_match:
                    # Calculate propagation time (absolute difference)
                    prop_time = abs(job_timing["received_at"] - other_job["received_at"])
                    
                    # Determine which job arrived first
                    first_source = source if job_timing["received_at"] <= other_job["received_at"] else other_source
                    second_source = other_source if first_source == source else source
                    
                    match_data = {
                        "job_id": job_timing["job_id"],
                        "mining_pool": job_timing["mining_pool"],
                        "sources": [source, other_source],
                        "first_source": first_source,
                        "second_source": second_source,
                        "propagation_time": prop_time,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    # Add to matches
                    matches.append((other_source, match_data))
                    
                    # Create key for source pair statistics
                    source_pair = f"{first_source}-{second_source}"
                    
                    # Update propagation stats
                    self.propagation_stats[source_pair]["times"].append(prop_time)
                    
                    # Keep only window_size propagation times
                    if len(self.propagation_stats[source_pair]["times"]) > self.window_size:
                        self.propagation_stats[source_pair]["times"] = self.propagation_stats[source_pair]["times"][-self.window_size:]
                    
                    # We only need one match per service
                    break
        
        # If we found matches, add to job_matches
        if matches:
            match_entry = {
                "job_id": job_timing["job_id"],
                "mining_pool": job_timing["mining_pool"],
                "primary_source": source,
                "matches": [match_data for _, match_data in matches],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.job_matches.append(match_entry)
            
            # Keep only the last window_size matches
            if len(self.job_matches) > self.window_size:
                self.job_matches = self.job_matches[-self.window_size:]
    
    def _update_statistics(self):
        """Update all timing statistics."""
        # Update inter-arrival statistics
        for source, stats in self.inter_arrival_stats.items():
            times = stats["times"]
            if times:
                stats["mean"] = np.mean(times)
                stats["median"] = np.median(times)
                stats["min"] = np.min(times)
                stats["max"] = np.max(times)
                stats["stddev"] = np.std(times)
        
        # Update propagation statistics
        for source_pair, stats in self.propagation_stats.items():
            times = stats["times"]
            if times:
                stats["mean"] = np.mean(times)
                stats["median"] = np.median(times)
                stats["min"] = np.min(times)
                stats["max"] = np.max(times)
                stats["stddev"] = np.std(times)
    
    def get_propagation_stats(self) -> Dict[str, Any]:
        """
        Get propagation statistics for all source pairs.
        
        Returns:
            Dictionary of propagation statistics
        """
        stats = {}
        
        for source_pair, pair_stats in self.propagation_stats.items():
            if pair_stats["times"]:
                stats[source_pair] = {
                    "mean": pair_stats["mean"],
                    "median": pair_stats["median"],
                    "min": pair_stats["min"],
                    "max": pair_stats["max"],
                    "stddev": pair_stats["stddev"],
                    "sample_count": len(pair_stats["times"])
                }
        
        return stats
    
    def get_inter_arrival_stats(self) -> Dict[str, Any]:
        """
        Get inter-arrival time statistics for all services.
        
        Returns:
            Dictionary of inter-arrival time statistics
        """
        stats = {}
        
        for source, source_stats in self.inter_arrival_stats.items():
            if source_stats["times"]:
                stats[source] = {
                    "mean": source_stats["mean"],
                    "median": source_stats["median"],
                    "min": source_stats["min"],
                    "max": source_stats["max"],
                    "stddev": source_stats["stddev"],
                    "sample_count": len(source_stats["times"])
                }
        
        return stats
    
    def get_recent_matches(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent job matches.
        
        Args:
            limit: Maximum number of matches to return
            
        Returns:
            List of recent job matches
        """
        return self.job_matches[-limit:]
    
    def get_first_provider_stats(self) -> Dict[str, Dict[str, float]]:
        """
        Get statistics on which service typically provides jobs first.
        
        Returns:
            Dictionary with service names and percentage of times they were first
        """
        first_counts = defaultdict(int)
        total_matches = len(self.job_matches)
        
        if total_matches == 0:
            return {}
        
        # Count how many times each service was first
        for match in self.job_matches:
            for match_data in match.get("matches", []):
                first_source = match_data.get("first_source")
                if first_source:
                    first_counts[first_source] += 1
        
        # Calculate percentages
        result = {}
        for source, count in first_counts.items():
            result[source] = {
                "count": count,
                "percentage": (count / total_matches) * 100
            }
        
        return result
    
    def get_timing_report(self) -> Dict[str, Any]:
        """
        Get comprehensive timing analysis report.
        
        Returns:
            Dictionary with all timing statistics
        """
        return {
            "propagation_stats": self.get_propagation_stats(),
            "inter_arrival_stats": self.get_inter_arrival_stats(),
            "first_provider_stats": self.get_first_provider_stats(),
            "recent_matches": self.get_recent_matches(5),
            "match_count": len(self.job_matches),
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
# Statistical analysis
import logging
from typing import Dict, Any, List, Set, Tuple, Optional, Counter
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)

class StatsCalculator:
    """Calculates statistical metrics for stratum monitoring comparison."""
    
    def __init__(self, time_window: float = 3600.0):
        """
        Initialize the stats calculator.
        
        Args:
            time_window: Time window in seconds for statistics (default: 1 hour)
        """
        self.time_window = time_window
        
        # Job statistics
        self.job_stats = {
            "by_service": defaultdict(list),        # Service -> jobs
            "by_pool": defaultdict(list),           # Mining pool -> jobs
            "by_height": defaultdict(list),         # Block height -> jobs
            "total_jobs": 0,
            "last_update": None
        }
        
        # Agreement statistics
        self.agreement_stats = {
            "job_agreements": [],                   # List of job agreement records
            "agreement_counts": Counter(),          # Counter of service combinations that agreed
            "agreement_rates": {},                  # Agreement rates between services
            "last_agreement": None
        }
        
        # Job processing times
        self.processing_times = []
    
    def add_job(self, job: Dict[str, Any], processing_time: Optional[float] = None):
        """
        Add a job to the statistics calculation.
        
        Args:
            job: Normalized job data
            processing_time: Time taken to process the job (if available)
        """
        source = job.get("source")
        mining_pool = job.get("mining_pool", "unknown")
        height = job.get("height")
        
        # Add to job statistics
        job_record = {
            "job_id": job.get("job_id"),
            "mining_pool": mining_pool,
            "height": height,
            "timestamp": job.get("timestamp"),
            "source": source,
            "version": job.get("version"),
            "bits": job.get("bits"),
            "time": job.get("time"),
            "processing_time": processing_time
        }
        
        # Store by different dimensions
        self.job_stats["by_service"][source].append(job_record)
        self.job_stats["by_pool"][mining_pool].append(job_record)
        if height is not None:
            self.job_stats["by_height"][height].append(job_record)
        
        # Update total count
        self.job_stats["total_jobs"] += 1
        self.job_stats["last_update"] = datetime.utcnow()
        
        # Store processing time if available
        if processing_time is not None:
            self.processing_times.append(processing_time)
        
        # Clean up old data
        self._clean_old_data()
    
    def add_job_agreement(self, agreement: Dict[str, Any]):
        """
        Record an agreement between services on a job.
        
        Args:
            agreement: Dictionary with agreement information
                - services: List of services that agreed
                - job_id: ID of the job
                - timestamp: When the agreement was detected
        """
        if "services" not in agreement or not agreement["services"]:
            return
        
        # Add to agreements
        self.agreement_stats["job_agreements"].append(agreement)
        
        # Update agreement counts
        services_tuple = tuple(sorted(agreement["services"]))
        self.agreement_stats["agreement_counts"][services_tuple] += 1
        
        # Update last agreement timestamp
        self.agreement_stats["last_agreement"] = datetime.utcnow()
        
        # Update agreement rates
        self._update_agreement_rates()
    
    def _update_agreement_rates(self):
        """Update agreement rates between services."""
        # Count jobs by service
        service_counts = {
            service: len(jobs)
            for service, jobs in self.job_stats["by_service"].items()
        }
        
        # Calculate agreement rates
        agreement_rates = {}
        
        for services, count in self.agreement_stats["agreement_counts"].items():
            if len(services) < 2:
                continue  # Need at least 2 services to have an agreement
            
            # Calculate the rate based on the service with the fewest jobs
            min_service_count = min(service_counts.get(service, 0) for service in services)
            
            if min_service_count > 0:
                rate = count / min_service_count
                agreement_rates[services] = rate
        
        self.agreement_stats["agreement_rates"] = agreement_rates
    
    def _clean_old_data(self):
        """Remove data outside the time window."""
        cutoff = datetime.utcnow() - timedelta(seconds=self.time_window)
        cutoff_str = cutoff.isoformat()
        
        # Clean job statistics
        for service, jobs in list(self.job_stats["by_service"].items()):
            self.job_stats["by_service"][service] = [
                job for job in jobs 
                if job.get("timestamp", "") >= cutoff_str
            ]
            
        for pool, jobs in list(self.job_stats["by_pool"].items()):
            self.job_stats["by_pool"][pool] = [
                job for job in jobs 
                if job.get("timestamp", "") >= cutoff_str
            ]
            
        for height, jobs in list(self.job_stats["by_height"].items()):
            self.job_stats["by_height"][height] = [
                job for job in jobs 
                if job.get("timestamp", "") >= cutoff_str
            ]
        
        # Clean agreement statistics
        self.agreement_stats["job_agreements"] = [
            agreement for agreement in self.agreement_stats["job_agreements"]
            if agreement.get("timestamp", "") >= cutoff_str
        ]
        
        # Recalculate agreement counts and rates
        self.agreement_stats["agreement_counts"] = Counter()
        for agreement in self.agreement_stats["job_agreements"]:
            services_tuple = tuple(sorted(agreement["services"]))
            self.agreement_stats["agreement_counts"][services_tuple] += 1
        
        self._update_agreement_rates()
    
    def get_service_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for each service.
        
        Returns:
            Dictionary mapping services to their statistics
        """
        stats = {}
        
        for service, jobs in self.job_stats["by_service"].items():
            if not jobs:
                continue
                
            # Count unique pools
            pools = set(job["mining_pool"] for job in jobs)
            
            # Count unique heights
            heights = set(job["height"] for job in jobs if job["height"] is not None)
            
            # Calculate job rate (jobs per minute)
            time_range_sec = min(self.time_window, 
                               (datetime.utcnow() - datetime.fromisoformat(min(job["timestamp"] for job in jobs))).total_seconds())
            job_rate = (len(jobs) / time_range_sec) * 60 if time_range_sec > 0 else 0
            
            stats[service] = {
                "job_count": len(jobs),
                "pools_count": len(pools),
                "heights_count": len(heights),
                "job_rate_per_minute": job_rate,
                "latest_job": max(jobs, key=lambda x: x["timestamp"]) if jobs else None
            }
        
        return stats
    
    def get_pool_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for each mining pool.
        
        Returns:
            Dictionary mapping pools to their statistics
        """
        stats = {}
        
        for pool, jobs in self.job_stats["by_pool"].items():
            if not jobs:
                continue
                
            # Count services that observed this pool
            services = set(job["source"] for job in jobs)
            
            # Group jobs by height
            jobs_by_height = defaultdict(list)
            for job in jobs:
                if job["height"] is not None:
                    jobs_by_height[job["height"]].append(job)
            
            # Calculate average jobs per height
            avg_jobs_per_height = (sum(len(height_jobs) for height_jobs in jobs_by_height.values()) / 
                                  len(jobs_by_height)) if jobs_by_height else 0
            
            stats[pool] = {
                "job_count": len(jobs),
                "services_count": len(services),
                "heights_count": len(jobs_by_height),
                "avg_jobs_per_height": avg_jobs_per_height,
                "latest_job": max(jobs, key=lambda x: x["timestamp"]) if jobs else None
            }
        
        return stats
    
    def get_height_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for each block height.
        
        Returns:
            Dictionary mapping heights to their statistics
        """
        stats = {}
        
        for height, jobs in self.job_stats["by_height"].items():
            if not jobs:
                continue
                
            # Count services that observed this height
            services = set(job["source"] for job in jobs)
            
            # Count pools that produced jobs for this height
            pools = set(job["mining_pool"] for job in jobs)
            
            # Calculate time range for this height
            first_seen = min(datetime.fromisoformat(job["timestamp"]) for job in jobs)
            last_seen = max(datetime.fromisoformat(job["timestamp"]) for job in jobs)
            time_range = (last_seen - first_seen).total_seconds()
            
            stats[height] = {
                "job_count": len(jobs),
                "services_count": len(services),
                "pools_count": len(pools),
                "services": list(services),
                "pools": list(pools),
                "first_seen": first_seen.isoformat(),
                "last_seen": last_seen.isoformat(),
                "time_range_seconds": time_range
            }
        
        return stats
    
    def get_agreement_stats(self) -> Dict[str, Any]:
        """
        Get statistics on agreement between services.
        
        Returns:
            Dictionary with agreement statistics
        """
        # Format agreement counts for easier consumption
        formatted_counts = {}
        for services, count in self.agreement_stats["agreement_counts"].items():
            formatted_counts["-".join(services)] = count
        
        # Format agreement rates for easier consumption
        formatted_rates = {}
        for services, rate in self.agreement_stats["agreement_rates"].items():
            formatted_rates["-".join(services)] = rate
        
        return {
            "agreement_counts": formatted_counts,
            "agreement_rates": formatted_rates,
            "total_agreements": sum(self.agreement_stats["agreement_counts"].values()),
            "recent_agreements": self.agreement_stats["job_agreements"][-10:] if self.agreement_stats["job_agreements"] else []
        }
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get statistics on job processing times.
        
        Returns:
            Dictionary with processing time statistics
        """
        if not self.processing_times:
            return {
                "count": 0,
                "mean": None,
                "median": None,
                "min": None,
                "max": None,
                "stddev": None
            }
        
        return {
            "count": len(self.processing_times),
            "mean": np.mean(self.processing_times),
            "median": np.median(self.processing_times),
            "min": np.min(self.processing_times),
            "max": np.max(self.processing_times),
            "stddev": np.std(self.processing_times)
        }
    
    def get_job_frequency_by_pool(self) -> Dict[str, float]:
        """
        Get job frequency per minute by mining pool.
        
        Returns:
            Dictionary mapping pools to job frequencies
        """
        frequencies = {}
        
        for pool, jobs in self.job_stats["by_pool"].items():
            if not jobs:
                continue
                
            # Calculate job rate (jobs per minute)
            time_range_sec = min(self.time_window, 
                               (datetime.utcnow() - datetime.fromisoformat(min(job["timestamp"] for job in jobs))).total_seconds())
            job_rate = (len(jobs) / time_range_sec) * 60 if time_range_sec > 0 else 0
            
            frequencies[pool] = job_rate
        
        return frequencies
    
    def get_version_distribution(self) -> Dict[str, Dict[str, int]]:
        """
        Get distribution of block versions by service.
        
        Returns:
            Dictionary mapping services to version distributions
        """
        distribution = {}
        
        for service, jobs in self.job_stats["by_service"].items():
            if not jobs:
                continue
                
            # Count occurrences of each version
            version_counts = Counter(job["version"] for job in jobs if job["version"])
            
            distribution[service] = dict(version_counts)
        
        return distribution
    
    def get_top_pools(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top mining pools by job count.
        
        Args:
            limit: Maximum number of pools to return
            
        Returns:
            List of pool statistics, sorted by job count
        """
        pool_stats = self.get_pool_stats()
        
        # Sort pools by job count
        sorted_pools = sorted(
            [{"pool": pool, **stats} for pool, stats in pool_stats.items()],
            key=lambda x: x["job_count"],
            reverse=True
        )
        
        return sorted_pools[:limit]
    
    def get_latest_heights(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get statistics for the latest block heights.
        
        Args:
            limit: Maximum number of heights to return
            
        Returns:
            List of height statistics, sorted by height (descending)
        """
        height_stats = self.get_height_stats()
        
        # Sort heights in descending order
        sorted_heights = sorted(
            [{"height": int(height), **stats} for height, stats in height_stats.items()],
            key=lambda x: x["height"],
            reverse=True
        )
        
        return sorted_heights[:limit]
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics report.
        
        Returns:
            Dictionary with all statistics
        """
        return {
            "service_stats": self.get_service_stats(),
            "pool_stats": self.get_pool_stats(),
            "height_stats": self.get_latest_heights(10),
            "agreement_stats": self.get_agreement_stats(),
            "processing_stats": self.get_processing_stats(),
            "job_frequency_by_pool": self.get_job_frequency_by_pool(),
            "version_distribution": self.get_version_distribution(),
            "top_pools": self.get_top_pools(),
            "total_jobs": self.job_stats["total_jobs"],
            "time_window_seconds": self.time_window,
            "timestamp": datetime.utcnow().isoformat()
        }
# Regional analysis
import logging
from typing import Dict, Any, List, Set, Tuple, Optional
from collections import defaultdict
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)

class RegionAnalyzer:
    """Analyzes regional differences in stratum monitoring services."""
    
    def __init__(self, window_size: int = 200):
        """
        Initialize the region analyzer.
        
        Args:
            window_size: Number of jobs to keep in analysis window
        """
        self.window_size = window_size
        
        # Jobs by service and region
        self.region_jobs = defaultdict(lambda: defaultdict(list))
        
        # Jobs by mining pool and region
        self.pool_region_jobs = defaultdict(lambda: defaultdict(list))
        
        # Region statistics
        self.region_stats = {
            "service_regions": defaultdict(set),  # Service -> set of regions seen
            "pool_regions": defaultdict(set),     # Pool -> set of regions seen
            "region_pools": defaultdict(set),     # Region -> set of pools seen
            "propagation_by_region": defaultdict(lambda: defaultdict(list))  # source_region-target_region -> propagation times
        }
    
    def add_job(self, job: Dict[str, Any], received_timestamp: float):
        """
        Add a job to the region analysis.
        
        Args:
            job: Normalized job data
            received_timestamp: Timestamp when job was received
        """
        source = job.get("source")
        mining_pool = job.get("mining_pool", "unknown")
        
        # Extract region information
        source_region = job.get("region", {}).get("source", "unknown")
        target_region = job.get("region", {}).get("target", "unknown")
        
        # Enrich job data with timing
        job_data = {
            "job_id": job.get("job_id"),
            "mining_pool": mining_pool,
            "height": job.get("height"),
            "source_region": source_region,
            "target_region": target_region,
            "received_at": received_timestamp,
            "job": job  # Store reference to full job
        }
        
        # Store by service and region
        self.region_jobs[source][target_region].append(job_data)
        if len(self.region_jobs[source][target_region]) > self.window_size:
            self.region_jobs[source][target_region] = self.region_jobs[source][target_region][-self.window_size:]
        
        # Store by pool and region
        self.pool_region_jobs[mining_pool][target_region].append(job_data)
        if len(self.pool_region_jobs[mining_pool][target_region]) > self.window_size:
            self.pool_region_jobs[mining_pool][target_region] = self.pool_region_jobs[mining_pool][target_region][-self.window_size:]
        
        # Update region statistics
        self.region_stats["service_regions"][source].add(target_region)
        self.region_stats["pool_regions"][mining_pool].add(target_region)
        self.region_stats["region_pools"][target_region].add(mining_pool)
        
        # Check for cross-region matches
        self._check_cross_region_matches(job_data)
    
    def _check_cross_region_matches(self, job_data: Dict[str, Any]):
        """
        Check for matches across different regions.
        
        Args:
            job_data: Job data to check for matches
        """
        source = job_data["job"].get("source")
        job_id = job_data["job_id"]
        mining_pool = job_data["mining_pool"]
        target_region = job_data["target_region"]
        received_at = job_data["received_at"]
        
        # Look for matching jobs in other regions for the same service
        for other_region, jobs in self.region_jobs[source].items():
            if other_region == target_region:
                continue  # Skip same region
            
            # Look for matching job_id and pool in this region
            for other_job in jobs:
                if (other_job["job_id"] == job_id and 
                    other_job["mining_pool"] == mining_pool):
                    
                    # Calculate propagation time between regions
                    prop_time = abs(received_at - other_job["received_at"])
                    
                    # Determine direction (which region received first)
                    first_region = target_region if received_at <= other_job["received_at"] else other_region
                    second_region = other_region if first_region == target_region else target_region
                    
                    # Create key for region pair
                    region_pair = f"{first_region}-{second_region}"
                    
                    # Store propagation time
                    self.region_stats["propagation_by_region"][region_pair].append(prop_time)
                    
                    # Keep only window_size propagation times
                    if len(self.region_stats["propagation_by_region"][region_pair]) > self.window_size:
                        self.region_stats["propagation_by_region"][region_pair] = self.region_stats["propagation_by_region"][region_pair][-self.window_size:]
                    
                    break  # We only need one match per region
    
    def get_region_distribution(self) -> Dict[str, Dict[str, int]]:
        """
        Get distribution of jobs by region for each service.
        
        Returns:
            Dictionary mapping services to region counts
        """
        distribution = {}
        
        for service, regions in self.region_jobs.items():
            service_dist = {}
            
            for region, jobs in regions.items():
                service_dist[region] = len(jobs)
            
            distribution[service] = service_dist
        
        return distribution
    
    def get_pool_region_distribution(self) -> Dict[str, Dict[str, int]]:
        """
        Get distribution of pools by region.
        
        Returns:
            Dictionary mapping pools to region counts
        """
        distribution = {}
        
        for pool, regions in self.pool_region_jobs.items():
            pool_dist = {}
            
            for region, jobs in regions.items():
                pool_dist[region] = len(jobs)
            
            distribution[pool] = pool_dist
        
        return distribution
    
    def get_region_propagation_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get propagation statistics between regions.
        
        Returns:
            Dictionary mapping region pairs to propagation statistics
        """
        stats = {}
        
        for region_pair, times in self.region_stats["propagation_by_region"].items():
            if times:
                stats[region_pair] = {
                    "mean": np.mean(times),
                    "median": np.median(times),
                    "min": np.min(times),
                    "max": np.max(times),
                    "stddev": np.std(times),
                    "sample_count": len(times)
                }
        
        return stats
    
    def get_region_pool_matrix(self) -> Dict[str, Dict[str, Set[str]]]:
        """
        Get matrix of which pools are seen in which regions.
        
        Returns:
            Dictionary mapping services to regions to pools
        """
        matrix = {}
        
        for service, regions in self.region_jobs.items():
            service_matrix = {}
            
            for region, jobs in regions.items():
                pools = set(job["mining_pool"] for job in jobs)
                service_matrix[region] = pools
            
            matrix[service] = service_matrix
        
        return matrix
    
    def get_region_exclusivity(self) -> Dict[str, List[str]]:
        """
        Get pools that are exclusive to specific regions.
        
        Returns:
            Dictionary mapping regions to exclusive pools
        """
        exclusivity = {}
        
        # Get all pools
        all_pools = set()
        for pools in self.region_stats["region_pools"].values():
            all_pools.update(pools)
        
        # For each region, find pools exclusive to it
        for region, pools in self.region_stats["region_pools"].items():
            # Pools in this region but not in others
            exclusive_pools = []
            
            for pool in pools:
                exclusive = True
                
                # Check if pool is in any other region
                for other_region, other_pools in self.region_stats["region_pools"].items():
                    if other_region != region and pool in other_pools:
                        exclusive = False
                        break
                
                if exclusive:
                    exclusive_pools.append(pool)
            
            if exclusive_pools:
                exclusivity[region] = exclusive_pools
        
        return exclusivity
    
    def get_region_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive regional analysis metrics.
        
        Returns:
            Dictionary with all regional statistics
        """
        all_regions = set()
        for regions in self.region_stats["service_regions"].values():
            all_regions.update(regions)
        
        return {
            "region_distribution": self.get_region_distribution(),
            "pool_region_distribution": self.get_pool_region_distribution(),
            "region_propagation_stats": self.get_region_propagation_stats(),
            "region_pool_matrix": self.get_region_pool_matrix(),
            "region_exclusivity": self.get_region_exclusivity(),
            "all_regions": list(all_regions),
            "service_region_count": {service: len(regions) for service, regions in self.region_stats["service_regions"].items()},
            "pool_region_count": {pool: len(regions) for pool, regions in self.region_stats["pool_regions"].items()},
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
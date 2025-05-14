import React, { useState, useEffect } from 'react';
import { Search, Filter, RefreshCw, Download, AlertCircle } from 'lucide-react';
import { endpoints } from '../utils/api';

// Import components
import JobsTable from '../components/JobsTable';

function JobComparisonPage() {
  // State for jobs data
  const [jobs, setJobs] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // State for filters
  const [source, setSource] = useState('');
  const [pool, setPool] = useState('');
  const [height, setHeight] = useState('');
  
  // State for pagination
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [totalPages, setTotalPages] = useState(1);
  
  // State for available pools and heights for filtering
  const [availablePools, setAvailablePools] = useState([]);
  const [availableHeights, setAvailableHeights] = useState([]);
  
  // State for matches
  const [jobMatches, setJobMatches] = useState([]);
  const [showMatches, setShowMatches] = useState(false);
  
  // Fetch jobs on mount and when filters change
  useEffect(() => {
    fetchJobs();
  }, [source, pool, height, page, pageSize]);
  
  // Fetch available filters on mount
  useEffect(() => {
    fetchFilters();
  }, []);
  
  // Fetch jobs
  const fetchJobs = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Build params
      const params = { page, page_size: pageSize };
      if (source) params.source = source;
      if (pool) params.pool = pool;
      if (height) params.height = parseInt(height);
      
      // Fetch jobs
      const response = await endpoints.getJobs(params);
      setJobs(response.data.jobs);
      setTotalPages(response.data.total_pages);
      
      // If showing matches, fetch matches for these jobs
      if (showMatches) {
        await fetchMatches();
      }
    } catch (err) {
      console.error('Error fetching jobs:', err);
      setError(err);
    } finally {
      setIsLoading(false);
    }
  };
  
  // Fetch filters (pools and heights)
  const fetchFilters = async () => {
    try {
      // Fetch pools
      const poolsResponse = await endpoints.getPools(100);
      setAvailablePools(poolsResponse.data.pools.map(pool => pool.name));
      
      // Fetch recent heights
      const statsResponse = await endpoints.getStats();
      if (statsResponse.data.latest_heights) {
        setAvailableHeights(statsResponse.data.latest_heights.map(h => h.height));
      }
    } catch (err) {
      console.error('Error fetching filters:', err);
    }
  };
  
  // Fetch matches
  const fetchMatches = async () => {
    try {
      const response = await endpoints.getMatches({ limit: 50 });
      setJobMatches(response.data.matches);
    } catch (err) {
      console.error('Error fetching matches:', err);
    }
  };
  
  // Handle filter changes
  const handleSourceChange = (e) => {
    setSource(e.target.value);
    setPage(1);
  };
  
  const handlePoolChange = (e) => {
    setPool(e.target.value);
    setPage(1);
  };
  
  const handleHeightChange = (e) => {
    setHeight(e.target.value);
    setPage(1);
  };
  
  // Handle reset filters
  const handleResetFilters = () => {
    setSource('');
    setPool('');
    setHeight('');
    setPage(1);
  };
  
  // Handle toggle matches
  const handleToggleMatches = async () => {
    const newShowMatches = !showMatches;
    setShowMatches(newShowMatches);
    
    if (newShowMatches) {
      await fetchMatches();
    }
  };
  
  // Handle export data
  const handleExportData = () => {
    // Create a CSV of the current jobs
    const headers = ['Job ID', 'Source', 'Mining Pool', 'Height', 'Timestamp', 'Previous Block Hash'];
    
    const csvContent = [
      headers.join(','),
      ...jobs.map(job => [
        job.job_id,
        job.source,
        job.mining_pool,
        job.height,
        job.timestamp,
        job.prev_block_hash
      ].join(','))
    ].join('\n');
    
    // Create and download the file
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `stratum-jobs-${new Date().toISOString().slice(0, 10)}.csv`);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };
  
  // Find matches for a job
  const findMatchesForJob = (job) => {
    return jobMatches
      .filter(match => 
        (match.primary_job.job_id === job.job_id && match.primary_job.source === job.source) ||
        match.matched_jobs.some(mj => mj.job.job_id === job.job_id && mj.job.source === job.source)
      )
      .flatMap(match => {
        // Include primary job if it's not the current job
        const matches = [];
        if (!(match.primary_job.job_id === job.job_id && match.primary_job.source === job.source)) {
          matches.push(match.primary_job);
        }
        
        // Include matched jobs if they're not the current job
        matches.push(...match.matched_jobs
          .filter(mj => !(mj.job.job_id === job.job_id && mj.job.source === job.source))
          .map(mj => mj.job)
        );
        
        return matches;
      });
  };
  
  // Prepare jobs data with matches if showing matches
  const prepareJobsData = () => {
    if (!showMatches || jobMatches.length === 0) return jobs;
    
    return jobs.map(job => {
      const matches = findMatchesForJob(job);
      return {
        ...job,
        matches
      };
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Job Comparison</h1>
        <div className="flex items-center space-x-2">
          <button 
            onClick={fetchJobs} 
            disabled={isLoading}
            className="flex items-center px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            <RefreshCw size={16} className={`mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button 
            onClick={handleExportData}
            className="flex items-center px-3 py-2 bg-green-600 text-white rounded hover:bg-green-700"
          >
            <Download size={16} className="mr-2" />
            Export
          </button>
        </div>
      </div>
      
      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center">
            <Filter size={18} className="text-gray-500 mr-2" />
            <span className="text-gray-700 font-medium">Filters:</span>
          </div>
          
          <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Source filter */}
            <div>
              <label htmlFor="source-filter" className="block text-sm font-medium text-gray-700 mb-1">Source</label>
              <select
                id="source-filter"
                value={source}
                onChange={handleSourceChange}
                className="w-full rounded-md border border-gray-300 shadow-sm px-3 py-2 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">All Sources</option>
                <option value="miningpool.observer">miningpool.observer</option>
                <option value="stratum.work">stratum.work</option>
                <option value="mempool.space">mempool.space</option>
              </select>
            </div>
            
            {/* Pool filter */}
            <div>
              <label htmlFor="pool-filter" className="block text-sm font-medium text-gray-700 mb-1">Mining Pool</label>
              <select
                id="pool-filter"
                value={pool}
                onChange={handlePoolChange}
                className="w-full rounded-md border border-gray-300 shadow-sm px-3 py-2 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">All Pools</option>
                {availablePools.map(p => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>
            
            {/* Height filter */}
            <div>
              <label htmlFor="height-filter" className="block text-sm font-medium text-gray-700 mb-1">Block Height</label>
              <select
                id="height-filter"
                value={height}
                onChange={handleHeightChange}
                className="w-full rounded-md border border-gray-300 shadow-sm px-3 py-2 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">All Heights</option>
                {availableHeights.map(h => (
                  <option key={h} value={h}>{h}</option>
                ))}
              </select>
            </div>
          </div>
          
          <div>
            <button 
              onClick={handleResetFilters}
              className="px-3 py-2 border border-gray-300 rounded text-sm hover:bg-gray-50"
            >
              Reset
            </button>
          </div>
          
          <div className="flex items-center ml-auto">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="show-matches"
                checked={showMatches}
                onChange={handleToggleMatches}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="show-matches" className="ml-2 block text-sm text-gray-700">
                Show Matches
              </label>
            </div>
          </div>
        </div>
      </div>
      
      {/* Notice when filters active */}
      {(source || pool || height) && (
        <div className="bg-blue-50 border border-blue-200 text-blue-700 px-4 py-3 rounded-lg flex items-center">
          <AlertCircle size={16} className="mr-2" />
          <span>
            Showing filtered results: 
            {source && <span className="font-medium"> Source: {source}</span>}
            {pool && <span className="font-medium"> Pool: {pool}</span>}
            {height && <span className="font-medium"> Height: {height}</span>}
          </span>
        </div>
      )}
      
      {/* Jobs table */}
      <JobsTable 
        jobs={prepareJobsData()} 
        isLoading={isLoading} 
        error={error}
        showMatches={showMatches}
      />
      
      {/* Pagination */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-500">
          Showing {jobs.length} of {pageSize * totalPages} jobs
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setPage(prev => Math.max(prev - 1, 1))}
            disabled={page === 1 || isLoading}
            className="px-3 py-2 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          
          <span className="px-3 py-2">
            Page {page} of {totalPages}
          </span>
          
          <button
            onClick={() => setPage(prev => Math.min(prev + 1, totalPages))}
            disabled={page === totalPages || isLoading}
            className="px-3 py-2 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
          
          <select
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setPage(1);
            }}
            className="px-3 py-2 border border-gray-300 rounded"
          >
            <option value={10}>10 per page</option>
            <option value={20}>20 per page</option>
            <option value={50}>50 per page</option>
            <option value={100}>100 per page</option>
          </select>
        </div>
      </div>
    </div>
  );
}

export default JobComparisonPage;
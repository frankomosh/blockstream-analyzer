import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Filter, ExternalLink, Clock } from 'lucide-react';

function JobsTable({ jobs, isLoading, error }) {
  const [sortField, setSortField] = useState('timestamp');
  const [sortDirection, setSortDirection] = useState('desc');
  const [expandedRows, setExpandedRows] = useState({});
  
  // Handle sort
  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };
  
  // Toggle row expansion
  const toggleRow = (id) => {
    setExpandedRows({
      ...expandedRows,
      [id]: !expandedRows[id]
    });
  };
  
  // Sort jobs
  const sortedJobs = [...jobs].sort((a, b) => {
    let aValue = a[sortField];
    let bValue = b[sortField];
    
    // Handle special cases
    if (sortField === 'timestamp') {
      aValue = new Date(aValue).getTime();
      bValue = new Date(bValue).getTime();
    } else if (sortField === 'mining_pool' || sortField === 'source') {
      aValue = aValue.toLowerCase();
      bValue = bValue.toLowerCase();
    }
    
    if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
    if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
    return 0;
  });
  
  // Format timestamp
  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };
  
  // Truncate hash
  const truncateHash = (hash, length = 8) => {
    if (!hash) return 'N/A';
    return `${hash.substring(0, length)}...${hash.substring(hash.length - length)}`;
  };

  if (isLoading) {
    return <div className="text-center py-4">Loading jobs...</div>;
  }
  
  if (error) {
    return <div className="text-center py-4 text-red-500">Error loading jobs: {error.message}</div>;
  }
  
  if (jobs.length === 0) {
    return <div className="text-center py-4">No jobs found.</div>;
  }

  return (
    <div className="overflow-x-auto rounded-lg shadow">
      <table className="min-w-full bg-white">
        <thead className="bg-gray-100">
          <tr>
            <th className="w-12 px-4 py-3"></th>
            <th className="px-4 py-3 text-left">
              <button
                className="flex items-center text-xs font-medium text-gray-500 uppercase tracking-wider"
                onClick={() => handleSort('job_id')}
              >
                Job ID
                {sortField === 'job_id' && (
                  sortDirection === 'asc' ? <ChevronUp size={16} /> : <ChevronDown size={16} />
                )}
              </button>
            </th>
            <th className="px-4 py-3 text-left">
              <button
                className="flex items-center text-xs font-medium text-gray-500 uppercase tracking-wider"
                onClick={() => handleSort('source')}
              >
                Source
                {sortField === 'source' && (
                  sortDirection === 'asc' ? <ChevronUp size={16} /> : <ChevronDown size={16} />
                )}
              </button>
            </th>
            <th className="px-4 py-3 text-left">
              <button
                className="flex items-center text-xs font-medium text-gray-500 uppercase tracking-wider"
                onClick={() => handleSort('mining_pool')}
              >
                Pool
                {sortField === 'mining_pool' && (
                  sortDirection === 'asc' ? <ChevronUp size={16} /> : <ChevronDown size={16} />
                )}
              </button>
            </th>
            <th className="px-4 py-3 text-left">
              <button
                className="flex items-center text-xs font-medium text-gray-500 uppercase tracking-wider"
                onClick={() => handleSort('height')}
              >
                Height
                {sortField === 'height' && (
                  sortDirection === 'asc' ? <ChevronUp size={16} /> : <ChevronDown size={16} />
                )}
              </button>
            </th>
            <th className="px-4 py-3 text-left">
              <button
                className="flex items-center text-xs font-medium text-gray-500 uppercase tracking-wider"
                onClick={() => handleSort('timestamp')}
              >
                Timestamp
                {sortField === 'timestamp' && (
                  sortDirection === 'asc' ? <ChevronUp size={16} /> : <ChevronDown size={16} />
                )}
              </button>
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Hash
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {sortedJobs.map((job) => (
            <React.Fragment key={`${job.source}-${job.job_id}`}>
              <tr 
                className={`hover:bg-gray-50 cursor-pointer ${expandedRows[`${job.source}-${job.job_id}`] ? 'bg-blue-50' : ''}`}
                onClick={() => toggleRow(`${job.source}-${job.job_id}`)}
              >
                <td className="px-4 py-3 text-center">
                  {expandedRows[`${job.source}-${job.job_id}`] ? 
                    <ChevronUp size={16} /> : 
                    <ChevronDown size={16} />
                  }
                </td>
                <td className="px-4 py-3 font-mono text-sm">{job.job_id}</td>
                <td className="px-4 py-3">
                  <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
                    {job.source.split('.')[0]}
                  </span>
                </td>
                <td className="px-4 py-3">{job.mining_pool}</td>
                <td className="px-4 py-3">{job.height}</td>
                <td className="px-4 py-3 text-sm">{formatTimestamp(job.timestamp)}</td>
                <td className="px-4 py-3 font-mono text-sm">{truncateHash(job.prev_block_hash)}</td>
              </tr>
              
              {expandedRows[`${job.source}-${job.job_id}`] && (
                <tr className="bg-gray-50">
                  <td colSpan="7" className="px-4 py-3">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <h4 className="font-medium mb-2">Job Details</h4>
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          <div className="text-gray-500">Version:</div>
                          <div>{job.version}</div>
                          <div className="text-gray-500">Bits:</div>
                          <div>{job.bits}</div>
                          <div className="text-gray-500">Time:</div>
                          <div>{job.time}</div>
                          <div className="text-gray-500">Clean Jobs:</div>
                          <div>{job.clean_jobs ? 'Yes' : 'No'}</div>
                          <div className="text-gray-500">Difficulty:</div>
                          <div>{job.difficulty}</div>
                        </div>
                      </div>
                      
                      <div>
                        <h4 className="font-medium mb-2">Technical Data</h4>
                        <div className="mb-2">
                          <div className="text-gray-500 text-sm">Previous Block Hash:</div>
                          <div className="font-mono text-sm break-all">{job.prev_block_hash}</div>
                        </div>
                        <div>
                          <div className="text-gray-500 text-sm">Coinbase Transaction:</div>
                          <div className="font-mono text-sm truncate">{job.coinbase_tx}</div>
                        </div>
                      </div>
                    </div>
                    
                    <div className="mt-4 border-t pt-2 flex justify-between items-center">
                      <div className="text-sm text-gray-500 flex items-center">
                        <Clock size={14} className="mr-1" />
                        Received at: {formatTimestamp(job.timestamp)}
                      </div>
                      <button className="text-sm text-blue-600 flex items-center">
                        View Full Details <ExternalLink size={14} className="ml-1" />
                      </button>
                    </div>
                  </td>
                </tr>
              )}
            </React.Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default JobsTable;
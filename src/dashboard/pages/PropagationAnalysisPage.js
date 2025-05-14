import React, { useState, useEffect } from 'react';
import { 
  ArrowRightCircle, 
  RefreshCw, 
  Clock, 
  Activity, 
  BarChart2, 
  Map,
  TrendingUp,
  TrendingDown
} from 'lucide-react';
import { endpoints } from '../utils/api';

// Import components
import PropagationTimeChart from '../components/PropagationTimeChart';
import StatsCard from '../components/StatsCard';

function PropagationAnalysisPage() {
  // State for propagation data
  const [propagationData, setPropagationData] = useState({});
  const [propagationStats, setPropagationStats] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // State for time range
  const [timeRange, setTimeRange] = useState(12);
  
  // Define service pairs
  const servicePairs = [
    'miningpool.observer-stratum.work',
    'miningpool.observer-mempool.space',
    'stratum.work-mempool.space'
  ];
  
  // Fetch data on mount and when time range changes
  useEffect(() => {
    fetchPropagationData();
  }, [timeRange]);
  
  // Fetch propagation data
  const fetchPropagationData = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Fetch propagation data for all service pairs
      const responses = await Promise.all(
        servicePairs.map(pair => endpoints.getPropagation(pair, timeRange))
      );
      
      // Process propagation data
      const dataMap = {};
      const statsMap = {};
      
      servicePairs.forEach((pair, index) => {
        const response = responses[index].data;
        dataMap[pair] = response.data || [];
        
        if (response.stats) {
          statsMap[pair] = response.stats;
        }
      });
      
      setPropagationData(dataMap);
      setPropagationStats(statsMap);
    } catch (err) {
      console.error('Error fetching propagation data:', err);
      setError(err);
    } finally {
      setIsLoading(false);
    }
  };
  
  // Calculate global stats
  const calculateGlobalStats = () => {
    if (Object.keys(propagationStats).length === 0) return { avg: 0, min: 0, max: 0 };
    
    const values = Object.values(propagationStats);
    
    const avgValues = values.map(s => s.mean).filter(v => !isNaN(v));
    const minValues = values.map(s => s.min).filter(v => !isNaN(v));
    const maxValues = values.map(s => s.max).filter(v => !isNaN(v));
    
    if (avgValues.length === 0) return { avg: 0, min: 0, max: 0 };
    
    return {
      avg: avgValues.reduce((sum, val) => sum + val, 0) / avgValues.length,
      min: Math.min(...minValues),
      max: Math.max(...maxValues)
    };
  };
  
  // Get fastest and slowest service pairs
  const getFastestAndSlowestPairs = () => {
    if (Object.keys(propagationStats).length === 0) {
      return { fastest: null, slowest: null };
    }
    
    let fastest = { pair: null, value: Infinity };
    let slowest = { pair: null, value: -Infinity };
    
    Object.entries(propagationStats).forEach(([pair, stats]) => {
      if (stats.mean < fastest.value) {
        fastest = { pair, value: stats.mean };
      }
      
      if (stats.mean > slowest.value) {
        slowest = { pair, value: stats.mean };
      }
    });
    
    return { fastest, slowest };
  };
  
  // Format service pair for display
  const formatServicePair = (pair) => {
    return pair.replace('-', ' → ').split('.').map(s => s.charAt(0).toUpperCase() + s.slice(1)).join('.');
  };
  
  const globalStats = calculateGlobalStats();
  const { fastest, slowest } = getFastestAndSlowestPairs();

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Propagation Analysis</h1>
        <div className="flex items-center space-x-2">
          <div className="text-sm text-gray-500">
            Time Range:
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(Number(e.target.value))}
              className="ml-2 px-2 py-1 border border-gray-300 rounded"
            >
              <option value={3}>3 hours</option>
              <option value={6}>6 hours</option>
              <option value={12}>12 hours</option>
              <option value={24}>24 hours</option>
              <option value={48}>48 hours</option>
            </select>
          </div>
          
          <button 
            onClick={fetchPropagationData} 
            disabled={isLoading}
            className="flex items-center px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            <RefreshCw size={16} className={`mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>
      
      {error && (
        <div className="bg-red-50 text-red-800 p-4 rounded-lg">
          Error loading propagation data: {error.message}
        </div>
      )}
      
      {/* Key metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard 
          title="Average Propagation Time" 
          value={`${globalStats.avg.toFixed(2)} ms`}
          icon={<Clock size={24} className="text-blue-500" />} 
          footer="Across all services"
          isLoading={isLoading}
        />
        <StatsCard 
          title="Fastest Propagation" 
          value={fastest ? `${fastest.value.toFixed(2)} ms` : 'N/A'}
          icon={<TrendingDown size={24} className="text-green-500" />} 
          footer={fastest ? `Between ${formatServicePair(fastest.pair)}` : 'No data'}
          isLoading={isLoading}
        />
        <StatsCard 
          title="Slowest Propagation" 
          value={slowest ? `${slowest.value.toFixed(2)} ms` : 'N/A'}
          icon={<TrendingUp size={24} className="text-red-500" />} 
          footer={slowest ? `Between ${formatServicePair(slowest.pair)}` : 'No data'}
          isLoading={isLoading}
        />
        <StatsCard 
          title="Service Pairs Analyzed" 
          value={servicePairs.length}
          icon={<Activity size={24} className="text-purple-500" />} 
          footer="Number of service comparisons"
          isLoading={isLoading}
        />
      </div>
      
      {/* Propagation time visualization */}
      <div className="bg-white rounded-lg shadow p-4">
        <h2 className="text-lg font-medium mb-4">Propagation Time Comparison</h2>
        
        <div className="mb-4 text-sm text-gray-500">
          This chart shows how quickly jobs propagate between different stratum monitoring services. 
          Lower values indicate faster propagation.
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {servicePairs.map(pair => (
            <div key={pair} className="flex flex-col">
              <div className="text-center mb-2 font-medium text-gray-700 flex items-center justify-center">
                <span>{pair.split('-')[0].split('.')[0]}</span>
                <ArrowRightCircle size={18} className="mx-2 text-blue-500" />
                <span>{pair.split('-')[1].split('.')[0]}</span>
              </div>
              
              <PropagationTimeChart 
                servicePair={pair} 
                data={propagationData[pair] || []} 
                isLoading={isLoading}
                error={error}
              />
            </div>
          ))}
        </div>
      </div>
      
      {/* Detailed statistics */}
      <div className="bg-white rounded-lg shadow p-4">
        <h2 className="text-lg font-medium mb-4">Detailed Statistics</h2>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Service Pair
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Mean
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Median
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Min
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Max
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Standard Deviation
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Samples
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {isLoading ? (
                <tr>
                  <td colSpan="7" className="px-6 py-4 text-center">Loading statistics...</td>
                </tr>
              ) : Object.keys(propagationStats).length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-6 py-4 text-center">No statistics available</td>
                </tr>
              ) : (
                Object.entries(propagationStats).map(([pair, stats]) => (
                  <tr key={pair}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {formatServicePair(pair)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {stats.mean.toFixed(2)} ms
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {stats.median.toFixed(2)} ms
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {stats.min.toFixed(2)} ms
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {stats.max.toFixed(2)} ms
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {stats.stddev?.toFixed(2) || 'N/A'} ms
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {stats.sample_count}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
      
      {/* Analysis notes */}
      <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
        <h3 className="text-lg font-medium text-blue-800 mb-2">Analysis Notes</h3>
        <ul className="list-disc list-inside text-blue-700 space-y-2">
          <li>Propagation time measures how long it takes for the same job to appear on different services.</li>
          <li>Lower propagation times indicate better synchronization between services.</li>
          <li>Regional differences can significantly impact propagation times.</li>
          <li>High standard deviation suggests inconsistent connectivity between services.</li>
          <li>The fastest service pair typically has the closest geographic proximity or network connectivity.</li>
        </ul>
      </div>
    </div>
  );
}

export default PropagationAnalysisPage;
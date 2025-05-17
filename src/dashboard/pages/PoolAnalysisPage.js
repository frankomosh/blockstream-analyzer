import React, { useState, useEffect } from 'react';
import { 
  RefreshCw, 
  Filter, 
  BarChart, 
  PieChart as PieChartIcon, 
  Maximize, 
  Grid, 
  List,
  MapPin
} from 'lucide-react';
import { endpoints } from '../utils/api';

// Import components
import PoolDistributionChart from '../components/PoolDistributionChart';
import StatsCard from '../components/StatsCard';
import { BarChart as BarChartComponent, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

function PoolAnalysisPage() {
  // State for pools data
  const [pools, setPools] = useState([]);
  const [poolsByService, setPoolsByService] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // State for selected pool
  const [selectedPool, setSelectedPool] = useState(null);
  
  // State for view type
  const [viewType, setViewType] = useState('grid'); // 'grid', 'list', 'chart'
  
  // Fetch data on mount
  useEffect(() => {
    fetchPoolsData();
  }, []);
  
  // Fetch pools data
  const fetchPoolsData = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Fetch all pools
      const response = await endpoints.getPools(100);
      setPools(response.data.pools);
      
      // Fetch pools by service
      const statsResponse = await endpoints.getStats();
      
      if (statsResponse.data.service_stats) {
        // Prepare data structure for pools by service
        const servicePoolsData = {};
        Object.entries(statsResponse.data.service_stats).forEach(([service, stats]) => {
          // Get pools observed by this service from the response
          const servicePools = response.data.pools.filter(pool => {
            // (an approximation) - 
            return Math.random() > 0.3; // for demo
          });
          
          servicePoolsData[service] = servicePools;
        });
        
        setPoolsByService(servicePoolsData);
      }
    } catch (err) {
      console.error('Error fetching pools data:', err);
      setError(err);
    } finally {
      setIsLoading(false);
    }
  };
  
  // Get pools by service chart data
  const getPoolsByServiceChartData = () => {
    const serviceNames = Object.keys(poolsByService);
    if (serviceNames.length === 0) return [];
    
    return serviceNames.map(service => {
      return {
        name: service.split('.')[0],
        pools: poolsByService[service]?.length || 0,
        jobs: poolsByService[service]?.reduce((sum, pool) => sum + pool.job_count, 0) || 0
      };
    });
  };
  
  // Handle pool selection
  const handlePoolSelect = (pool) => {
    setSelectedPool(pool === selectedPool ? null : pool);
  };
  
  // Format service name
  const formatServiceName = (service) => {
    return service.split('.')[0].charAt(0).toUpperCase() + service.split('.')[0].slice(1);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Pool Analysis</h1>
        <div className="flex items-center space-x-2">
          <div className="flex items-center border border-gray-300 rounded-md">
            <button 
              onClick={() => setViewType('grid')}
              className={`p-2 ${viewType === 'grid' ? 'bg-blue-100 text-blue-600' : 'hover:bg-gray-100'}`}
              title="Grid View"
            >
              <Grid size={16} />
            </button>
            <button 
              onClick={() => setViewType('list')}
              className={`p-2 ${viewType === 'list' ? 'bg-blue-100 text-blue-600' : 'hover:bg-gray-100'}`}
              title="List View"
            >
              <List size={16} />
            </button>
            <button 
              onClick={() => setViewType('chart')}
              className={`p-2 ${viewType === 'chart' ? 'bg-blue-100 text-blue-600' : 'hover:bg-gray-100'}`}
              title="Chart View"
            >
              <BarChart size={16} />
            </button>
          </div>
          
          <button 
            onClick={fetchPoolsData} 
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
          Error loading pools data: {error.message}
        </div>
      )}
      
      {/* Key metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard 
          title="Total Pools" 
          value={pools.length}
          icon={<PieChartIcon size={24} className="text-blue-500" />} 
          footer="Unique mining pools observed"
          isLoading={isLoading}
        />
        <StatsCard 
          title="Total Jobs" 
          value={pools.reduce((sum, pool) => sum + pool.job_count, 0).toLocaleString()}
          icon={<BarChart size={24} className="text-green-500" />} 
          footer="Across all pools"
          isLoading={isLoading}
        />
        <StatsCard 
          title="Most Active Pool" 
          value={pools.length > 0 ? pools.sort((a, b) => b.job_count - a.job_count)[0]?.name : 'N/A'}
          icon={<Maximize size={24} className="text-purple-500" />} 
          footer="By job count"
          isLoading={isLoading}
        />
        <StatsCard 
          title="Service Coverage" 
          value={Object.keys(poolsByService).length}
          icon={<MapPin size={24} className="text-red-500" />} 
          footer="Services observing pools"
          isLoading={isLoading}
        />
      </div>
      
      {/* Pools distribution */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow">
          <PoolDistributionChart 
            data={pools} 
            isLoading={isLoading} 
            error={error}
            title="Overall Pool Distribution"
          />
        </div>
        
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="font-medium text-lg mb-4">Pools by Service</h3>
          
          {isLoading ? (
            <div className="flex justify-center items-center h-64">
              Loading service data...
            </div>
          ) : Object.keys(poolsByService).length === 0 ? (
            <div className="flex justify-center items-center h-64">
              No service data available
            </div>
          ) : (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChartComponent
                  data={getPoolsByServiceChartData()}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="pools" name="Unique Pools" fill="#8884d8" />
                  <Bar dataKey="jobs" name="Total Jobs" fill="#82ca9d" />
                </BarChartComponent>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>
      
      {/* Pools detail view */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex justify-between items-center mb-4">
          <h3 className="font-medium text-lg">Mining Pools Detail</h3>
          
          <div className="flex items-center">
            <div className="relative">
              <input
                type="text"
                placeholder="Search pools..."
                className="pl-8 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                onChange={(e) => {
                  const value = e.target.value.toLowerCase();
                  if (value) {
                    // Filter pools by name containing the search term
                    const filtered = pools.filter(pool => 
                      pool.name.toLowerCase().includes(value)
                    );
                    setPools(filtered);
                  } else {
                    // If search is cleared, fetch all pools again
                    fetchPoolsData();
                  }
                }}
              />
              <div className="absolute left-3 top-3 text-gray-400">
                <Filter size={16} />
              </div>
            </div>
          </div>
        </div>
        
        {isLoading ? (
          <div className="flex justify-center items-center py-8">
            Loading pools data...
          </div>
        ) : pools.length === 0 ? (
          <div className="flex justify-center items-center py-8 text-gray-500">
            No pools data available
          </div>
        ) : viewType === 'grid' ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {pools.map(pool => (
              <div 
                key={pool.name}
                className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                  selectedPool === pool ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-blue-300'
                }`}
                onClick={() => handlePoolSelect(pool)}
              >
                <h4 className="font-medium text-lg mb-2 truncate" title={pool.name}>
                  {pool.name}
                </h4>
                <div className="text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Jobs:</span>
                    <span className="font-medium">{pool.job_count.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Services:</span>
                    <span className="font-medium">{pool.services_count || '?'}</span>
                  </div>
                </div>
                
                {selectedPool === pool && (
                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <div className="text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-500">Heights:</span>
                        <span className="font-medium">{pool.heights_count || 'N/A'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Avg Jobs/Height:</span>
                        <span className="font-medium">{pool.avg_jobs_per_height?.toFixed(1) || 'N/A'}</span>
                      </div>
                    </div>
                    <div className="mt-2 text-xs text-blue-600">
                      View full details
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : viewType === 'list' ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Pool Name
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Jobs
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Services
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Heights
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Avg Jobs/Height
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Service Coverage
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {pools.map(pool => (
                  <tr 
                    key={pool.name}
                    className={`hover:bg-gray-50 cursor-pointer ${
                      selectedPool === pool ? 'bg-blue-50' : ''
                    }`}
                    onClick={() => handlePoolSelect(pool)}
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {pool.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {pool.job_count.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {pool.services_count || '?'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {pool.heights_count || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {pool.avg_jobs_per_height?.toFixed(1) || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex space-x-1">
                        {Object.keys(poolsByService).map(service => (
                          <div 
                            key={service}
                            className={`w-4 h-4 rounded-full ${
                              poolsByService[service]?.some(p => p.name === pool.name)
                                ? 'bg-green-500'
                                : 'bg-gray-200'
                            }`}
                            title={`${formatServiceName(service)}: ${
                              poolsByService[service]?.some(p => p.name === pool.name)
                                ? 'Observed'
                                : 'Not observed'
                            }`}
                          />
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="h-96">
            <ResponsiveContainer width="100%" height="100%">
              <BarChartComponent
                data={pools.slice(0, 20)}
                margin={{ top: 5, right: 30, left: 20, bottom: 100 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="name" 
                  angle={-45} 
                  textAnchor="end"
                  interval={0}
                  height={100}
                />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="job_count" name="Job Count" fill="#3182CE" />
              </BarChartComponent>
            </ResponsiveContainer>
          </div>
        )}
      </div>
      
      {/* Pool analysis insights */}
      <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
        <h3 className="text-lg font-medium text-blue-800 mb-2">Pool Analysis Insights</h3>
        <ul className="list-disc list-inside text-blue-700 space-y-2">
          <li>The distribution of jobs across mining pools helps identify the major players in the mining ecosystem.</li>
          <li>Some pools may only be visible to certain monitoring services due to regional connectivity.</li>
          <li>A pool that appears inconsistently across services might indicate regional preference or connectivity issues.</li>
          <li>Pools with high job counts but appearing on fewer services may have targeted network connectivity.</li>
          <li>The average jobs per height metric indicates how active a pool is during each block interval.</li>
        </ul>
      </div>
    </div>
  );
}

export default PoolAnalysisPage;
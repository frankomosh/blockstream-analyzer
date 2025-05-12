import React, { useState, useEffect } from 'react';
import { BarChart2, Cpu, Clock, Layers, RefreshCw } from 'lucide-react';
import { endpoints } from '../utils/api';

// Import components
import ServiceStatusCard from '../components/ServiceStatusCard';
import StatsCard from '../components/StatsCard';
import PropagationTimeChart from '../components/PropagationTimeChart';
import PoolDistributionChart from '../components/PoolDistributionChart';

function OverviewPage() {
  const [stats, setStats] = useState(null);
  const [clientStatus, setClientStatus] = useState([]);
  const [propagationData, setPropagationData] = useState({});
  const [topPools, setTopPools] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  // Fetch data
  useEffect(() => {
    fetchData();
    // Refresh data every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Fetch all data in parallel
      const [statsResponse, clientsResponse, poolsResponse] = await Promise.all([
        endpoints.getStats(),
        endpoints.getClients(),
        endpoints.getPools(10)
      ]);
      
      setStats(statsResponse.data);
      setClientStatus(clientsResponse.data.clients);
      setTopPools(poolsResponse.data.pools);
      
      // Fetch propagation data for main service pairs
      const servicePairs = [
        'miningpool.observer-stratum.work',
        'miningpool.observer-mempool.space',
        'stratum.work-mempool.space'
      ];
      
      const propagationResponses = await Promise.all(
        servicePairs.map(pair => endpoints.getPropagation(pair, 6))
      );
      
      const propagationDataMap = {};
      servicePairs.forEach((pair, index) => {
        propagationDataMap[pair] = propagationResponses[index].data.data;
      });
      
      setPropagationData(propagationDataMap);
      setLastUpdate(new Date());
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError(err);
    } finally {
      setIsLoading(false);
    }
  };

  // Format the last update time
  const formatLastUpdate = () => {
    if (!lastUpdate) return 'Never';
    return lastUpdate.toLocaleTimeString();
  };

  // Calculate the total job count
  const getTotalJobCount = () => {
    if (!stats || !stats.job_counts) return 0;
    return stats.job_counts.total || 0;
  };

  // Get the current block height
  const getCurrentHeight = () => {
    if (!stats || !stats.latest_heights || stats.latest_heights.length === 0) return 'N/A';
    return stats.latest_heights[0].height;
  };

  // Get services agreement rate
  const getAgreementRate = () => {
    if (!stats || !stats.agreement_stats || !stats.agreement_stats.agreement_rates) return 'N/A';
    
    // Calculate average agreement rate
    const rates = Object.values(stats.agreement_stats.agreement_rates);
    if (rates.length === 0) return 'N/A';
    
    const avgRate = rates.reduce((sum, rate) => sum + rate, 0) / rates.length;
    return `${(avgRate * 100).toFixed(1)}%`;
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Overview Dashboard</h1>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-500">Last updated: {formatLastUpdate()}</span>
          <button 
            onClick={fetchData} 
            disabled={isLoading}
            className="p-2 rounded-full hover:bg-gray-100"
          >
            <RefreshCw size={16} className={isLoading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 text-red-800 p-4 rounded-lg">
          Error loading dashboard data: {error.message}
        </div>
      )}

      {/* Key metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard 
          title="Total Jobs" 
          value={getTotalJobCount().toLocaleString()} 
          icon={<Layers size={24} className="text-blue-500" />} 
          footer="Across all stratum monitoring services"
          isLoading={isLoading}
        />
        <StatsCard 
          title="Current Block Height" 
          value={getCurrentHeight()} 
          icon={<Cpu size={24} className="text-green-500" />} 
          footer="Latest observed block height"
          isLoading={isLoading}
        />
        <StatsCard 
          title="Service Agreement" 
          value={getAgreementRate()} 
          icon={<BarChart2 size={24} className="text-orange-500" />} 
          footer="Average agreement between services"
          isLoading={isLoading}
        />
        <StatsCard 
          title="Active Pools" 
          value={topPools.length} 
          icon={<Clock size={24} className="text-purple-500" />} 
          footer="Unique mining pools observed"
          isLoading={isLoading}
        />
      </div>

      {/* Service status cards */}
      <div>
        <h2 className="text-lg font-medium mb-3">Service Status</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {clientStatus.map(client => (
            <ServiceStatusCard key={client.service} service={client} />
          ))}
        </div>
      </div>

      {/* Propagation time charts */}
      <div>
        <h2 className="text-lg font-medium mb-3">Propagation Time</h2>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {Object.entries(propagationData).map(([servicePair, data]) => (
            <PropagationTimeChart 
              key={servicePair} 
              servicePair={servicePair} 
              data={data} 
              isLoading={isLoading}
              error={error}
            />
          ))}
        </div>
      </div>

      {/* Pool distribution and latest block height */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <PoolDistributionChart 
          data={topPools} 
          isLoading={isLoading} 
          error={error}
          title="Mining Pool Distribution"
        />
        
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="font-medium text-lg mb-4">Latest Block Heights</h3>
          {isLoading ? (
            <div className="animate-pulse space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="flex items-center">
                  <div className="h-5 bg-gray-200 rounded w-1/6 mr-2"></div>
                  <div className="h-5 bg-gray-200 rounded w-1/2"></div>
                </div>
              ))}
            </div>
          ) : stats && stats.latest_heights ? (
            <div className="space-y-3">
              {stats.latest_heights.slice(0, 5).map(height => (
                <div key={height.height} className="flex items-center">
                  <div className="bg-blue-100 text-blue-800 px-2 py-1 rounded-md text-sm w-16 text-center mr-2">
                    {height.height}
                  </div>
                  <div>
                    <div className="text-sm">
                      {new Date(height.first_seen).toLocaleString()}
                    </div>
                    <div className="text-xs text-gray-500">
                      {height.services_count} services • {height.pools_count} pools • {height.job_count} jobs
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">No height data available</div>
          )}
        </div>
      </div>
    </div>
  );
}

export default OverviewPage;
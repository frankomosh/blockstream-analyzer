import React, { useState, useEffect } from 'react';
import { Bell, RefreshCw } from 'lucide-react';
import api from '../utils/api';

function Header() {
  const [lastUpdate, setLastUpdate] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [serviceStatus, setServiceStatus] = useState({
    'miningpool.observer': 'inactive',
    'stratum.work': 'inactive',
    'mempool.space': 'inactive'
  });

  // Fetch service status on mount and every 30 seconds
  useEffect(() => {
    fetchServiceStatus();
    const interval = setInterval(fetchServiceStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchServiceStatus = async () => {
    try {
      const response = await api.get('/api/clients');
      const statusMap = {};
      
      response.data.clients.forEach(client => {
        statusMap[client.service] = client.status;
      });
      
      setServiceStatus(statusMap);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Error fetching service status:', error);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await fetchServiceStatus();
    setIsRefreshing(false);
  };

  return (
    <header className="bg-white shadow-md px-6 py-3 flex justify-between items-center">
      <div className="flex items-center space-x-4">
        <h2 className="text-lg font-semibold">Stratum Monitor Dashboard</h2>
        <div className="flex space-x-2">
          {Object.entries(serviceStatus).map(([service, status]) => (
            <div key={service} className="flex items-center">
              <div 
                className={`w-3 h-3 rounded-full mr-1 ${status === 'active' ? 'bg-green-500' : 'bg-red-500'}`} 
              />
              <span className="text-xs">{service.split('.')[0]}</span>
            </div>
          ))}
        </div>
      </div>
      
      <div className="flex items-center space-x-4">
        <div className="text-sm text-gray-500">
          {lastUpdate ? `Last updated: ${lastUpdate.toLocaleTimeString()}` : 'Updating...'}
        </div>
        
        <button 
          onClick={handleRefresh} 
          disabled={isRefreshing}
          className="p-2 rounded-full hover:bg-gray-100"
        >
          <RefreshCw size={18} className={isRefreshing ? 'animate-spin' : ''} />
        </button>
        
        <button className="p-2 rounded-full hover:bg-gray-100 relative">
          <Bell size={18} />
          <span className="absolute top-0 right-0 w-2 h-2 bg-red-500 rounded-full"></span>
        </button>
      </div>
    </header>
  );
}

export default Header;
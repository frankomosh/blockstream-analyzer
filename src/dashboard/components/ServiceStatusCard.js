import React from 'react';
import { Clock, BarChart2, Server } from 'lucide-react';

function ServiceStatusCard({ service }) {
  const { name, status, jobsReceived, poolsObserved, lastActivity } = service;
  
  // Format the service name
  const displayName = name.split('.')[0].charAt(0).toUpperCase() + name.split('.')[0].slice(1);
  
  // Format the last activity time
  const formatLastActivity = () => {
    if (!lastActivity) return 'N/A';
    
    const lastActivityDate = new Date(lastActivity * 1000); // Convert from Unix timestamp
    const now = new Date();
    const diffSeconds = Math.floor((now - lastActivityDate) / 1000);
    
    if (diffSeconds < 60) return `${diffSeconds}s ago`;
    if (diffSeconds < 3600) return `${Math.floor(diffSeconds / 60)}m ago`;
    if (diffSeconds < 86400) return `${Math.floor(diffSeconds / 3600)}h ago`;
    return `${Math.floor(diffSeconds / 86400)}d ago`;
  };
  
  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <Server className="mr-2 text-blue-500" size={20} />
          <h3 className="font-medium text-lg">{displayName}</h3>
        </div>
        <div className="flex items-center">
          <div className={`w-3 h-3 rounded-full mr-2 ${status === 'active' ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-sm">{status === 'active' ? 'Active' : 'Inactive'}</span>
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <div className="flex items-center">
          <BarChart2 className="mr-2 text-gray-400" size={16} />
          <div>
            <div className="text-sm text-gray-500">Jobs Received</div>
            <div className="font-semibold">{jobsReceived.toLocaleString()}</div>
          </div>
        </div>
        
        <div className="flex items-center">
          <BarChart2 className="mr-2 text-gray-400" size={16} />
          <div>
            <div className="text-sm text-gray-500">Pools Observed</div>
            <div className="font-semibold">{poolsObserved}</div>
          </div>
        </div>
      </div>
      
      <div className="mt-4 flex items-center">
        <Clock className="mr-2 text-gray-400" size={16} />
        <div className="text-sm text-gray-500">Last Activity: <span className="font-medium">{formatLastActivity()}</span></div>
      </div>
    </div>
  );
}

export default ServiceStatusCard;
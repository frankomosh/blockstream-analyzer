import React from 'react';

function StatsCard({ title, value, icon, change, changeType = 'neutral', footer, isLoading = false }) {
  // Determine the change color based on type
  const getChangeColor = () => {
    if (changeType === 'positive') return 'text-green-500';
    if (changeType === 'negative') return 'text-red-500';
    return 'text-gray-500';
  };
  
  // Get the change icon
  const getChangeIcon = () => {
    if (changeType === 'positive') return '↑';
    if (changeType === 'negative') return '↓';
    return '•';
  };
  
  // Handle loading state
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-4 min-h-[120px]">
        <div className="animate-pulse">
          <div className="h-5 bg-gray-200 rounded w-1/2 mb-4"></div>
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="text-sm font-medium text-gray-500">{title}</h3>
          <div className="mt-1 text-2xl font-semibold">{value}</div>
          
          {change && (
            <div className={`mt-1 text-sm ${getChangeColor()}`}>
              <span className="mr-1">{getChangeIcon()}</span>
              {change}
            </div>
          )}
        </div>
        
        {icon && (
          <div className="p-2 bg-blue-50 rounded-lg">
            {icon}
          </div>
        )}
      </div>
      
      {footer && (
        <div className="mt-4 pt-3 border-t border-gray-100 text-sm text-gray-500">
          {footer}
        </div>
      )}
    </div>
  );
}

export default StatsCard;
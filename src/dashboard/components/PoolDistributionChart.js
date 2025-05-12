import React, { useState } from 'react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend
} from 'recharts';

function PoolDistributionChart({ data, isLoading, error, title = "Pool Distribution" }) {
  const [activeIndex, setActiveIndex] = useState(null);
  
  // Generate colors for the pie chart
  const COLORS = [
    '#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#A28DF8',
    '#19A7CE', '#FF6B6B', '#4ECDC4', '#FF9F1C', '#F2CC8F',
    '#AACFCF', '#679B9B', '#637373', '#A5D8DD', '#D64161'
  ];
  
  // Format data for the pie chart
  const formatData = () => {
    if (!data) return [];
    
    // Sort by job count descending
    const sortedData = [...data].sort((a, b) => b.job_count - a.job_count);
    
    // Take top 10 pools and group others
    if (sortedData.length > 10) {
      const topPools = sortedData.slice(0, 9);
      const otherPools = sortedData.slice(9);
      
      const otherCount = otherPools.reduce((sum, pool) => sum + pool.job_count, 0);
      
      return [
        ...topPools,
        { name: 'Other Pools', job_count: otherCount }
      ];
    }
    
    return sortedData;
  };
  
  const formattedData = formatData();
  
  // Custom tooltip
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white shadow-md rounded p-3 border border-gray-200">
          <p className="font-medium">{data.name}</p>
          <p className="text-sm">
            <span className="text-gray-500">Jobs:</span> {data.job_count.toLocaleString()}
          </p>
          <p className="text-sm">
            <span className="text-gray-500">Share:</span> {(data.job_count / totalJobs * 100).toFixed(1)}%
          </p>
        </div>
      );
    }
    return null;
  };
  
  // Handle mouse events
  const handleMouseEnter = (_, index) => {
    setActiveIndex(index);
  };
  
  const handleMouseLeave = () => {
    setActiveIndex(null);
  };
  
  // Calculate total jobs
  const totalJobs = formattedData.reduce((sum, item) => sum + item.job_count, 0);

  if (isLoading) {
    return <div className="flex justify-center items-center h-64 bg-white rounded-lg shadow">Loading pool data...</div>;
  }
  
  if (error) {
    return <div className="flex justify-center items-center h-64 bg-white rounded-lg shadow text-red-500">Error loading pool data: {error.message}</div>;
  }
  
  if (!data || data.length === 0) {
    return <div className="flex justify-center items-center h-64 bg-white rounded-lg shadow">No pool data available.</div>;
  }

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="font-medium text-lg mb-4">{title}</h3>
      
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={formattedData}
              dataKey="job_count"
              nameKey="name"
              cx="50%"
              cy="50%"
              outerRadius={80}
              innerRadius={55}
              onMouseEnter={handleMouseEnter}
              onMouseLeave={handleMouseLeave}
              paddingAngle={2}
            >
              {formattedData.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={COLORS[index % COLORS.length]} 
                  opacity={activeIndex === null || activeIndex === index ? 1 : 0.6}
                  stroke="#fff"
                  strokeWidth={1}
                />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend 
              layout="vertical" 
              align="right" 
              verticalAlign="middle"
              formatter={(value, entry, index) => {
                // Format the legend text to include percentage
                const item = formattedData[index];
                return <span className="text-sm">{value} ({(item.job_count / totalJobs * 100).toFixed(1)}%)</span>;
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
      
      <div className="mt-2 text-center text-sm text-gray-500">
        Total Jobs: {totalJobs.toLocaleString()} | Unique Pools: {data.length}
      </div>
    </div>
  );
}

export default PoolDistributionChart;
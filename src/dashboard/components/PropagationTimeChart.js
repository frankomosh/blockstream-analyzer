import React, { useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceArea
} from 'recharts';

function PropagationTimeChart({ data, servicePair, isLoading, error }) {
  const [hoveredArea, setHoveredArea] = useState(null);
  
  // Format the timestamp for display
  const formatXAxis = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };
  
  // Format the tooltip label
  const formatTooltipLabel = (label) => {
    const date = new Date(label);
    return date.toLocaleString();
  };
  
  // Calculate statistics
  const calculateStats = () => {
    if (!data || data.length === 0) return { avg: 0, min: 0, max: 0 };
    
    const values = data.map(item => item.value);
    const sum = values.reduce((a, b) => a + b, 0);
    
    return {
      avg: sum / values.length,
      min: Math.min(...values),
      max: Math.max(...values)
    };
  };
  
  const stats = calculateStats();
  
  // Define color themes for different service pairs
  const getLineColor = () => {
    const colorMap = {
      'miningpool.observer-stratum.work': '#4299e1', // blue
      'miningpool.observer-mempool.space': '#48bb78', // green
      'stratum.work-mempool.space': '#ed8936', // orange
      'default': '#805ad5' // purple
    };
    
    return colorMap[servicePair] || colorMap.default;
  };
  
  // Handle mouse events for reference areas
  const handleMouseEnter = (area) => {
    setHoveredArea(area);
  };
  
  const handleMouseLeave = () => {
    setHoveredArea(null);
  };

  if (isLoading) {
    return <div className="flex justify-center items-center h-64 bg-white rounded-lg shadow">Loading propagation data...</div>;
  }
  
  if (error) {
    return <div className="flex justify-center items-center h-64 bg-white rounded-lg shadow text-red-500">Error loading propagation data: {error.message}</div>;
  }
  
  if (!data || data.length === 0) {
    return <div className="flex justify-center items-center h-64 bg-white rounded-lg shadow">No propagation data available.</div>;
  }

  const lineColor = getLineColor();

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-medium text-lg">{servicePair.replace('-', ' → ')}</h3>
        <div className="flex space-x-4 text-sm">
          <div>
            <span className="text-gray-500">Avg:</span>{' '}
            <span className="font-medium">{stats.avg.toFixed(2)}ms</span>
          </div>
          <div>
            <span className="text-gray-500">Min:</span>{' '}
            <span className="font-medium">{stats.min.toFixed(2)}ms</span>
          </div>
          <div>
            <span className="text-gray-500">Max:</span>{' '}
            <span className="font-medium">{stats.max.toFixed(2)}ms</span>
          </div>
        </div>
      </div>
      
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={data}
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="timestamp" 
              tickFormatter={formatXAxis} 
              minTickGap={50}
            />
            <YAxis 
              label={{ value: 'ms', angle: -90, position: 'insideLeft' }} 
              domain={['dataMin', 'dataMax']}
            />
            <Tooltip 
              formatter={(value) => [`${value.toFixed(2)}ms`, 'Propagation Time']}
              labelFormatter={formatTooltipLabel}
            />
            <Legend />
            
            {/* Reference areas for statistics */}
            <ReferenceArea 
              y1={stats.min} y2={stats.min} 
              stroke="red" strokeOpacity={hoveredArea === 'min' ? 0.8 : 0.3} 
              onMouseEnter={() => handleMouseEnter('min')}
              onMouseLeave={handleMouseLeave}
              label={hoveredArea === 'min' ? `Min: ${stats.min.toFixed(2)}ms` : ''}
            />
            <ReferenceArea 
              y1={stats.avg} y2={stats.avg} 
              stroke="green" strokeOpacity={hoveredArea === 'avg' ? 0.8 : 0.3} 
              onMouseEnter={() => handleMouseEnter('avg')}
              onMouseLeave={handleMouseLeave}
              label={hoveredArea === 'avg' ? `Avg: ${stats.avg.toFixed(2)}ms` : ''}
            />
            <ReferenceArea 
              y1={stats.max} y2={stats.max} 
              stroke="blue" strokeOpacity={hoveredArea === 'max' ? 0.8 : 0.3} 
              onMouseEnter={() => handleMouseEnter('max')}
              onMouseLeave={handleMouseLeave} 
              label={hoveredArea === 'max' ? `Max: ${stats.max.toFixed(2)}ms` : ''}
            />
            
            <Line 
              type="monotone" 
              dataKey="value" 
              name="Propagation Time" 
              stroke={lineColor} 
              strokeWidth={2} 
              dot={{ r: 2 }}
              activeDot={{ r: 6 }}
              animationDuration={500}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default PropagationTimeChart;
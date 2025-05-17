import React, { useState, useEffect } from 'react';
import { Save, RefreshCw, AlertTriangle, Check, X, Moon, Sun, Database } from 'lucide-react';
import { endpoints } from '../utils/api';

function SettingsPage() {
  // Settings state
  const [settings, setSettings] = useState({
    // Dashboard settings
    theme: 'light',
    refreshInterval: 30,
    dataRetentionDays: 7,
    
    // Service settings
    services: {
      'miningpool.observer': {
        enabled: true,
        url: 'wss://stratum.miningpool.observer/ws',
        region: 'global'
      },
      'stratum.work': {
        enabled: true,
        url: 'wss://stratum.work/ws',
        region: 'eu'
      },
      'mempool.space': {
        enabled: true,
        url: 'wss://mempool.space/stratum/ws',
        region: 'global'
      }
    },
    
    // Analysis settings
    analysis: {
      jobMatchingThreshold: 10,
      timeWindow: 300,
      propagationAnalysisEnabled: true,
      regionAnalysisEnabled: true
    }
  });
  
  // UI state
  const [isLoading, setIsLoading] = useState(false);
  const [saveStatus, setSaveStatus] = useState(null); // 'success', 'error', null
  const [isDarkMode, setIsDarkMode] = useState(false);
  
  // Load settings on mount
  useEffect(() => {
    loadSettings();
    
    // Check for dark mode preference
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    setIsDarkMode(prefersDark);
  }, []);
  
  // Apply dark mode when it changes
  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDarkMode]);
  
  // Load settings
  const loadSettings = async () => {
    // In a real app, this would load from an API or local storage
    // For this demo, we'll just use the default settings
    setIsLoading(true);
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // In a real implementation, you would fetch settings from your API
      // const response = await fetch('/api/settings');
      // const data = await response.json();
      // setSettings(data);
      
      setIsLoading(false);
    } catch (error) {
      console.error('Error loading settings:', error);
      setIsLoading(false);
    }
  };
  
  // Save settings
  const saveSettings = async () => {
    setIsLoading(true);
    setSaveStatus(null);
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 800));
      
      // (save settings to API)
      // await fetch('/api/settings', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(settings)
      // });
      
      // Save theme preference to local storage
      localStorage.setItem('theme', settings.theme);
      
      setIsLoading(false);
      setSaveStatus('success');
      
      // Clear success message after 3 seconds
      setTimeout(() => setSaveStatus(null), 3000);
    } catch (error) {
      console.error('Error saving settings:', error);
      setIsLoading(false);
      setSaveStatus('error');
    }
  };
  
  // Toggle dark mode
  const toggleDarkMode = () => {
    const newMode = !isDarkMode;
    setIsDarkMode(newMode);
    setSettings({
      ...settings,
      theme: newMode ? 'dark' : 'light'
    });
  };
  
  // Handle service toggle
  const handleServiceToggle = (service) => {
    setSettings({
      ...settings,
      services: {
        ...settings.services,
        [service]: {
          ...settings.services[service],
          enabled: !settings.services[service].enabled
        }
      }
    });
  };
  
  // Handle service URL change
  const handleServiceUrlChange = (service, url) => {
    setSettings({
      ...settings,
      services: {
        ...settings.services,
        [service]: {
          ...settings.services[service],
          url
        }
      }
    });
  };
  
  // Handle service region change
  const handleServiceRegionChange = (service, region) => {
    setSettings({
      ...settings,
      services: {
        ...settings.services,
        [service]: {
          ...settings.services[service],
          region
        }
      }
    });
  };
  
  // Handle refresh interval change
  const handleRefreshIntervalChange = (value) => {
    setSettings({
      ...settings,
      refreshInterval: parseInt(value, 10)
    });
  };
  
  // Handle data retention change
  const handleDataRetentionChange = (value) => {
    setSettings({
      ...settings,
      dataRetentionDays: parseInt(value, 10)
    });
  };
  
  // Handle job matching threshold change
  const handleJobMatchingThresholdChange = (value) => {
    setSettings({
      ...settings,
      analysis: {
        ...settings.analysis,
        jobMatchingThreshold: parseInt(value, 10)
      }
    });
  };
  
  // Handle time window change
  const handleTimeWindowChange = (value) => {
    setSettings({
      ...settings,
      analysis: {
        ...settings.analysis,
        timeWindow: parseInt(value, 10)
      }
    });
  };
  
  // Handle analysis toggle
  const handleAnalysisToggle = (analysis) => {
    setSettings({
      ...settings,
      analysis: {
        ...settings.analysis,
        [analysis]: !settings.analysis[analysis]
      }
    });
  };
  
  // Execute database maintenance
  const handleDatabaseMaintenance = async () => {
    if (window.confirm('Are you sure you want to run database maintenance? This will clean up old data according to your retention settings.')) {
      setIsLoading(true);
      
      try {
        // In a real implementation, you would call your API
        // await fetch('/api/maintenance', { method: 'POST' });
        
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        alert('Database maintenance completed successfully');
        setIsLoading(false);
      } catch (error) {
        console.error('Error running maintenance:', error);
        alert('Error running maintenance: ' + error.message);
        setIsLoading(false);
      }
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Settings</h1>
        <div className="flex items-center space-x-2">
          {saveStatus === 'success' && (
            <div className="flex items-center text-green-600 bg-green-50 px-3 py-2 rounded">
              <Check size={16} className="mr-2" />
              Settings saved successfully
            </div>
          )}
          
          {saveStatus === 'error' && (
            <div className="flex items-center text-red-600 bg-red-50 px-3 py-2 rounded">
              <X size={16} className="mr-2" />
              Error saving settings
            </div>
          )}
          
          <button 
            onClick={saveSettings} 
            disabled={isLoading}
            className="flex items-center px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            <Save size={16} className="mr-2" />
            Save Settings
          </button>
        </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Dashboard Settings */}
        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="text-lg font-medium mb-4">Dashboard Settings</h2>
          
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <div>
                <label className="block text-sm font-medium text-gray-700">Dark Mode</label>
                <span className="text-sm text-gray-500">Enable dark mode for the dashboard</span>
              </div>
              <div className="relative inline-block w-12 h-6 rounded-full bg-gray-200">
                <input 
                  type="checkbox" 
                  id="dark-mode-toggle" 
                  className="sr-only"
                  checked={isDarkMode}
                  onChange={toggleDarkMode}
                />
                <label 
                  htmlFor="dark-mode-toggle" 
                  className="absolute inset-0 rounded-full cursor-pointer"
                >
                  <div className={`absolute w-6 h-6 rounded-full transition-transform ${isDarkMode ? 'bg-blue-600 transform translate-x-6' : 'bg-white'}`}>
                    {isDarkMode ? (
                      <Moon size={14} className="m-1 text-white" />
                    ) : (
                      <Sun size={14} className="m-1 text-yellow-500" />
                    )}
                  </div>
                </label>
              </div>
            </div>
            
            <div>
              <label htmlFor="refresh-interval" className="block text-sm font-medium text-gray-700">
                Refresh Interval (seconds)
              </label>
              <select
                id="refresh-interval"
                value={settings.refreshInterval}
                onChange={(e) => handleRefreshIntervalChange(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              >
                <option value="10">10 seconds</option>
                <option value="30">30 seconds</option>
                <option value="60">1 minute</option>
                <option value="300">5 minutes</option>
                <option value="0">Manual refresh</option>
              </select>
              <p className="mt-1 text-sm text-gray-500">
                How often the dashboard automatically refreshes data
              </p>
            </div>
            
            <div>
              <label htmlFor="data-retention" className="block text-sm font-medium text-gray-700">
                Data Retention (days)
              </label>
              <select
                id="data-retention"
                value={settings.dataRetentionDays}
                onChange={(e) => handleDataRetentionChange(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              >
                <option value="1">1 day</option>
                <option value="3">3 days</option>
                <option value="7">7 days</option>
                <option value="14">14 days</option>
                <option value="30">30 days</option>
              </select>
              <p className="mt-1 text-sm text-gray-500">
                How long to keep historical data before automatic cleanup
              </p>
            </div>
            
            <div className="pt-4">
              <button
                onClick={handleDatabaseMaintenance}
                disabled={isLoading}
                className="flex items-center px-3 py-2 border border-gray-300 rounded text-sm hover:bg-gray-50"
              >
                <Database size={16} className="mr-2" />
                Run Database Maintenance
              </button>
              <p className="mt-1 text-sm text-gray-500">
                Manually clean up old data and optimize database
              </p>
            </div>
          </div>
        </div>
        
        {/* Analysis Settings */}
        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="text-lg font-medium mb-4">Analysis Settings</h2>
          
          <div className="space-y-4">
            <div>
              <label htmlFor="job-matching-threshold" className="block text-sm font-medium text-gray-700">
                Job Matching Threshold
              </label>
              <input
                id="job-matching-threshold"
                type="number"
                min="1"
                max="20"
                value={settings.analysis.jobMatchingThreshold}
                onChange={(e) => handleJobMatchingThresholdChange(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
              <p className="mt-1 text-sm text-gray-500">
                Minimum score required to consider two jobs as matching (higher = stricter matching)
              </p>
            </div>
            
            <div>
              <label htmlFor="time-window" className="block text-sm font-medium text-gray-700">
                Time Window (seconds)
              </label>
              <input
                id="time-window"
                type="number"
                min="60"
                max="3600"
                step="60"
                value={settings.analysis.timeWindow}
                onChange={(e) => handleTimeWindowChange(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
              <p className="mt-1 text-sm text-gray-500">
                Time window for considering jobs related (lower = faster but might miss matches)
              </p>
            </div>
            
            <div className="flex justify-between items-center pt-2">
              <div>
                <label className="block text-sm font-medium text-gray-700">Propagation Analysis</label>
                <span className="text-sm text-gray-500">Enable propagation time analysis</span>
              </div>
              <div className="relative inline-block w-12 h-6 rounded-full bg-gray-200">
                <input 
                  type="checkbox" 
                  id="propagation-toggle" 
                  className="sr-only"
                  checked={settings.analysis.propagationAnalysisEnabled}
                  onChange={() => handleAnalysisToggle('propagationAnalysisEnabled')}
                />
                <label 
                  htmlFor="propagation-toggle" 
                  className="absolute inset-0 rounded-full cursor-pointer"
                >
                  <div className={`absolute w-6 h-6 rounded-full transition-transform ${settings.analysis.propagationAnalysisEnabled ? 'bg-blue-600 transform translate-x-6' : 'bg-white'}`} />
                </label>
              </div>
            </div>
            
            <div className="flex justify-between items-center">
              <div>
                <label className="block text-sm font-medium text-gray-700">Region Analysis</label>
                <span className="text-sm text-gray-500">Enable regional propagation analysis</span>
              </div>
              <div className="relative inline-block w-12 h-6 rounded-full bg-gray-200">
                <input 
                  type="checkbox" 
                  id="region-toggle" 
                  className="sr-only"
                  checked={settings.analysis.regionAnalysisEnabled}
                  onChange={() => handleAnalysisToggle('regionAnalysisEnabled')}
                />
                <label 
                  htmlFor="region-toggle" 
                  className="absolute inset-0 rounded-full cursor-pointer"
                >
                  <div className={`absolute w-6 h-6 rounded-full transition-transform ${settings.analysis.regionAnalysisEnabled ? 'bg-blue-600 transform translate-x-6' : 'bg-white'}`} />
                </label>
              </div>
            </div>
          </div>
        </div>
        
        {/* Service Settings */}
        <div className="bg-white rounded-lg shadow p-4 lg:col-span-2">
          <h2 className="text-lg font-medium mb-4">Service Settings</h2>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Service
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Enabled
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    WebSocket URL
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Region
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {Object.entries(settings.services).map(([service, config]) => (
                  <tr key={service}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{service}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="relative inline-block w-12 h-6 rounded-full bg-gray-200">
                        <input 
                          type="checkbox" 
                          id={`service-toggle-${service}`} 
                          className="sr-only"
                          checked={config.enabled}
                          onChange={() => handleServiceToggle(service)}
                        />
                        <label 
                          htmlFor={`service-toggle-${service}`} 
                          className="absolute inset-0 rounded-full cursor-pointer"
                        >
                          <div className={`absolute w-6 h-6 rounded-full transition-transform ${config.enabled ? 'bg-blue-600 transform translate-x-6' : 'bg-white'}`} />
                        </label>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <input
                        type="text"
                        value={config.url}
                        onChange={(e) => handleServiceUrlChange(service, e.target.value)}
                        className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm"
                      />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <select
                        value={config.region}
                        onChange={(e) => handleServiceRegionChange(service, e.target.value)}
                        className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm"
                      >
                        <option value="global">Global</option>
                        <option value="us">United States</option>
                        <option value="eu">Europe</option>
                        <option value="asia">Asia</option>
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          <div className="mt-4 bg-yellow-50 border-l-4 border-yellow-400 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <AlertTriangle className="h-5 w-5 text-yellow-400" />
              </div>
              <div className="ml-3">
                <p className="text-sm text-yellow-700">
                  Changing service settings may affect data collection. Please restart the application after saving for changes to take effect.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SettingsPage;
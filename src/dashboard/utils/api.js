import axios from 'axios';

// Create a config object with default settings
const apiConfig = {
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8080',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
};

// axios instance created with the config
const api = axios.create(apiConfig);

// Adding a request interceptor for authentication if needed
api.interceptors.request.use(
  (config) => {
    // adding auth tokens here (if needed in the future)
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle specific error cases
    if (error.response) {
      // Server responded with an error status
      console.error('API Error:', error.response.status, error.response.data);
      
      // handle specific status codes here
      if (error.response.status === 401) {
        // Handle unauthorized
      } else if (error.response.status === 404) {
        // Handle not found
      }
    } else if (error.request) {
      // Request was made but no response received
      console.error('API Error: No response received', error.request);
    } else {
      // Error in setting up the request
      console.error('API Error:', error.message);
    }
    
    return Promise.reject(error);
  }
);

// Define API endpoints
const endpoints = {
  // Stats endpoints
  getStats: () => api.get('/api/stats'),
  getStatsHistory: (field, hours = 24, interval = 5) => 
    api.get(`/api/stats/history/${field}?hours=${hours}&interval=${interval}`),
  
  // Jobs endpoints
  getJobs: (params = {}) => api.get('/api/jobs', { params }),
  getJobByID: (jobId, source) => api.get(`/api/jobs/${jobId}?source=${source}`),
  getJobsByHeight: (height, params = {}) => api.get(`/api/jobs/height/${height}`, { params }),
  getJobsByPool: (pool, params = {}) => api.get(`/api/jobs/pool/${pool}`, { params }),
  
  // Matches endpoints
  getMatches: (params = {}) => api.get('/api/matches', { params }),
  getMatchesByPool: (pool, params = {}) => api.get(`/api/matches/pool/${pool}`, { params }),
  
  // Propagation endpoints
  getPropagation: (sourcePair, hours = 24) => 
    api.get(`/api/propagation/${sourcePair}?hours=${hours}`),
  
  // Pools endpoints
  getPools: (limit = 10) => api.get(`/api/pools?limit=${limit}`),
  
  // Client status endpoint
  getClients: () => api.get('/api/clients'),
  
  // Health check
  getHealth: () => api.get('/api/health'),
};

// Export both the raw axios instance and the endpoints
export { api as default, endpoints };
import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { SidebarIcon, Server, Layers, BarChart2, Activity, Settings } from 'lucide-react';

// Import pages
import OverviewPage from './pages/OverviewPage';
import JobComparisonPage from './pages/JobComparisonPage';
import PropagationAnalysisPage from './pages/PropagationAnalysisPage';
import PoolAnalysisPage from './pages/PoolAnalysisPage';
import SettingsPage from './pages/SettingsPage';

// Import components
import Header from './components/Header';
import Footer from './components/Footer';

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <Router>
      <div className="flex h-screen bg-gray-100">
        {/* Sidebar */}
        <div className={`${sidebarOpen ? 'w-64' : 'w-20'} bg-blue-800 text-white transition-all duration-300 ease-in-out`}>
          <div className="p-4 flex justify-between items-center">
            <h1 className={`font-bold text-xl ${!sidebarOpen && 'hidden'}`}>StratumSync</h1>
            <button onClick={toggleSidebar} className="p-1 rounded-md hover:bg-blue-700">
              <SidebarIcon size={20} />
            </button>
          </div>
          <nav className="mt-6">
            <NavItem to="/" icon={<Server size={20} />} text="Overview" sidebarOpen={sidebarOpen} />
            <NavItem to="/jobs" icon={<Layers size={20} />} text="Job Comparison" sidebarOpen={sidebarOpen} />
            <NavItem to="/propagation" icon={<Activity size={20} />} text="Propagation" sidebarOpen={sidebarOpen} />
            <NavItem to="/pools" icon={<BarChart2 size={20} />} text="Pool Analysis" sidebarOpen={sidebarOpen} />
            <NavItem to="/settings" icon={<Settings size={20} />} text="Settings" sidebarOpen={sidebarOpen} />
          </nav>
        </div>

        {/* Main content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <Header />
          <main className="flex-1 overflow-y-auto p-4">
            <Routes>
              <Route path="/" element={<OverviewPage />} />
              <Route path="/jobs" element={<JobComparisonPage />} />
              <Route path="/propagation" element={<PropagationAnalysisPage />} />
              <Route path="/pools" element={<PoolAnalysisPage />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Routes>
          </main>
          <Footer />
        </div>
      </div>
    </Router>
  );
}

// Navigation item component
function NavItem({ to, icon, text, sidebarOpen }) {
  return (
    <Link to={to} className="flex items-center px-4 py-3 text-white hover:bg-blue-700 transition-colors">
      <span className="mr-4">{icon}</span>
      {sidebarOpen && <span>{text}</span>}
    </Link>
  );
}

export default App;
import React from 'react';

function Footer() {
  const currentYear = new Date().getFullYear();
  
  return (
    <footer className="bg-white shadow-md px-6 py-2 text-center text-sm text-gray-500">
      <div className="flex justify-between items-center">
        <div>
          StratumSync © {currentYear} | Bitcoin Stratum Monitoring Comparison Tool
        </div>
        <div className="flex space-x-4">
          <a href="https://github.com/your-username/stratum-sync" className="hover:text-blue-600 transition-colors">GitHub</a>
          <a href="#" className="hover:text-blue-600 transition-colors">Documentation</a>
          <a href="#" className="hover:text-blue-600 transition-colors">About</a>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
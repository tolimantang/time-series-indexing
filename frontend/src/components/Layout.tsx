'use client';

import React, { useState, useEffect } from 'react';
import { Moon, Sun, Github, Activity, Database, Sparkles } from 'lucide-react';
import AstroFinancialAPI from '@/lib/api';
import { UserProfile } from './UserProfile';
import { useAuth } from '../contexts/AuthContext';

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const [isDark, setIsDark] = useState(false);
  const [apiStatus, setApiStatus] = useState<'connecting' | 'connected' | 'error'>('connecting');
  const [systemStats, setSystemStats] = useState<any>(null);
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    checkApiStatus();
    const interval = setInterval(checkApiStatus, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const checkApiStatus = async () => {
    try {
      const isConnected = await AstroFinancialAPI.checkConnection();
      if (isConnected) {
        setApiStatus('connected');
        // Get system stats
        try {
          const health = await AstroFinancialAPI.getHealth();
          setSystemStats(health);
        } catch (error) {
          console.error('Failed to fetch system stats:', error);
        }
      } else {
        setApiStatus('error');
      }
    } catch (error) {
      setApiStatus('error');
    }
  };

  const toggleTheme = () => {
    setIsDark(!isDark);
    document.documentElement.classList.toggle('dark');
  };

  const getStatusColor = () => {
    switch (apiStatus) {
      case 'connected': return 'text-green-500';
      case 'error': return 'text-red-500';
      default: return 'text-yellow-500';
    }
  };

  const getStatusText = () => {
    switch (apiStatus) {
      case 'connected': return 'API Connected';
      case 'error': return 'API Disconnected';
      default: return 'Connecting...';
    }
  };

  return (
    <div className={`min-h-screen transition-colors ${isDark ? 'dark bg-gray-900' : 'bg-gray-50'}`}>
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo and title */}
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-8 h-8 text-blue-600" />
                <div>
                  <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                    AstroFinancial
                  </h1>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Celestial Market Intelligence
                  </p>
                </div>
              </div>
            </div>

            {/* Status and controls */}
            <div className="flex items-center gap-4">
              {/* API Status */}
              {isAuthenticated && (
                <div className="flex items-center gap-2 text-sm">
                  <div className={`w-2 h-2 rounded-full ${getStatusColor().replace('text-', 'bg-')}`} />
                  <span className={`${getStatusColor()}`}>
                    {getStatusText()}
                  </span>
                </div>
              )}

              {/* System stats */}
              {isAuthenticated && systemStats && (
                <div className="hidden md:flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
                  {systemStats.postgresql && (
                    <div className="flex items-center gap-1">
                      <Database className="w-3 h-3" />
                      <span>{systemStats.postgresql.total_records.toLocaleString()} records</span>
                    </div>
                  )}
                  {systemStats.chromadb && (
                    <div className="flex items-center gap-1">
                      <Activity className="w-3 h-3" />
                      <span>{systemStats.chromadb.astro_detailed} embeddings</span>
                    </div>
                  )}
                </div>
              )}

              {/* Theme toggle */}
              <button
                onClick={toggleTheme}
                className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
                aria-label="Toggle theme"
              >
                {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
              </button>

              {/* GitHub link */}
              <a
                href="https://github.com/yetang/time-series-indexing"
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
                aria-label="View on GitHub"
              >
                <Github className="w-5 h-5" />
              </a>

              {/* User Profile */}
              {isAuthenticated && <UserProfile />}
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* About */}
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wide">
                About AstroFinancial
              </h3>
              <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                Advanced correlation analysis between astronomical events and financial markets using
                natural language processing and semantic search.
              </p>
            </div>

            {/* Features */}
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wide">
                Features
              </h3>
              <ul className="mt-2 space-y-1 text-sm text-gray-600 dark:text-gray-400">
                <li>• Semantic astronomical pattern search</li>
                <li>• Market correlation analysis</li>
                <li>• 50+ years of historical data</li>
                <li>• 384-dimensional embeddings</li>
                <li>• Real-time API integration</li>
              </ul>
            </div>

            {/* Technical */}
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wide">
                Technology Stack
              </h3>
              <ul className="mt-2 space-y-1 text-sm text-gray-600 dark:text-gray-400">
                <li>• Swiss Ephemeris calculations</li>
                <li>• Sentence Transformers ML</li>
                <li>• ChromaDB vector search</li>
                <li>• PostgreSQL data storage</li>
                <li>• FastAPI + Next.js</li>
              </ul>
            </div>
          </div>

          <div className="mt-8 pt-8 border-t border-gray-200 dark:border-gray-700">
            <div className="flex justify-between items-center">
              <p className="text-sm text-gray-500 dark:text-gray-400">
                © 2024 AstroFinancial System. Built for research and educational purposes.
              </p>
              <div className="flex items-center gap-2 text-xs text-gray-400">
                <span>Powered by</span>
                <Sparkles className="w-3 h-3" />
                <span>Claude Code</span>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
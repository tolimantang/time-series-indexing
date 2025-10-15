import React, { useState, useEffect } from 'react';
import { Clock, Search, BarChart3, Eye, Trash2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

interface SearchHistoryItem {
  id: string;
  query: string;
  search_type: 'semantic' | 'pattern_analysis';
  created_at: string;
  results_count: number;
  query_parameters: any;
}

interface SearchHistoryProps {
  onSelectQuery?: (query: string, type: 'semantic' | 'pattern_analysis', parameters?: any) => void;
}

export const SearchHistory: React.FC<SearchHistoryProps> = ({ onSelectQuery }) => {
  const [history, setHistory] = useState<SearchHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { token } = useAuth();

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    if (token) {
      fetchSearchHistory();
    }
  }, [token]);

  const fetchSearchHistory = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/auth/search-history`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch search history');
      }

      const data = await response.json();
      setHistory(data.searches || []);
    } catch (error) {
      console.error('Error fetching search history:', error);
      setError('Failed to load search history');
    } finally {
      setLoading(false);
    }
  };

  const deleteSearchHistoryItem = async (searchId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/search-history/${searchId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to delete search history item');
      }

      // Remove from local state
      setHistory(prev => prev.filter(item => item.id !== searchId));
    } catch (error) {
      console.error('Error deleting search history:', error);
    }
  };

  const handleSelectQuery = (item: SearchHistoryItem) => {
    if (onSelectQuery) {
      onSelectQuery(item.query, item.search_type, item.query_parameters);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

    if (diffInHours < 1) {
      const minutes = Math.floor(diffInHours * 60);
      return `${minutes}m ago`;
    } else if (diffInHours < 24) {
      return `${Math.floor(diffInHours)}h ago`;
    } else if (diffInHours < 24 * 7) {
      return `${Math.floor(diffInHours / 24)}d ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  const getSearchTypeIcon = (type: string) => {
    return type === 'semantic' ? <Search className="w-4 h-4" /> : <BarChart3 className="w-4 h-4" />;
  };

  const getSearchTypeColor = (type: string) => {
    return type === 'semantic'
      ? 'text-blue-600 bg-blue-100 dark:bg-blue-900 dark:text-blue-300'
      : 'text-green-600 bg-green-100 dark:bg-green-900 dark:text-green-300';
  };

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Search History</h3>
        </div>
        <div className="p-6 text-center">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mx-auto"></div>
          <p className="text-gray-500 dark:text-gray-400 mt-2">Loading search history...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Search History</h3>
        </div>
        <div className="p-6 text-center">
          <p className="text-red-500">{error}</p>
          <button
            onClick={fetchSearchHistory}
            className="mt-2 text-blue-600 hover:text-blue-700 dark:text-blue-400"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Search History</h3>
          <div className="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400">
            <Clock className="w-4 h-4" />
            <span>{history.length} searches</span>
          </div>
        </div>
      </div>

      <div className="max-h-96 overflow-y-auto">
        {history.length === 0 ? (
          <div className="p-6 text-center">
            <Search className="w-8 h-8 text-gray-400 mx-auto mb-2" />
            <p className="text-gray-500 dark:text-gray-400">No search history yet</p>
            <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">
              Your searches will appear here
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {history.map((item) => (
              <div
                key={item.id}
                className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getSearchTypeColor(item.search_type)}`}>
                        {getSearchTypeIcon(item.search_type)}
                        {item.search_type === 'semantic' ? 'Search' : 'Analysis'}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {formatDate(item.created_at)}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {item.results_count} results
                      </span>
                    </div>

                    <p className="text-sm font-medium text-gray-900 dark:text-white mb-1 truncate">
                      {item.query}
                    </p>

                    {item.query_parameters && (
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {item.search_type === 'pattern_analysis' && (
                          <span>
                            {item.query_parameters.lookback_days}d lookback • {item.query_parameters.target_assets?.join(', ')}
                          </span>
                        )}
                        {item.search_type === 'semantic' && (
                          <span>
                            Max {item.query_parameters.max_results} results
                          </span>
                        )}
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-1 ml-2">
                    <button
                      onClick={() => handleSelectQuery(item)}
                      className="p-1.5 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                      title="Use this query"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => deleteSearchHistoryItem(item.id)}
                      className="p-1.5 text-gray-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
                      title="Delete from history"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {history.length > 0 && (
        <div className="p-4 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={fetchSearchHistory}
            className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
          >
            Refresh history
          </button>
        </div>
      )}
    </div>
  );
};
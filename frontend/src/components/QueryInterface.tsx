'use client';

import React, { useState } from 'react';
import { Search, BarChart3, Clock, Loader2 } from 'lucide-react';
import AstroFinancialAPI from '@/lib/api';
import type { QueryResponse, PatternAnalysisResponse } from '@/types/api';

interface QueryInterfaceProps {
  onSearchResults: (results: QueryResponse) => void;
  onPatternAnalysis: (results: PatternAnalysisResponse) => void;
}

export default function QueryInterface({ onSearchResults, onPatternAnalysis }: QueryInterfaceProps) {
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [maxResults, setMaxResults] = useState(10);
  const [lookbackDays, setLookbackDays] = useState(30);
  const [targetAssets, setTargetAssets] = useState(['SPY', 'VIX', 'EURUSD']);

  const handleSemanticSearch = async () => {
    if (!query.trim()) return;

    setIsSearching(true);
    try {
      const results = await AstroFinancialAPI.semanticSearch({
        query: query.trim(),
        max_results: maxResults,
        include_market_data: true
      });
      onSearchResults(results);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setIsSearching(false);
    }
  };

  const handlePatternAnalysis = async () => {
    if (!query.trim()) return;

    setIsAnalyzing(true);
    try {
      const results = await AstroFinancialAPI.patternAnalysis({
        query: query.trim(),
        lookback_days: lookbackDays,
        target_assets: targetAssets
      });
      onPatternAnalysis(results);
    } catch (error) {
      console.error('Analysis error:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const exampleQueries = [
    "Saturn in Capricorn with Mercury retrograde",
    "Moon conjunct Jupiter in Cancer",
    "Mars opposition Neptune tight aspects",
    "Multiple planetary conjunctions",
    "Venus in Gemini with lunar eclipse"
  ];

  const handleExampleClick = (example: string) => {
    setQuery(example);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSemanticSearch();
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">
          Astro-Financial Pattern Search
        </h2>
        <p className="text-gray-600">
          Discover how astronomical events correlate with market movements using natural language queries.
        </p>
      </div>

      {/* Main Query Input */}
      <div className="mb-6">
        <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-2">
          Astronomical Query
        </label>
        <div className="relative">
          <textarea
            id="query"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="e.g., What happens to EUR/USD when Saturn and Neptune are conjunct, Jupiter is in late Cancer, and moon about to go to Gemini"
            className="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            rows={3}
          />
          <div className="absolute bottom-2 right-2 text-xs text-gray-400">
            Press Enter to search
          </div>
        </div>
      </div>

      {/* Example Queries */}
      <div className="mb-6">
        <h3 className="text-sm font-medium text-gray-700 mb-2">Example Queries:</h3>
        <div className="flex flex-wrap gap-2">
          {exampleQueries.map((example, index) => (
            <button
              key={index}
              onClick={() => handleExampleClick(example)}
              className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full transition-colors"
            >
              {example}
            </button>
          ))}
        </div>
      </div>

      {/* Search Options */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div>
          <label htmlFor="maxResults" className="block text-sm font-medium text-gray-700 mb-1">
            Max Results
          </label>
          <select
            id="maxResults"
            value={maxResults}
            onChange={(e) => setMaxResults(Number(e.target.value))}
            className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value={5}>5 results</option>
            <option value={10}>10 results</option>
            <option value={20}>20 results</option>
            <option value={50}>50 results</option>
          </select>
        </div>

        <div>
          <label htmlFor="lookbackDays" className="block text-sm font-medium text-gray-700 mb-1">
            Analysis Period (days)
          </label>
          <select
            id="lookbackDays"
            value={lookbackDays}
            onChange={(e) => setLookbackDays(Number(e.target.value))}
            className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value={7}>7 days</option>
            <option value={30}>30 days</option>
            <option value={90}>90 days</option>
            <option value={365}>1 year</option>
          </select>
        </div>

        <div>
          <label htmlFor="targetAssets" className="block text-sm font-medium text-gray-700 mb-1">
            Target Assets
          </label>
          <input
            id="targetAssets"
            type="text"
            value={targetAssets.join(', ')}
            onChange={(e) => setTargetAssets(e.target.value.split(',').map(s => s.trim()))}
            placeholder="SPY, VIX, EURUSD"
            className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row gap-3">
        <button
          onClick={handleSemanticSearch}
          disabled={!query.trim() || isSearching}
          className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium rounded-lg transition-colors"
        >
          {isSearching ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Search className="w-4 h-4" />
          )}
          {isSearching ? 'Searching...' : 'Semantic Search'}
        </button>

        <button
          onClick={handlePatternAnalysis}
          disabled={!query.trim() || isAnalyzing}
          className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-medium rounded-lg transition-colors"
        >
          {isAnalyzing ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <BarChart3 className="w-4 h-4" />
          )}
          {isAnalyzing ? 'Analyzing...' : 'Pattern Analysis'}
        </button>
      </div>

      {/* Query Stats */}
      <div className="mt-4 flex items-center gap-4 text-xs text-gray-500">
        <div className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          <span>Response time: &lt;2s average</span>
        </div>
        <div>•</div>
        <div>384-dimensional semantic embeddings</div>
        <div>•</div>
        <div>50+ years of astronomical data</div>
      </div>
    </div>
  );
}
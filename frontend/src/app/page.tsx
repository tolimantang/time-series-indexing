'use client';

import React, { useState } from 'react';
import Layout from '@/components/Layout';
import QueryInterface from '@/components/QueryInterface';
import ResultsDisplay from '@/components/ResultsDisplay';
import PatternAnalysis from '@/components/PatternAnalysis';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import type { QueryResponse, PatternAnalysisResponse } from '@/types/api';

export default function HomePage() {
  const [searchResults, setSearchResults] = useState<QueryResponse | null>(null);
  const [analysisResults, setAnalysisResults] = useState<PatternAnalysisResponse | null>(null);
  const [activeTab, setActiveTab] = useState<'search' | 'analysis'>('search');

  const handleSearchResults = (results: QueryResponse) => {
    setSearchResults(results);
    setActiveTab('search');
  };

  const handlePatternAnalysis = (results: PatternAnalysisResponse) => {
    setAnalysisResults(results);
    setActiveTab('analysis');
  };

  return (
    <ProtectedRoute>
      <Layout>
        <div className="space-y-8">
        {/* Hero section */}
        <div className="text-center py-12">
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 dark:text-white mb-4">
            Astro<span className="text-blue-600">Financial</span>
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto mb-8">
            Discover hidden correlations between celestial events and financial markets using
            advanced AI-powered semantic search and pattern analysis.
          </p>
          <div className="flex justify-center gap-8 text-sm text-gray-500">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <span>50+ Years of Data</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span>Real-time Analysis</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
              <span>ML-Powered Search</span>
            </div>
          </div>
        </div>

        {/* Query interface */}
        <QueryInterface
          onSearchResults={handleSearchResults}
          onPatternAnalysis={handlePatternAnalysis}
        />

        {/* Results section */}
        {(searchResults || analysisResults) && (
          <div className="space-y-6">
            {/* Tab navigation */}
            <div className="flex justify-center">
              <div className="flex bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
                <button
                  onClick={() => setActiveTab('search')}
                  className={`px-6 py-2 rounded-md text-sm font-medium transition-colors ${
                    activeTab === 'search'
                      ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                      : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
                  }`}
                  disabled={!searchResults}
                >
                  Search Results
                  {searchResults && (
                    <span className="ml-2 px-2 py-0.5 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs rounded-full">
                      {searchResults.results_count}
                    </span>
                  )}
                </button>
                <button
                  onClick={() => setActiveTab('analysis')}
                  className={`px-6 py-2 rounded-md text-sm font-medium transition-colors ${
                    activeTab === 'analysis'
                      ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                      : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
                  }`}
                  disabled={!analysisResults}
                >
                  Pattern Analysis
                  {analysisResults && (
                    <span className="ml-2 px-2 py-0.5 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 text-xs rounded-full">
                      {analysisResults.results_count}
                    </span>
                  )}
                </button>
              </div>
            </div>

            {/* Tab content */}
            <div className="min-h-[400px]">
              {activeTab === 'search' && <ResultsDisplay results={searchResults} />}
              {activeTab === 'analysis' && <PatternAnalysis analysis={analysisResults} />}
            </div>
          </div>
        )}

        {/* Getting started section (only show when no results) */}
        {!searchResults && !analysisResults && (
          <div className="max-w-4xl mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-16">
              {/* Semantic Search */}
              <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
                    <span className="text-blue-600 dark:text-blue-400 text-sm font-bold">1</span>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Semantic Search
                  </h3>
                </div>
                <p className="text-gray-600 dark:text-gray-300 mb-4">
                  Use natural language to find similar astronomical patterns in history.
                  Our AI understands complex celestial relationships and finds matching periods.
                </p>
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  <strong>Example:</strong> "Saturn in Capricorn with Mercury retrograde"
                </div>
              </div>

              {/* Pattern Analysis */}
              <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-8 h-8 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center">
                    <span className="text-green-600 dark:text-green-400 text-sm font-bold">2</span>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Pattern Analysis
                  </h3>
                </div>
                <p className="text-gray-600 dark:text-gray-300 mb-4">
                  Analyze how specific astronomical events correlate with market movements.
                  Get statistical insights, volatility metrics, and historical performance.
                </p>
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  <strong>Includes:</strong> Returns, volatility, success rates, significant moves
                </div>
              </div>
            </div>

            {/* Features grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
              <div className="text-center">
                <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-purple-600 dark:text-purple-400 text-lg">🪐</span>
                </div>
                <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                  Swiss Ephemeris
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-300">
                  High-precision astronomical calculations using the industry-standard Swiss Ephemeris library
                </p>
              </div>

              <div className="text-center">
                <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-blue-600 dark:text-blue-400 text-lg">🤖</span>
                </div>
                <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                  AI-Powered
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-300">
                  384-dimensional embeddings using Sentence Transformers for semantic understanding
                </p>
              </div>

              <div className="text-center">
                <div className="w-12 h-12 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-green-600 dark:text-green-400 text-lg">📊</span>
                </div>
                <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                  Market Data
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-300">
                  Comprehensive analysis across major asset classes including forex, indices, and volatility
                </p>
              </div>
            </div>
          </div>
        )}
        </div>
      </Layout>
    </ProtectedRoute>
  );
}

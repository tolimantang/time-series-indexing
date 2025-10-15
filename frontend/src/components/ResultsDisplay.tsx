'use client';

import React from 'react';
import { Calendar, Clock, Star, TrendingUp, Moon, Sun } from 'lucide-react';
import type { QueryResponse, QueryResult } from '@/types/api';

interface ResultsDisplayProps {
  results: QueryResponse | null;
}

export default function ResultsDisplay({ results }: ResultsDisplayProps) {
  if (!results) {
    return (
      <div className="w-full max-w-4xl mx-auto p-6 bg-gray-50 rounded-lg text-center">
        <div className="text-gray-500">
          <Search className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>Enter a query above to discover astronomical patterns and their market correlations.</p>
        </div>
      </div>
    );
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const getSimilarityColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 bg-green-100';
    if (score >= 0.6) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getMoonPhaseIcon = (phase: number) => {
    // Phase is typically 0-1, where 0/1 = new moon, 0.5 = full moon
    if (phase < 0.125 || phase > 0.875) return <Moon className="w-4 h-4" />;
    if (phase >= 0.375 && phase <= 0.625) return <Sun className="w-4 h-4" />;
    return <div className="w-4 h-4 rounded-full bg-gray-400" />;
  };

  const ResultCard = ({ result }: { result: QueryResult }) => (
    <div className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
      {/* Header with date and similarity */}
      <div className="flex justify-between items-start mb-4">
        <div className="flex items-center gap-2">
          <Calendar className="w-5 h-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-800">
            {formatDate(result.date)}
          </h3>
        </div>
        <div className={`px-3 py-1 rounded-full text-sm font-medium ${getSimilarityColor(result.similarity_score)}`}>
          {(result.similarity_score * 100).toFixed(1)}% match
        </div>
      </div>

      {/* Astronomical description */}
      <div className="mb-4">
        <p className="text-gray-700 leading-relaxed">
          {result.description}
        </p>
      </div>

      {/* Metadata grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4 p-4 bg-gray-50 rounded-lg">
        <div className="text-center">
          <div className="text-xs text-gray-500 uppercase tracking-wide">Conjunctions</div>
          <div className="text-lg font-semibold text-blue-600">
            {result.metadata.conjunction_count}
          </div>
        </div>

        <div className="text-center">
          <div className="text-xs text-gray-500 uppercase tracking-wide">Total Aspects</div>
          <div className="text-lg font-semibold text-purple-600">
            {result.metadata.total_aspects}
          </div>
        </div>

        <div className="text-center">
          <div className="text-xs text-gray-500 uppercase tracking-wide">Lunar Phase</div>
          <div className="flex items-center justify-center gap-1">
            {getMoonPhaseIcon(result.metadata.lunar_phase)}
            <span className="text-sm font-medium">
              {(result.metadata.lunar_phase * 100).toFixed(0)}%
            </span>
          </div>
        </div>

        <div className="text-center">
          <div className="text-xs text-gray-500 uppercase tracking-wide">Tight Aspects</div>
          <div className="text-lg">
            {result.metadata.has_tight_aspects ? (
              <Star className="w-5 h-5 text-yellow-500 mx-auto" />
            ) : (
              <span className="text-gray-400">—</span>
            )}
          </div>
        </div>
      </div>

      {/* Planetary positions */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">Jupiter</div>
          <div className="text-sm font-medium text-orange-600">
            {result.metadata.jupiter_sign}
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">Saturn</div>
          <div className="text-sm font-medium text-indigo-600">
            {result.metadata.saturn_sign}
          </div>
        </div>
      </div>

      {/* Major conjunctions if present */}
      {result.metadata.major_conjunctions && (
        <div className="mb-4">
          <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">Major Conjunctions</div>
          <div className="flex flex-wrap gap-1">
            {result.metadata.major_conjunctions.split(', ').map((conjunction, index) => (
              <span
                key={index}
                className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full"
              >
                {conjunction}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Full description toggle */}
      <details className="mt-4">
        <summary className="text-sm text-blue-600 cursor-pointer hover:text-blue-800">
          View detailed astronomical description
        </summary>
        <div className="mt-2 p-3 bg-blue-50 rounded text-sm text-gray-700 leading-relaxed">
          {result.full_description}
        </div>
      </details>
    </div>
  );

  return (
    <div className="w-full max-w-4xl mx-auto">
      {/* Results header */}
      <div className="mb-6 p-4 bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="flex justify-between items-center mb-2">
          <h2 className="text-xl font-bold text-gray-800">
            Search Results
          </h2>
          <div className="flex items-center gap-4 text-sm text-gray-600">
            <div className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              <span>{results.execution_time_ms}ms</span>
            </div>
            <div className="flex items-center gap-1">
              <TrendingUp className="w-4 h-4" />
              <span>{results.results_count} results</span>
            </div>
          </div>
        </div>

        <div className="text-sm text-gray-600">
          <strong>Query:</strong> "{results.metadata.query}"
        </div>

        {results.metadata.collection && (
          <div className="text-xs text-gray-500 mt-1">
            Collection: {results.metadata.collection}
          </div>
        )}
      </div>

      {/* Results list */}
      {results.results.length === 0 ? (
        <div className="bg-white rounded-lg p-8 text-center border border-gray-200">
          <div className="text-gray-500">
            <Star className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p className="text-lg">No matching patterns found</p>
            <p className="text-sm mt-2">Try adjusting your query or using different astronomical terms.</p>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {results.results.map((result, index) => (
            <ResultCard key={index} result={result} />
          ))}
        </div>
      )}
    </div>
  );
}

function Search({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
      />
    </svg>
  );
}
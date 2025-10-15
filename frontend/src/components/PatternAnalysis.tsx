'use client';

import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts';
import { TrendingUp, TrendingDown, Minus, Calendar, DollarSign, Activity } from 'lucide-react';
import type { PatternAnalysisResponse, PatternAnalysisResult } from '@/types/api';

interface PatternAnalysisProps {
  analysis: PatternAnalysisResponse | null;
}

export default function PatternAnalysis({ analysis }: PatternAnalysisProps) {
  if (!analysis) {
    return (
      <div className="w-full max-w-4xl mx-auto p-6 bg-gray-50 rounded-lg text-center">
        <div className="text-gray-500">
          <Activity className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>Run a pattern analysis to see market correlations with astronomical events.</p>
        </div>
      </div>
    );
  }

  const getReturnColor = (returnValue: number) => {
    if (returnValue > 0) return 'text-green-600';
    if (returnValue < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const getReturnIcon = (returnValue: number) => {
    if (returnValue > 0) return <TrendingUp className="w-4 h-4" />;
    if (returnValue < 0) return <TrendingDown className="w-4 h-4" />;
    return <Minus className="w-4 h-4" />;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const COLORS = ['#10B981', '#EF4444', '#6B7280']; // green, red, gray

  const AssetAnalysisCard = ({ result }: { result: PatternAnalysisResult }) => {
    const distributionData = [
      { name: 'Positive', value: result.return_distribution.positive_days, color: COLORS[0] },
      { name: 'Negative', value: result.return_distribution.negative_days, color: COLORS[1] },
      { name: 'Neutral', value: result.return_distribution.neutral_days, color: COLORS[2] }
    ];

    const significantMovesData = result.significant_moves.map(move => ({
      date: move.date,
      return: move.return * 100, // Convert to percentage
      formattedDate: formatDate(move.date)
    }));

    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        {/* Asset header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h3 className="text-xl font-bold text-gray-800">{result.asset}</h3>
            <p className="text-sm text-gray-600">Sample size: {result.sample_size} periods</p>
          </div>
          <div className="text-right">
            <div className={`text-2xl font-bold ${getReturnColor(result.avg_return)}`}>
              {getReturnIcon(result.avg_return)}
            </div>
          </div>
        </div>

        {/* Key metrics */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-xs text-gray-500 uppercase tracking-wide">Avg Return</div>
            <div className={`text-lg font-bold ${getReturnColor(result.avg_return)}`}>
              {(result.avg_return * 100).toFixed(2)}%
            </div>
          </div>

          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-xs text-gray-500 uppercase tracking-wide">Volatility</div>
            <div className="text-lg font-bold text-blue-600">
              {(result.volatility * 100).toFixed(2)}%
            </div>
          </div>

          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-xs text-gray-500 uppercase tracking-wide">Success Rate</div>
            <div className="text-lg font-bold text-purple-600">
              {((result.return_distribution.positive_days / result.sample_size) * 100).toFixed(1)}%
            </div>
          </div>
        </div>

        {/* Return distribution pie chart */}
        <div className="mb-6">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Return Distribution</h4>
          <div className="flex items-center gap-6">
            <div className="w-32 h-32">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={distributionData}
                    cx="50%"
                    cy="50%"
                    innerRadius={25}
                    outerRadius={50}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    {distributionData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="flex-1">
              <div className="space-y-2">
                {distributionData.map((item, index) => (
                  <div key={index} className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: item.color }}
                    />
                    <span className="text-sm text-gray-600">
                      {item.name}: {item.value} days
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Significant moves */}
        {result.significant_moves.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">
              Significant Moves ({result.significant_moves.length})
            </h4>

            {/* Line chart for significant moves */}
            <div className="h-48 mb-4">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={significantMovesData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="formattedDate"
                    tick={{ fontSize: 12 }}
                    angle={-45}
                    textAnchor="end"
                    height={60}
                  />
                  <YAxis
                    tick={{ fontSize: 12 }}
                    label={{ value: 'Return (%)', angle: -90, position: 'insideLeft' }}
                  />
                  <Tooltip
                    formatter={(value: number) => [`${value.toFixed(2)}%`, 'Return']}
                    labelFormatter={(label) => `Date: ${label}`}
                  />
                  <Line
                    type="monotone"
                    dataKey="return"
                    stroke="#3B82F6"
                    strokeWidth={2}
                    dot={{ fill: '#3B82F6', strokeWidth: 2, r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Top moves list */}
            <div className="space-y-2">
              {result.significant_moves.slice(0, 5).map((move, index) => (
                <div key={index} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-gray-500" />
                    <span className="text-sm font-medium">{formatDate(move.date)}</span>
                  </div>
                  <div className={`flex items-center gap-1 ${getReturnColor(move.return)}`}>
                    {getReturnIcon(move.return)}
                    <span className="text-sm font-bold">
                      {(move.return * 100).toFixed(2)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="w-full max-w-6xl mx-auto">
      {/* Analysis header */}
      <div className="mb-6 p-4 bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="flex justify-between items-center mb-2">
          <h2 className="text-xl font-bold text-gray-800">
            Pattern Analysis Results
          </h2>
          <div className="flex items-center gap-4 text-sm text-gray-600">
            <div className="flex items-center gap-1">
              <Activity className="w-4 h-4" />
              <span>{analysis.execution_time_ms}ms</span>
            </div>
            <div className="flex items-center gap-1">
              <DollarSign className="w-4 h-4" />
              <span>{analysis.results_count} assets</span>
            </div>
          </div>
        </div>

        <div className="text-sm text-gray-600 mb-2">
          <strong>Query:</strong> "{analysis.metadata.query}"
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-gray-500">
          <div>
            <strong>Matching Periods:</strong> {analysis.metadata.matching_periods}
          </div>
          <div>
            <strong>Lookback:</strong> {analysis.metadata.lookback_days} days
          </div>
          <div>
            <strong>Assets:</strong> {analysis.metadata.target_assets.join(', ')}
          </div>
        </div>
      </div>

      {/* Analysis results */}
      {analysis.results.length === 0 ? (
        <div className="bg-white rounded-lg p-8 text-center border border-gray-200">
          <div className="text-gray-500">
            <Activity className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p className="text-lg">No pattern data found</p>
            <p className="text-sm mt-2">The query didn't match any historical periods with market data.</p>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {analysis.results.map((result, index) => (
            <AssetAnalysisCard key={index} result={result} />
          ))}
        </div>
      )}

      {/* Summary insights */}
      {analysis.results.length > 0 && (
        <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <h3 className="text-lg font-semibold text-blue-800 mb-2">Key Insights</h3>
          <div className="text-sm text-blue-700 space-y-1">
            <div>
              • Best performing asset: {analysis.results.reduce((best, current) =>
                current.avg_return > best.avg_return ? current : best
              ).asset} ({(analysis.results.reduce((best, current) =>
                current.avg_return > best.avg_return ? current : best
              ).avg_return * 100).toFixed(2)}% avg return)
            </div>
            <div>
              • Most volatile: {analysis.results.reduce((most, current) =>
                current.volatility > most.volatility ? current : most
              ).asset} ({(analysis.results.reduce((most, current) =>
                current.volatility > most.volatility ? current : most
              ).volatility * 100).toFixed(2)}% volatility)
            </div>
            <div>
              • Total patterns analyzed: {analysis.metadata.matching_periods} occurrences
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
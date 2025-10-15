// API client for the astro-financial system

import axios from 'axios';
import type {
  SemanticQueryRequest,
  QueryResponse,
  PatternAnalysisRequest,
  PatternAnalysisResponse,
  HealthResponse,
  ExampleQueries,
} from '@/types/api';

// Configure the base API client
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    throw error;
  }
);

export class AstroFinancialAPI {
  /**
   * Check API health and get system statistics
   */
  static async getHealth(): Promise<HealthResponse> {
    const response = await apiClient.get<HealthResponse>('/health');
    return response.data;
  }

  /**
   * Get example queries for the frontend
   */
  static async getExamples(): Promise<ExampleQueries> {
    const response = await apiClient.get<ExampleQueries>('/query/examples');
    return response.data;
  }

  /**
   * Perform semantic search using natural language
   */
  static async semanticSearch(request: SemanticQueryRequest): Promise<QueryResponse> {
    const response = await apiClient.post<QueryResponse>('/query/semantic', {
      query: request.query,
      max_results: request.max_results || 10,
      collection_name: request.collection_name || 'astronomical_detailed',
      include_market_data: request.include_market_data ?? true,
    });
    return response.data;
  }

  /**
   * Analyze market patterns for astronomical events
   */
  static async patternAnalysis(request: PatternAnalysisRequest): Promise<PatternAnalysisResponse> {
    const response = await apiClient.post<PatternAnalysisResponse>('/analysis/pattern', {
      query: request.query,
      lookback_days: request.lookback_days || 30,
      target_assets: request.target_assets || ['SPY', 'VIX', 'EURUSD'],
    });
    return response.data;
  }

  /**
   * Check if the API is accessible
   */
  static async checkConnection(): Promise<boolean> {
    try {
      const response = await apiClient.get('/');
      return response.status === 200;
    } catch {
      return false;
    }
  }
}

export default AstroFinancialAPI;
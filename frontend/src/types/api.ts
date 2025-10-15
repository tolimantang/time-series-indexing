// API types for the astro-financial system

export interface SemanticQueryRequest {
  query: string;
  max_results?: number;
  collection_name?: string;
  include_market_data?: boolean;
}

export interface QueryResult {
  date: string;
  similarity_score: number;
  description: string;
  full_description: string;
  metadata: {
    date: string;
    year: number;
    month: number;
    day: number;
    conjunction_count: number;
    jupiter_sign: string;
    saturn_sign: string;
    total_aspects: number;
    lunar_phase: number;
    has_tight_aspects: boolean;
    major_conjunctions?: string;
  };
}

export interface QueryResponse {
  query_type: string;
  results_count: number;
  results: QueryResult[];
  execution_time_ms: number;
  metadata: {
    query: string;
    collection?: string;
    include_market_data?: boolean;
  };
}

export interface PatternAnalysisRequest {
  query: string;
  lookback_days?: number;
  target_assets?: string[];
}

export interface PatternAnalysisResult {
  asset: string;
  sample_size: number;
  avg_return: number;
  volatility: number;
  return_distribution: {
    positive_days: number;
    negative_days: number;
    neutral_days: number;
  };
  significant_moves: Array<{
    date: string;
    return: number;
  }>;
}

export interface PatternAnalysisResponse {
  query_type: string;
  results_count: number;
  results: PatternAnalysisResult[];
  execution_time_ms: number;
  metadata: {
    query: string;
    matching_periods: number;
    lookback_days: number;
    target_assets: string[];
  };
}

export interface HealthResponse {
  status: string;
  postgresql?: {
    total_records: number;
    unique_dates: number;
    date_range: {
      start: string | null;
      end: string | null;
    };
    avg_quality_score: number;
  };
  chromadb?: {
    astro_detailed: number;
    astro_patterns: number;
  };
  timestamp: string;
}

export interface ExampleQueries {
  semantic_queries: string[];
  structured_query_examples: Array<{
    description: string;
    params: Record<string, any>;
  }>;
  pattern_analysis_examples: Array<{
    query: string;
    lookback_days: number;
    target_assets: string[];
  }>;
}
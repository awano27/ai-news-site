/**
 * 記事データ型定義 v2.0
 * バックエンドのPythonスキーマと対応
 */

export interface Article {
  id: string;
  title: string;
  url: string;
  source: string;
  source_tier: 1 | 2 | 3;
  published_date: string;
  category: 'business' | 'tools' | 'company' | 'research' | 'sns';
  content_summary?: string;
  technical_summary?: string;
  business_implications?: string;
  key_takeaways: string[];
  action_items: string[];
  
  evaluation?: {
    engineer_score: number;
    business_score: number;
    score_breakdown: {
      quality: number;
      relevance: number;
      temporal: number;
      trust: number;
      actionability: number;
    };
  };
  
  technical_metadata?: {
    difficulty_level: 'beginner' | 'intermediate' | 'advanced' | 'research';
    implementation_ready: boolean;
    code_available: boolean;
    github_repo?: string;
    reproducibility_score: number;
  };
  
  business_metadata?: {
    implementation_cost?: 'low' | 'medium' | 'high' | 'enterprise';
    time_to_value?: string;
    competitive_advantage?: string;
  };
  
  entities?: {
    companies: string[];
    technologies: string[];
    concepts: string[];
    products: string[];
  };
  
  related_articles: string[];
  evidence_score: number;
  
  bias_assessment?: {
    neutrality_score: number;
    detected_biases: string[];
  };
}

export interface NewsData {
  generated_at: string;
  system_version: string;
  highlight?: Article;
  categories: {
    engineer: Article[];
    business: Article[];
    research: Article[];
    tools: Article[];
  };
  metadata: {
    total_articles_processed: number;
    total_sources: number;
    evaluation_thresholds: {
      engineer: number;
      business: number;
    };
    quality_indicators: {
      average_evidence_score: number;
      articles_with_code: number;
      articles_with_case_studies: number;
    };
  };
}

export type PersonaType = 'engineer' | 'business';
export type CategoryType = 'engineer' | 'business' | 'research' | 'tools';
export type DifficultyLevel = 'beginner' | 'intermediate' | 'advanced' | 'research';
export type ImplementationCost = 'low' | 'medium' | 'high' | 'enterprise';

export interface SearchFilters {
  persona?: PersonaType;
  category?: CategoryType;
  difficulty_level?: DifficultyLevel;
  implementation_cost?: ImplementationCost;
  min_score?: number;
  date_range?: {
    start: string;
    end: string;
  };
  has_code?: boolean;
  has_case_studies?: boolean;
}

export interface SearchResult {
  article: Article;
  score: number;
  score_breakdown: Record<string, number>;
  rank: number;
}
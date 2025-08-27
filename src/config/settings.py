"""
設定管理システム v2.0
"""
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path


@dataclass
class APIConfig:
    """API設定"""
    gemini_api_key: str = os.getenv('GEMINI_API_KEY', '')
    gemini_model: str = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash-lite')
    gemini_url_context_batch: int = int(os.getenv('GEMINI_URL_CONTEXT_BATCH', '20'))
    
    openai_api_key: str = os.getenv('OPENAI_API_KEY', '')
    openai_model: str = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    
    github_token: str = os.getenv('GITHUB_TOKEN', '')
    x_bearer_token: str = os.getenv('X_BEARER_TOKEN', '')


@dataclass
class ModelConfig:
    """モデル設定"""
    embedding_model: str = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L12-v2')
    reranker_model: str = os.getenv('RERANKER_MODEL', 'cross-encoder/ms-marco-MiniLM-L-12-v2')
    ner_model: str = os.getenv('NER_MODEL', 'dbmdz/bert-large-cased-finetuned-conll03-english')


@dataclass
class DataSourceConfig:
    """データソース設定"""
    tier1_sources: List[str] = field(default_factory=lambda: 
        os.getenv('TIER1_SOURCES', 'arxiv,openai,anthropic,deepmind,papers-with-code').split(',')
    )
    tier2_sources: List[str] = field(default_factory=lambda:
        os.getenv('TIER2_SOURCES', 'github-trending,towards-data-science,techcrunch').split(',')
    )
    x_posts_csv: str = os.getenv('X_POSTS_CSV', '')


@dataclass
class EvaluationConfig:
    """評価設定"""
    # エンジニア向け重み (format: key:value,key:value)
    engineer_weights: Dict[str, float] = field(default_factory=lambda: dict([
        kv.split(':') for kv in os.getenv('ENGINEER_WEIGHT_PRESET', 
        'technical_depth:0.35,implementation:0.25,novelty:0.20,reproducibility:0.15,community_impact:0.05').split(',')
        if ':' in kv
    ]))
    
    # ビジネス向け重み
    business_weights: Dict[str, float] = field(default_factory=lambda: dict([
        kv.split(':') for kv in os.getenv('BUSINESS_WEIGHT_PRESET',
        'business_impact:0.40,roi_potential:0.25,market_validation:0.20,implementation_ease:0.10,strategic_value:0.05').split(',')
        if ':' in kv
    ]))
    
    evaluation_db_url: str = os.getenv('EVALUATION_DB_URL', '')
    recommendation_threshold: float = float(os.getenv('RECOMMENDATION_THRESHOLD', '0.75'))
    noise_filter_threshold: float = float(os.getenv('NOISE_FILTER_THRESHOLD', '0.3'))


@dataclass
class PerformanceConfig:
    """パフォーマンス設定"""
    cache_ttl_seconds: int = int(os.getenv('CACHE_TTL_SECONDS', '3600'))
    vector_index_size: int = int(os.getenv('VECTOR_INDEX_SIZE', '100000'))
    batch_processing_size: int = int(os.getenv('BATCH_PROCESSING_SIZE', '50'))
    parallel_workers: int = int(os.getenv('PARALLEL_WORKERS', '8'))
    global_timeout_sec: int = int(os.getenv('NEWS_GLOBAL_TIMEOUT_SEC', '60'))


@dataclass
class SearchConfig:
    """検索設定"""
    hybrid_weight: float = float(os.getenv('SEARCH_HYBRID_WEIGHT', '0.7'))  # BM25 vs Semantic
    top_k: int = int(os.getenv('SEARCH_TOP_K', '100'))
    rerank_top_k: int = int(os.getenv('RERANK_TOP_K', '20'))


@dataclass
class TemporalConfig:
    """時間的価値設定"""
    half_life_hours: int = int(os.getenv('HALF_LIFE_HOURS', '72'))
    evergreen_boost_factor: float = float(os.getenv('EVERGREEN_BOOST_FACTOR', '1.5'))
    trend_window_days: int = int(os.getenv('TREND_WINDOW_DAYS', '7'))
    max_age_hours: int = int(os.getenv('NEWS_MAX_AGE_HOURS', '24'))


@dataclass
class QualityConfig:
    """品質設定"""
    min_content_length: int = int(os.getenv('MIN_CONTENT_LENGTH', '500'))
    max_summary_length: int = int(os.getenv('MAX_SUMMARY_LENGTH', '300'))
    faithfulness_threshold: float = float(os.getenv('FAITHFULNESS_THRESHOLD', '0.8'))
    bias_detection_sensitivity: str = os.getenv('BIAS_DETECTION_SENSITIVITY', 'medium')


@dataclass
class BasicConfig:
    """基本設定"""
    hours_lookback: int = int(os.getenv('HOURS_LOOKBACK', '24'))
    max_items_per_category: int = int(os.getenv('MAX_ITEMS_PER_CATEGORY', '10'))
    translate_to_ja: bool = bool(int(os.getenv('TRANSLATE_TO_JA', '1')))
    translate_engine: str = os.getenv('TRANSLATE_ENGINE', 'deepl')
    fast_mode: bool = os.getenv('NEWS_FAST_MODE') == '1'


@dataclass
class Settings:
    """統合設定クラス"""
    basic: BasicConfig = field(default_factory=BasicConfig)
    api: APIConfig = field(default_factory=APIConfig)
    models: ModelConfig = field(default_factory=ModelConfig)
    data_sources: DataSourceConfig = field(default_factory=DataSourceConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    temporal: TemporalConfig = field(default_factory=TemporalConfig)
    quality: QualityConfig = field(default_factory=QualityConfig)
    
    # パス設定
    root_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent)
    sources_yaml: Path = field(init=False)
    news_dir: Path = field(init=False)
    output_dir: Path = field(init=False)
    
    def __post_init__(self):
        """パス設定の初期化"""
        self.sources_yaml = self.root_dir / 'sources.yaml'
        self.news_dir = self.root_dir / 'news'
        self.output_dir = self.root_dir / 'dist'
        
        # ディレクトリ作成
        self.news_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
    
    def validate(self) -> List[str]:
        """設定の妥当性チェック"""
        errors = []
        
        # 必須API設定のチェック
        if not self.api.gemini_api_key and not self.basic.fast_mode:
            errors.append("GEMINI_API_KEY is required unless FAST_MODE is enabled")
        
        # ファイル存在チェック
        if not self.sources_yaml.exists():
            errors.append(f"Sources file not found: {self.sources_yaml}")
        
        # 数値範囲チェック
        if not 0 <= self.search.hybrid_weight <= 1:
            errors.append("SEARCH_HYBRID_WEIGHT must be between 0 and 1")
        
        if self.evaluation.recommendation_threshold < 0 or self.evaluation.recommendation_threshold > 1:
            errors.append("RECOMMENDATION_THRESHOLD must be between 0 and 1")
        
        return errors


# グローバル設定インスタンス
settings = Settings()

# 設定の妥当性チェック
validation_errors = settings.validate()
if validation_errors:
    print("⚠️  Configuration warnings:")
    for error in validation_errors:
        print(f"   - {error}")
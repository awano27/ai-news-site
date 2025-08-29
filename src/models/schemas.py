"""
データスキーマ v2.0 - 拡張記事スキーマの定義
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum


class SourceTier(Enum):
    """情報源ティア"""
    TIER_1 = 1  # 最重要ソース
    TIER_2 = 2  # 重要ソース
    TIER_3 = 3  # 補助ソース


class DifficultyLevel(Enum):
    """技術的難易度"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    RESEARCH = "research"


class ImplementationCost(Enum):
    """実装コスト"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ENTERPRISE = "enterprise"


class FactCheckStatus(Enum):
    """ファクトチェック状態"""
    VERIFIED = "verified"
    PARTIAL = "partial"
    UNVERIFIED = "unverified"


class EvidenceType(Enum):
    """根拠タイプ"""
    PAPER = "paper"
    PRESS_RELEASE = "press_release"
    DOCUMENTATION = "documentation"
    CODE = "code"


@dataclass
class BenchmarkResult:
    """ベンチマーク結果"""
    dataset: str
    metric: str
    score: float
    sota_comparison: float  # SOTA比較 (%)


@dataclass
class ComputeRequirements:
    """計算リソース要件"""
    gpu: Optional[str] = None
    memory: Optional[str] = None
    training_time: Optional[str] = None


@dataclass
class TechnicalMetadata:
    """技術的メタデータ（エンジニア向け）"""
    difficulty_level: DifficultyLevel
    implementation_ready: bool = False
    code_available: bool = False
    paper_link: Optional[str] = None
    github_repo: Optional[str] = None
    colab_notebook: Optional[str] = None
    benchmark_results: List[BenchmarkResult] = field(default_factory=list)
    reproducibility_score: float = 0.0
    dependencies: List[str] = field(default_factory=list)
    compute_requirements: Optional[ComputeRequirements] = None


@dataclass
class ROIIndicators:
    """ROI指標"""
    payback_period: Optional[str] = None
    cost_reduction: Optional[str] = None
    revenue_increase: Optional[str] = None


@dataclass
class CaseStudy:
    """事例研究"""
    company: str
    industry: str
    results: str
    timeline: str


@dataclass
class FundingInfo:
    """資金調達情報"""
    amount: Optional[str] = None
    round: Optional[str] = None
    investors: List[str] = field(default_factory=list)


@dataclass
class BusinessMetadata:
    """ビジネスメタデータ（ビジネスマン向け）"""
    market_size: Optional[str] = None
    growth_rate: Optional[float] = None
    roi_indicators: Optional[ROIIndicators] = None
    case_studies: List[CaseStudy] = field(default_factory=list)
    implementation_cost: Optional[ImplementationCost] = None
    time_to_value: Optional[str] = None
    competitive_advantage: Optional[str] = None
    funding_info: Optional[FundingInfo] = None


@dataclass
class ScoreBreakdown:
    """スコア内訳"""
    quality: float
    relevance: float
    temporal: float
    trust: float
    actionability: float


@dataclass
class UserRatings:
    """ユーザー評価"""
    likes: int = 0
    stars: float = 0.0
    bookmarks: int = 0
    feedback_count: int = 0


@dataclass
class EvaluationMetrics:
    """評価メトリクス"""
    engineer_score: float
    business_score: float
    score_breakdown: ScoreBreakdown
    user_ratings: Optional[UserRatings] = None
    expert_validation: bool = False
    fact_check_status: FactCheckStatus = FactCheckStatus.UNVERIFIED


@dataclass
class ArticleEntities:
    """エンティティ情報"""
    companies: List[str] = field(default_factory=list)
    technologies: List[str] = field(default_factory=list)
    people: List[str] = field(default_factory=list)
    concepts: List[str] = field(default_factory=list)
    products: List[str] = field(default_factory=list)


@dataclass
class Relationships:
    """関連性グラフ"""
    related_articles: List[str] = field(default_factory=list)
    prerequisite_articles: List[str] = field(default_factory=list)
    follow_up_articles: List[str] = field(default_factory=list)


@dataclass
class EvidenceSource:
    """根拠ソース"""
    type: EvidenceType
    url: str
    credibility_score: float


@dataclass
class Evidence:
    """根拠と信頼性"""
    primary_sources: List[EvidenceSource] = field(default_factory=list)
    citations: List[str] = field(default_factory=list)
    supporting_data: List[Any] = field(default_factory=list)


@dataclass
class BiasAssessment:
    """バイアス評価"""
    detected_biases: List[str] = field(default_factory=list)
    neutrality_score: float = 0.0
    transparency_score: float = 0.0


@dataclass
class Summaries:
    """要約と洞察"""
    executive_summary: Optional[str] = None
    technical_summary: Optional[str] = None
    business_implications: Optional[str] = None
    key_takeaways: List[str] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)


@dataclass
class Faithfulness:
    """忠実性チェック"""
    summary_accuracy: float = 0.0
    evidence_links: List[str] = field(default_factory=list)
    consistency_score: float = 0.0


@dataclass
class Article:
    """記事スキーマ v2.0"""
    # 基本情報
    id: str
    title: str
    url: str
    source: str
    source_tier: SourceTier
    
    # 時間情報
    published_date: datetime
    event_date: Optional[datetime] = None
    crawled_date: Optional[datetime] = None
    freshness_score: float = 0.0
    evergreen_score: float = 0.0
    
    # 技術的メタデータ
    technical: Optional[TechnicalMetadata] = None
    
    # ビジネスメタデータ
    business: Optional[BusinessMetadata] = None
    
    # 評価メトリクス
    evaluation: Optional[EvaluationMetrics] = None
    
    # エンティティと関連性
    entities: Optional[ArticleEntities] = None
    relationships: Optional[Relationships] = None
    
    # 根拠と信頼性
    evidence: Optional[Evidence] = None
    
    # バイアス評価
    bias_assessment: Optional[BiasAssessment] = None
    
    # 要約と洞察
    summaries: Optional[Summaries] = None
    
    # 忠実性チェック
    faithfulness: Optional[Faithfulness] = None
    
    # 追加フィールド
    content: Optional[str] = None  # 記事本文
    category: Optional[str] = None  # カテゴリ
    tags: List[str] = field(default_factory=list)  # タグ


@dataclass
class PersonaWeights:
    """ペルソナ別重み設定"""
    technical_depth: float = 0.0
    implementation: float = 0.0
    novelty: float = 0.0
    reproducibility: float = 0.0
    community_impact: float = 0.0
    business_impact: float = 0.0
    roi_potential: float = 0.0
    market_validation: float = 0.0
    implementation_ease: float = 0.0
    strategic_value: float = 0.0


@dataclass
class EngineerPersona:
    """エンジニアペルソナ設定"""
    weights: PersonaWeights = field(default_factory=lambda: PersonaWeights(
        technical_depth=0.35,
        implementation=0.25,
        novelty=0.20,
        reproducibility=0.15,
        community_impact=0.05
    ))


@dataclass
class BusinessPersona:
    """ビジネスマンペルソナ設定"""
    weights: PersonaWeights = field(default_factory=lambda: PersonaWeights(
        business_impact=0.40,
        roi_potential=0.25,
        market_validation=0.20,
        implementation_ease=0.10,
        strategic_value=0.05
    ))
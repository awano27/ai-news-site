"""
多層評価システム v2.0
5つの独立した評価軸による多角的スコアリング
"""
import math
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import asdict

from ..models.schemas import (
    Article, PersonaWeights, ScoreBreakdown, 
    EngineerPersona, BusinessPersona
)
from ..config.settings import settings


class MultiLayerEvaluator:
    """多層評価エンジン"""
    
    def __init__(self):
        self.engineer_persona = EngineerPersona()
        self.business_persona = BusinessPersona()
        
        # キーワード辞書
        self._load_keywords()
    
    def _load_keywords(self):
        """評価用キーワード辞書の読み込み"""
        # 技術的深度キーワード
        self.technical_keywords = {
            'high': [
                'algorithm', 'implementation', 'architecture', 'neural network',
                'transformer', 'attention', 'backpropagation', 'optimization',
                'gradient', 'loss function', 'hyperparameter', 'regularization',
                'dropout', 'batch normalization', 'embedding', 'encoder', 'decoder'
            ],
            'medium': [
                'model', 'training', 'dataset', 'accuracy', 'precision', 'recall',
                'f1-score', 'classification', 'regression', 'clustering',
                'supervised', 'unsupervised', 'reinforcement'
            ],
            'low': [
                'AI', 'machine learning', 'deep learning', 'artificial intelligence',
                'prediction', 'automation', 'data science', 'analytics'
            ]
        }
        
        # ビジネス影響度キーワード
        self.business_keywords = {
            'high': [
                'revenue', 'profit', 'ROI', 'cost reduction', 'efficiency',
                'productivity', 'competitive advantage', 'market share',
                'disruption', 'transformation', 'scaling', 'automation',
                'enterprise', 'billion', 'million'
            ],
            'medium': [
                'business', 'customer', 'user experience', 'workflow',
                'process', 'optimization', 'solution', 'platform',
                'adoption', 'deployment', 'integration'
            ],
            'low': [
                'application', 'use case', 'example', 'demo', 'prototype',
                'concept', 'idea', 'potential', 'future'
            ]
        }
        
        # 新規性キーワード
        self.novelty_keywords = [
            'breakthrough', 'novel', 'new', 'first', 'pioneer', 'innovative',
            'unprecedented', 'state-of-the-art', 'SOTA', 'record', 'best',
            'improved', 'better', 'superior', 'advanced', 'cutting-edge'
        ]
        
        # 実装可能性キーワード
        self.implementation_keywords = [
            'code', 'github', 'repository', 'implementation', 'library',
            'framework', 'API', 'tutorial', 'guide', 'documentation',
            'open source', 'available', 'download', 'install', 'usage'
        ]
    
    def evaluate_article(self, article: Article, persona: str = 'engineer') -> Dict:
        """記事の有益性を多層的に評価"""
        
        # Layer 1: コンテンツ品質スコア
        quality_score = self._assess_quality(article)
        
        # Layer 2: ペルソナ別関連性スコア
        relevance_score = self._calculate_relevance(article, persona)
        
        # Layer 3: 時間的価値スコア
        temporal_score = self._calculate_temporal_value(article)
        
        # Layer 4: 信頼性スコア（E-E-A-T準拠）
        trust_score = self._calculate_trust_score(article)
        
        # Layer 5: アクショナビリティスコア
        action_score = self._calculate_actionability(article, persona)
        
        # 重み付き合計スコア
        total_score = self._weighted_sum(
            quality_score, relevance_score, 
            temporal_score, trust_score, action_score
        )
        
        return {
            'total_score': total_score,
            'breakdown': ScoreBreakdown(
                quality=quality_score,
                relevance=relevance_score,
                temporal=temporal_score,
                trust=trust_score,
                actionability=action_score
            ),
            'recommendation': self._generate_recommendation(total_score, persona)
        }
    
    def _assess_quality(self, article: Article) -> float:
        """Layer 1: コンテンツ品質評価"""
        score = 0.0
        
        # 内容の長さと構造
        if article.content:
            content_length = len(article.content)
            if content_length >= settings.quality.min_content_length:
                score += 0.2
            
            # 構造化された内容の有無
            if any(marker in article.content.lower() for marker in 
                   ['abstract', 'introduction', 'methodology', 'results', 'conclusion']):
                score += 0.1
        
        # タイトルの情報量
        title_words = len(article.title.split())
        if 5 <= title_words <= 15:  # 適切な長さ
            score += 0.1
        
        # 引用・参照の有無
        if article.evidence and article.evidence.citations:
            score += 0.2
        
        # 図表・視覚的要素
        if article.content and any(indicator in article.content.lower() for indicator in 
                                 ['figure', 'table', 'chart', 'graph', 'image']):
            score += 0.1
        
        # 専門用語の適切な使用
        tech_terms = sum(1 for keyword_list in self.technical_keywords.values() 
                        for keyword in keyword_list 
                        if keyword.lower() in article.title.lower() or 
                        (article.content and keyword.lower() in article.content.lower()))
        if tech_terms >= 3:
            score += 0.2
        elif tech_terms >= 1:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_relevance(self, article: Article, persona: str) -> float:
        """Layer 2: ペルソナ別関連性スコア"""
        if persona == 'engineer':
            return self._engineer_relevance(article)
        elif persona == 'business':
            return self._business_relevance(article)
        else:
            return 0.0
    
    def _engineer_relevance(self, article: Article) -> float:
        """エンジニア向け関連性評価"""
        score = 0.0
        weights = self.engineer_persona.weights
        
        text = f"{article.title} {article.content or ''}"
        text_lower = text.lower()
        
        # 技術的深度
        tech_score = 0.0
        for level, keywords in self.technical_keywords.items():
            weight = {'high': 1.0, 'medium': 0.7, 'low': 0.4}[level]
            matches = sum(1 for kw in keywords if kw in text_lower)
            tech_score += matches * weight
        tech_score = min(tech_score / 10, 1.0)  # 正規化
        score += tech_score * weights.technical_depth
        
        # 実装可能性
        impl_score = sum(1 for kw in self.implementation_keywords if kw in text_lower)
        impl_score = min(impl_score / 5, 1.0)
        score += impl_score * weights.implementation
        
        # 新規性
        novelty_score = sum(1 for kw in self.novelty_keywords if kw in text_lower)
        novelty_score = min(novelty_score / 3, 1.0)
        score += novelty_score * weights.novelty
        
        # 再現性（メタデータから）
        reprod_score = 0.0
        if article.technical:
            if article.technical.code_available:
                reprod_score += 0.4
            if article.technical.github_repo:
                reprod_score += 0.3
            if article.technical.colab_notebook:
                reprod_score += 0.3
        score += reprod_score * weights.reproducibility
        
        # コミュニティ影響（エンティティから推定）
        community_score = 0.0
        if article.entities:
            # 有名な技術・プロダクトへの言及
            famous_techs = ['pytorch', 'tensorflow', 'transformers', 'bert', 'gpt']
            community_score = sum(0.2 for tech in famous_techs 
                                if any(tech in entity.lower() 
                                      for entity in article.entities.technologies))
        score += min(community_score, 1.0) * weights.community_impact
        
        return min(score, 1.0)
    
    def _business_relevance(self, article: Article) -> float:
        """ビジネス向け関連性評価"""
        score = 0.0
        weights = self.business_persona.weights
        
        text = f"{article.title} {article.content or ''}"
        text_lower = text.lower()
        
        # ビジネス影響度
        biz_score = 0.0
        for level, keywords in self.business_keywords.items():
            weight = {'high': 1.0, 'medium': 0.7, 'low': 0.4}[level]
            matches = sum(1 for kw in keywords if kw in text_lower)
            biz_score += matches * weight
        biz_score = min(biz_score / 8, 1.0)
        score += biz_score * weights.business_impact
        
        # ROI可能性（ビジネスメタデータから）
        roi_score = 0.0
        if article.business and article.business.roi_indicators:
            roi = article.business.roi_indicators
            if roi.cost_reduction:
                roi_score += 0.4
            if roi.revenue_increase:
                roi_score += 0.4
            if roi.payback_period:
                roi_score += 0.2
        score += roi_score * weights.roi_potential
        
        # 市場検証（事例研究から）
        market_score = 0.0
        if article.business and article.business.case_studies:
            market_score = min(len(article.business.case_studies) * 0.3, 1.0)
        score += market_score * weights.market_validation
        
        # 導入容易性
        ease_score = 0.0
        if article.business:
            cost_scores = {
                'low': 1.0, 'medium': 0.7, 'high': 0.4, 'enterprise': 0.2
            }
            if article.business.implementation_cost:
                ease_score = cost_scores.get(article.business.implementation_cost.value, 0.5)
        score += ease_score * weights.implementation_ease
        
        # 戦略的価値
        strategic_score = 0.0
        if article.business and article.business.competitive_advantage:
            strategic_score = 0.8
        score += strategic_score * weights.strategic_value
        
        return min(score, 1.0)
    
    def _calculate_temporal_value(self, article: Article) -> float:
        """Layer 3: 時間的価値の計算"""
        now = datetime.now()
        pub_date = article.published_date
        
        # 1. 鮮度スコア（指数減衰）
        hours_since_publish = (now - pub_date).total_seconds() / 3600
        half_life_hours = settings.temporal.half_life_hours
        freshness = math.exp(-hours_since_publish * math.log(2) / half_life_hours)
        
        # 2. 持続的価値（エバーグリーン度）
        evergreen_score = self._assess_evergreen_potential(article)
        
        # 3. イベント駆動価値
        event_relevance = self._calculate_event_relevance(article)
        
        # 4. トレンド同期性
        trend_alignment = self._measure_trend_alignment(article)
        
        # 重み付き平均
        return (freshness * 0.3 + evergreen_score * 0.3 + 
                event_relevance * 0.25 + trend_alignment * 0.15)
    
    def _assess_evergreen_potential(self, article: Article) -> float:
        """エバーグリーン度の評価"""
        score = 0.0
        
        # 基礎的な技術・概念への言及
        evergreen_topics = [
            'algorithm', 'data structure', 'optimization', 'theory',
            'framework', 'methodology', 'principle', 'fundamental'
        ]
        
        text = f"{article.title} {article.content or ''}".lower()
        matches = sum(1 for topic in evergreen_topics if topic in text)
        score = min(matches / 3, 1.0)
        
        # 特定の製品・バージョンに依存しない内容
        version_indicators = ['v1', 'v2', 'version', 'update', 'release', 'beta']
        if not any(indicator in text for indicator in version_indicators):
            score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_event_relevance(self, article: Article) -> float:
        """イベント駆動価値の計算"""
        # 重要なイベント（学会、製品発表など）との関連性
        important_events = [
            'neurips', 'icml', 'iclr', 'aaai', 'ijcai', 'acl', 'emnlp',
            'conference', 'summit', 'keynote', 'announcement', 'release'
        ]
        
        text = f"{article.title} {article.content or ''}".lower()
        matches = sum(1 for event in important_events if event in text)
        
        return min(matches / 2, 1.0)
    
    def _measure_trend_alignment(self, article: Article) -> float:
        """トレンド同期性の測定"""
        # 現在のAIトレンドキーワード
        trend_keywords = [
            'llm', 'large language model', 'gpt', 'transformer',
            'generative ai', 'multimodal', 'foundation model',
            'fine-tuning', 'rag', 'retrieval augmented'
        ]
        
        text = f"{article.title} {article.content or ''}".lower()
        matches = sum(1 for trend in trend_keywords if trend in text)
        
        return min(matches / 3, 1.0)
    
    def _calculate_trust_score(self, article: Article) -> float:
        """Layer 4: 信頼性スコア（E-E-A-T準拠）"""
        score = 0.0
        
        # Experience（経験）
        if article.entities and article.entities.people:
            # 著名な研究者・専門家の言及
            score += 0.2
        
        # Expertise（専門性）
        if article.source_tier.value == 1:  # Tier 1ソース
            score += 0.3
        elif article.source_tier.value == 2:  # Tier 2ソース
            score += 0.2
        
        # Authoritativeness（権威性）
        if article.evidence and article.evidence.primary_sources:
            score += 0.2
        
        # Trustworthiness（信頼性）
        if article.evidence and len(article.evidence.citations) >= 3:
            score += 0.2
        
        # バイアス評価による調整
        if article.bias_assessment:
            bias_penalty = len(article.bias_assessment.detected_biases) * 0.1
            score = max(0, score - bias_penalty)
        
        return min(score, 1.0)
    
    def _calculate_actionability(self, article: Article, persona: str) -> float:
        """Layer 5: アクショナビリティスコア"""
        score = 0.0
        
        # 具体的なアクションアイテムの有無
        if article.summaries and article.summaries.action_items:
            score += 0.3
        
        # 実装可能な情報の有無
        if persona == 'engineer':
            if article.technical:
                if article.technical.code_available:
                    score += 0.3
                if article.technical.implementation_ready:
                    score += 0.2
                if article.technical.dependencies:
                    score += 0.1
        
        elif persona == 'business':
            if article.business:
                if article.business.case_studies:
                    score += 0.3
                if article.business.roi_indicators:
                    score += 0.2
                if article.business.time_to_value:
                    score += 0.1
        
        # 次のステップの明確性
        if article.summaries and article.summaries.key_takeaways:
            score += 0.1
        
        return min(score, 1.0)
    
    def _weighted_sum(self, quality: float, relevance: float, 
                     temporal: float, trust: float, action: float) -> float:
        """重み付き合計の計算"""
        # デフォルトの重み
        weights = {
            'quality': 0.25,
            'relevance': 0.30,
            'temporal': 0.15,
            'trust': 0.20,
            'action': 0.10
        }
        
        return (quality * weights['quality'] + 
                relevance * weights['relevance'] +
                temporal * weights['temporal'] + 
                trust * weights['trust'] +
                action * weights['action'])
    
    def _generate_recommendation(self, total_score: float, persona: str) -> str:
        """推奨レベルの生成"""
        if total_score >= 0.8:
            return "必読" if persona == 'engineer' else "重要"
        elif total_score >= 0.6:
            return "推奨" if persona == 'engineer' else "注目"
        elif total_score >= 0.4:
            return "参考" if persona == 'engineer' else "検討"
        else:
            return "スキップ可" if persona == 'engineer' else "低優先"
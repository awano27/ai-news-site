"""
Daily AI News System v2.0 - メインビルドスクリプト
多層評価システムとハイブリッド検索を統合した高度なニュース分析システム
"""
import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

from .config.settings import settings
from .models.schemas import Article, SourceTier
from .collectors.gemini_analyzer import GeminiURLAnalyzer
from .evaluators.multi_layer_evaluator import MultiLayerEvaluator
from .search.hybrid_search import HybridSearchEngine
from .utils.simple_logging import setup_logging
from .collectors.source_manager import SourceManager

# ロギング設定
logger = setup_logging()


class NewsSystemV2:
    """Daily AI News System v2.0 メインクラス"""
    
    def __init__(self):
        self.gemini_analyzer = GeminiURLAnalyzer()
        self.evaluator = MultiLayerEvaluator()
        self.search_engine = HybridSearchEngine()
        self.source_manager = SourceManager()
        
        self.articles: List[Article] = []
        self.processed_urls = set()
    
    async def run_full_pipeline(self) -> Dict[str, Any]:
        """完全なパイプラインの実行"""
        logger.info("🚀 Starting Daily AI News System v2.0")
        
        try:
            # 1. 情報収集
            logger.info("📡 Phase 1: Collecting information from sources")
            raw_articles = await self._collect_from_sources()
            logger.info(f"Collected {len(raw_articles)} raw articles")
            
            # 2. URL Context分析（Gemini）
            logger.info("🧠 Phase 2: Analyzing content with Gemini")
            analyzed_articles = await self._analyze_with_gemini(raw_articles)
            logger.info(f"Analyzed {len(analyzed_articles)} articles")
            
            # 3. 多層評価
            logger.info("⚡ Phase 3: Multi-layer evaluation")
            evaluated_articles = await self._evaluate_articles(analyzed_articles)
            logger.info(f"Evaluated {len(evaluated_articles)} articles")
            
            # 4. 検索エンジンの学習
            logger.info("🔍 Phase 4: Training hybrid search engine")
            self.search_engine.fit(evaluated_articles)
            
            # 5. 記事の関連付けと最適化
            logger.info("🔗 Phase 5: Article relationship building")
            optimized_articles = await self._build_relationships(evaluated_articles)
            
            # 6. ペルソナ別選別とランキング
            logger.info("👥 Phase 6: Persona-based filtering and ranking")
            engineer_articles = self._filter_and_rank(optimized_articles, 'engineer')
            business_articles = self._filter_and_rank(optimized_articles, 'business')
            
            # 7. 出力生成
            logger.info("📄 Phase 7: Generating output")
            output_data = self._generate_output_data(
                engineer_articles, business_articles, optimized_articles
            )
            
            # 8. ファイル書き出し
            await self._write_output_files(output_data)
            
            logger.info("✅ Pipeline completed successfully")
            
            return {
                'status': 'success',
                'processed_articles': len(optimized_articles),
                'engineer_articles': len(engineer_articles),
                'business_articles': len(business_articles),
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e),
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
    
    async def _collect_from_sources(self) -> List[Dict[str, Any]]:
        """情報源からの収集"""
        return await self.source_manager.collect_all_sources()
    
    async def _analyze_with_gemini(self, raw_articles: List[Dict[str, Any]]) -> List[Article]:
        """Gemini URL Context分析"""
        analyzed_articles = []
        
        # URLリストを準備
        urls = [article['url'] for article in raw_articles if 'url' in article]
        
        if not urls:
            logger.warning("No URLs found for analysis")
            return []
        
        # バッチ分析
        logger.info(f"Analyzing {len(urls)} URLs with Gemini")
        analysis_results = await self.gemini_analyzer.analyze_batch(urls)
        
        # 結果を記事オブジェクトに変換
        for raw_article in raw_articles:
            url = raw_article.get('url')
            if not url or url in self.processed_urls:
                continue
            
            analysis_data = analysis_results.get(url)
            if not analysis_data:
                logger.warning(f"No analysis data for URL: {url}")
                continue
            
            try:
                # 記事オブジェクトに変換
                article = self.gemini_analyzer.convert_to_article_schema(url, analysis_data)
                
                # 元データから追加情報をマージ
                if 'published_date' in raw_article:
                    article.published_date = raw_article['published_date']
                if 'source' in raw_article:
                    article.source = raw_article['source']
                if 'source_tier' in raw_article:
                    article.source_tier = SourceTier(raw_article['source_tier'])
                
                analyzed_articles.append(article)
                self.processed_urls.add(url)
                
            except Exception as e:
                logger.error(f"Error converting article {url}: {e}")
                continue
        
        return analyzed_articles
    
    async def _evaluate_articles(self, articles: List[Article]) -> List[Article]:
        """記事の多層評価"""
        evaluated_articles = []
        
        for article in articles:
            try:
                # エンジニア向け評価
                engineer_eval = self.evaluator.evaluate_article(article, 'engineer')
                
                # ビジネス向け評価
                business_eval = self.evaluator.evaluate_article(article, 'business')
                
                # 評価結果を記事に保存
                from .models.schemas import EvaluationMetrics, UserRatings
                
                article.evaluation = EvaluationMetrics(
                    engineer_score=engineer_eval['total_score'],
                    business_score=business_eval['total_score'],
                    score_breakdown=engineer_eval['breakdown'],
                    user_ratings=UserRatings()
                )
                
                evaluated_articles.append(article)
                
            except Exception as e:
                logger.error(f"Error evaluating article {article.url}: {e}")
                continue
        
        return evaluated_articles
    
    async def _build_relationships(self, articles: List[Article]) -> List[Article]:
        """記事間の関連性構築"""
        if not articles:
            return articles
        
        # 関連記事の検索
        for i, article in enumerate(articles):
            try:
                # 記事のキーワードを使って関連記事を検索
                if article.summaries and article.summaries.key_takeaways:
                    query = " ".join(article.summaries.key_takeaways[:3])
                else:
                    query = article.title
                
                # 検索実行
                search_results = self.search_engine.search(query, top_k=5)
                
                # 自分自身を除いた関連記事のIDを設定
                related_ids = []
                for result in search_results:
                    if result.article.id != article.id:
                        related_ids.append(result.article.id)
                
                # 関連性情報を更新
                if not article.relationships:
                    from .models.schemas import Relationships
                    article.relationships = Relationships()
                
                article.relationships.related_articles = related_ids[:3]
                
            except Exception as e:
                logger.error(f"Error building relationships for {article.url}: {e}")
                continue
        
        return articles
    
    def _filter_and_rank(self, articles: List[Article], persona: str) -> List[Article]:
        """ペルソナ別フィルタリングとランキング"""
        # スコアでフィルタリング
        threshold = settings.evaluation.recommendation_threshold
        
        filtered_articles = []
        for article in articles:
            if not article.evaluation:
                continue
            
            score = (article.evaluation.engineer_score if persona == 'engineer' 
                    else article.evaluation.business_score)
            
            if score >= threshold:
                filtered_articles.append(article)
        
        # スコア順でソート
        filtered_articles.sort(
            key=lambda x: (
                x.evaluation.engineer_score if persona == 'engineer' 
                else x.evaluation.business_score
            ), 
            reverse=True
        )
        
        # 上位記事のみ返す
        max_items = settings.basic.max_items_per_category
        return filtered_articles[:max_items * 2]  # 余裕を持って多めに
    
    def _generate_output_data(self, engineer_articles: List[Article], 
                            business_articles: List[Article], 
                            all_articles: List[Article]) -> Dict[str, Any]:
        """出力データの生成"""
        
        def article_to_dict(article: Article) -> Dict[str, Any]:
            """記事をJSONシリアライズ可能な辞書に変換"""
            return {
                'id': article.id,
                'title': article.title,
                'url': article.url,
                'source': article.source,
                'source_tier': article.source_tier.value,
                'published_date': article.published_date.isoformat(),
                'category': article.category,
                'content_summary': (
                    article.summaries.executive_summary 
                    if article.summaries else article.content
                ),
                'technical_summary': (
                    article.summaries.technical_summary 
                    if article.summaries else None
                ),
                'business_implications': (
                    article.summaries.business_implications 
                    if article.summaries else None
                ),
                'key_takeaways': (
                    article.summaries.key_takeaways 
                    if article.summaries else []
                ),
                'action_items': (
                    article.summaries.action_items 
                    if article.summaries else []
                ),
                'evaluation': {
                    'engineer_score': article.evaluation.engineer_score,
                    'business_score': article.evaluation.business_score,
                    'score_breakdown': {
                        'quality': article.evaluation.score_breakdown.quality,
                        'relevance': article.evaluation.score_breakdown.relevance,
                        'temporal': article.evaluation.score_breakdown.temporal,
                        'trust': article.evaluation.score_breakdown.trust,
                        'actionability': article.evaluation.score_breakdown.actionability,
                    }
                } if article.evaluation else None,
                'technical_metadata': {
                    'difficulty_level': article.technical.difficulty_level.value,
                    'implementation_ready': article.technical.implementation_ready,
                    'code_available': article.technical.code_available,
                    'github_repo': article.technical.github_repo,
                    'reproducibility_score': article.technical.reproducibility_score
                } if article.technical else None,
                'business_metadata': {
                    'implementation_cost': (
                        article.business.implementation_cost.value 
                        if article.business.implementation_cost else None
                    ),
                    'time_to_value': article.business.time_to_value,
                    'competitive_advantage': article.business.competitive_advantage
                } if article.business else None,
                'entities': {
                    'companies': article.entities.companies,
                    'technologies': article.entities.technologies,
                    'concepts': article.entities.concepts,
                    'products': article.entities.products
                } if article.entities else None,
                'related_articles': (
                    article.relationships.related_articles 
                    if article.relationships else []
                ),
                'evidence_score': (
                    len(article.evidence.primary_sources) * 0.2 + 
                    len(article.evidence.citations) * 0.1
                    if article.evidence else 0.0
                ),
                'bias_assessment': {
                    'neutrality_score': article.bias_assessment.neutrality_score,
                    'detected_biases': article.bias_assessment.detected_biases
                } if article.bias_assessment else None
            } if article.evaluation else None
        
        # ハイライト記事の選定
        highlight_article = None
        if all_articles:
            # 最も総合スコアの高い記事
            best_article = max(
                all_articles, 
                key=lambda x: (
                    (x.evaluation.engineer_score + x.evaluation.business_score) / 2
                    if x.evaluation else 0
                )
            )
            if best_article.evaluation and (best_article.evaluation.engineer_score + best_article.evaluation.business_score) / 2 >= 0.7:
                highlight_article = article_to_dict(best_article)
        
        # カテゴリ別分類
        categories = {
            'engineer': [article_to_dict(a) for a in engineer_articles if article_to_dict(a)],
            'business': [article_to_dict(a) for a in business_articles if article_to_dict(a)],
            'research': [],
            'tools': []
        }
        
        # カテゴリ別に分類（詳細）
        for article in all_articles:
            article_dict = article_to_dict(article)
            if not article_dict:
                continue
                
            if article.category == 'research' and len(categories['research']) < settings.basic.max_items_per_category:
                categories['research'].append(article_dict)
            elif article.category == 'tools' and len(categories['tools']) < settings.basic.max_items_per_category:
                categories['tools'].append(article_dict)
        
        return {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'system_version': '2.0',
            'highlight': highlight_article,
            'categories': categories,
            'metadata': {
                'total_articles_processed': len(all_articles),
                'total_sources': len(set(a.source for a in all_articles)),
                'evaluation_thresholds': {
                    'engineer': settings.evaluation.recommendation_threshold,
                    'business': settings.evaluation.recommendation_threshold
                },
                'quality_indicators': {
                    'average_evidence_score': sum(
                        len(a.evidence.primary_sources) if a.evidence else 0 
                        for a in all_articles
                    ) / len(all_articles) if all_articles else 0,
                    'articles_with_code': sum(
                        1 for a in all_articles 
                        if a.technical and a.technical.code_available
                    ),
                    'articles_with_case_studies': sum(
                        1 for a in all_articles 
                        if a.business and a.business.case_studies
                    )
                }
            }
        }
    
    async def _write_output_files(self, output_data: Dict[str, Any]):
        """出力ファイルの書き出し"""
        # latest.jsonの出力
        latest_path = settings.news_dir / 'latest.json'
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        # 日付別ファイルの出力
        today = datetime.now().strftime('%Y-%m-%d')
        daily_path = settings.news_dir / f'{today}.json'
        with open(daily_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Output files written: {latest_path}, {daily_path}")


async def main():
    """メイン実行関数"""
    system = NewsSystemV2()
    result = await system.run_full_pipeline()
    
    if result['status'] == 'success':
        print("✅ Daily AI News System v2.0 completed successfully!")
        print(f"   - Processed: {result['processed_articles']} articles")
        print(f"   - Engineer articles: {result['engineer_articles']}")
        print(f"   - Business articles: {result['business_articles']}")
    else:
        print(f"❌ Pipeline failed: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
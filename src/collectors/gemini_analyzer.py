"""
Gemini URL Context分析システム v2.0
URLから直接コンテンツを分析し、構造化データを抽出
"""
import asyncio
import json
import logging
import re
from typing import Dict, List, Optional, Any
from dataclasses import asdict
from urllib.parse import urlparse

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from ..models.schemas import (
    Article, TechnicalMetadata, BusinessMetadata, 
    ArticleEntities, Evidence, Summaries, BenchmarkResult,
    ComputeRequirements, ROIIndicators, CaseStudy, FundingInfo,
    EvidenceSource, EvidenceType, DifficultyLevel, ImplementationCost
)
from ..config.settings import settings

logger = logging.getLogger(__name__)


def _validate_url(url: str) -> bool:
    """Validate URL format and scheme"""
    if not url or not isinstance(url, str):
        return False
    try:
        parsed = urlparse(url)
        # Only allow http and https schemes
        if parsed.scheme not in ('http', 'https'):
            return False
        # Must have a network location (domain)
        if not parsed.netloc:
            return False
        # Block localhost and private IPs (basic SSRF protection)
        if parsed.netloc.lower() in ('localhost', '127.0.0.1', '0.0.0.0', '[::1]'):
            return False
        if parsed.netloc.startswith('192.168.') or parsed.netloc.startswith('10.') or parsed.netloc.startswith('172.'):
            return False
        return True
    except Exception:
        return False


class GeminiURLAnalyzer:
    """Gemini URL Context分析エンジン"""

    def __init__(self):
        if not settings.api.gemini_api_key:
            logger.warning("GEMINI_API_KEY not set, URL analysis will be disabled")
            self.client = None
            return
        
        genai.configure(api_key=settings.api.gemini_api_key)
        self.client = genai.GenerativeModel(
            model_name=settings.api.gemini_model,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        
        # 構造化データ抽出用のプロンプトテンプレート
        self.analysis_prompt = self._create_analysis_prompt()
    
    def _create_analysis_prompt(self) -> str:
        """分析用プロンプトの生成"""
        return """
あなたはAI技術記事の専門アナリストです。与えられたURLのコンテンツを詳細に分析し、以下のJSON形式で構造化データを抽出してください。

記事の内容を基に、以下の情報を可能な限り正確に抽出してください：

```json
{
  "basic_info": {
    "title": "記事タイトル",
    "content_summary": "記事の主要な内容（500文字以内）",
    "category": "business|tools|company|research",
    "language": "ja|en"
  },
  "technical_metadata": {
    "difficulty_level": "beginner|intermediate|advanced|research",
    "implementation_ready": boolean,
    "code_available": boolean,
    "paper_link": "論文リンク（あれば）",
    "github_repo": "GitHubリポジトリ（あれば）",
    "colab_notebook": "Colabノートブック（あれば）",
    "benchmark_results": [
      {
        "dataset": "データセット名",
        "metric": "評価指標",
        "score": 数値,
        "sota_comparison": "SOTA比較（%）"
      }
    ],
    "reproducibility_score": 0.0-1.0,
    "dependencies": ["必要ライブラリのリスト"],
    "compute_requirements": {
      "gpu": "GPU要件",
      "memory": "メモリ要件", 
      "training_time": "学習時間"
    }
  },
  "business_metadata": {
    "market_size": "市場規模",
    "growth_rate": 数値,
    "roi_indicators": {
      "payback_period": "投資回収期間",
      "cost_reduction": "コスト削減額",
      "revenue_increase": "売上増加額"
    },
    "case_studies": [
      {
        "company": "企業名",
        "industry": "業界",
        "results": "結果",
        "timeline": "期間"
      }
    ],
    "implementation_cost": "low|medium|high|enterprise",
    "time_to_value": "価値実現期間",
    "competitive_advantage": "競争優位性の説明",
    "funding_info": {
      "amount": "調達額",
      "round": "調達ラウンド",
      "investors": ["投資家リスト"]
    }
  },
  "entities": {
    "companies": ["関連企業リスト"],
    "technologies": ["技術・フレームワークリスト"],
    "people": ["人物リスト"],
    "concepts": ["概念・手法リスト"],
    "products": ["製品・サービスリスト"]
  },
  "evidence": {
    "primary_sources": [
      {
        "type": "paper|press_release|documentation|code",
        "url": "URL",
        "credibility_score": 0.0-1.0
      }
    ],
    "citations": ["引用リスト"],
    "supporting_data": ["裏付けデータ"]
  },
  "summaries": {
    "executive_summary": "エグゼクティブサマリー（200文字以内）",
    "technical_summary": "技術要約（300文字以内）",
    "business_implications": "ビジネス示唆（300文字以内）",
    "key_takeaways": ["主要ポイントリスト（各100文字以内）"],
    "action_items": ["アクションアイテムリスト（各100文字以内）"]
  },
  "bias_assessment": {
    "detected_biases": ["検出されたバイアス"],
    "neutrality_score": 0.0-1.0,
    "transparency_score": 0.0-1.0
  },
  "quality_indicators": {
    "has_data": boolean,
    "has_citations": boolean,
    "has_methodology": boolean,
    "has_results": boolean,
    "content_depth": 0.0-1.0
  }
}
```

重要な注意事項：
1. 存在しない情報は null または空配列にしてください
2. 数値は実際の値がある場合のみ入力してください
3. スコアは0.0-1.0の範囲で評価してください
4. 日本語の記事は日本語で要約し、英語の記事は日本語に翻訳して要約してください
5. 技術的内容とビジネス価値の両面から分析してください
6. バイアスや偏見がないか客観的に評価してください

URL: {url}
"""
    
    async def analyze_url(self, url: str) -> Optional[Dict[str, Any]]:
        """URLの内容を分析して構造化データを返す"""
        if not self.client:
            logger.warning("Gemini client not available")
            return None

        # Validate URL before API call
        if not _validate_url(url):
            logger.warning(f"Invalid or unsafe URL rejected: {url}")
            return None

        try:
            # URLからコンテンツを分析
            prompt = self.analysis_prompt.format(url=url)
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.client.generate_content(prompt)
            )
            
            if not response or not response.text:
                logger.warning(f"Empty response for URL: {url}")
                return None
            
            # JSON応答をパース
            json_text = self._extract_json_from_response(response.text)
            if not json_text:
                logger.warning(f"No JSON found in response for URL: {url}")
                return None
            
            data = json.loads(json_text)
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error analyzing URL {url}: {e}")
            return None
    
    def _extract_json_from_response(self, response_text: str) -> Optional[str]:
        """レスポンスからJSON部分を抽出"""
        # ```json ... ``` パターンを探す
        json_pattern = r'```json\s*(.*?)\s*```'
        match = re.search(json_pattern, response_text, re.DOTALL)
        
        if match:
            return match.group(1).strip()
        
        # JSON object パターンを探す
        json_pattern = r'\{.*\}'
        match = re.search(json_pattern, response_text, re.DOTALL)
        
        if match:
            return match.group(0).strip()
        
        return None
    
    async def analyze_batch(self, urls: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """複数URLのバッチ分析"""
        # Filter out invalid URLs first
        valid_urls = [url for url in urls if _validate_url(url)]
        invalid_count = len(urls) - len(valid_urls)
        if invalid_count > 0:
            logger.warning(f"Filtered out {invalid_count} invalid URLs")

        batch_size = settings.api.gemini_url_context_batch
        results = {}

        for i in range(0, len(valid_urls), batch_size):
            batch_urls = valid_urls[i:i + batch_size]
            
            # 並列処理でバッチ分析
            tasks = [self.analyze_url(url) for url in batch_urls]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for url, result in zip(batch_urls, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Error analyzing {url}: {result}")
                    results[url] = None
                else:
                    results[url] = result
            
            # APIレート制限を考慮した待機
            if i + batch_size < len(urls):
                await asyncio.sleep(1)
        
        return results
    
    def convert_to_article_schema(self, url: str, analysis_data: Dict[str, Any]) -> Article:
        """分析データをArticleスキーマに変換"""
        basic = analysis_data.get('basic_info', {})
        tech_data = analysis_data.get('technical_metadata', {})
        biz_data = analysis_data.get('business_metadata', {})
        entities_data = analysis_data.get('entities', {})
        evidence_data = analysis_data.get('evidence', {})
        summaries_data = analysis_data.get('summaries', {})
        bias_data = analysis_data.get('bias_assessment', {})
        
        # URLからIDを生成
        article_id = str(hash(url))
        
        # 技術的メタデータの変換
        technical = None
        if tech_data:
            # ベンチマーク結果の変換
            benchmark_results = []
            for bench in tech_data.get('benchmark_results', []):
                if all(k in bench for k in ['dataset', 'metric', 'score']):
                    benchmark_results.append(BenchmarkResult(
                        dataset=bench['dataset'],
                        metric=bench['metric'],
                        score=float(bench['score']),
                        sota_comparison=float(bench.get('sota_comparison', 0))
                    ))
            
            # 計算要件の変換
            compute_req = None
            if tech_data.get('compute_requirements'):
                comp = tech_data['compute_requirements']
                compute_req = ComputeRequirements(
                    gpu=comp.get('gpu'),
                    memory=comp.get('memory'),
                    training_time=comp.get('training_time')
                )
            
            # 難易度レベルの変換
            difficulty = DifficultyLevel.INTERMEDIATE
            if tech_data.get('difficulty_level'):
                try:
                    difficulty = DifficultyLevel(tech_data['difficulty_level'])
                except ValueError:
                    pass
            
            technical = TechnicalMetadata(
                difficulty_level=difficulty,
                implementation_ready=tech_data.get('implementation_ready', False),
                code_available=tech_data.get('code_available', False),
                paper_link=tech_data.get('paper_link'),
                github_repo=tech_data.get('github_repo'),
                colab_notebook=tech_data.get('colab_notebook'),
                benchmark_results=benchmark_results,
                reproducibility_score=tech_data.get('reproducibility_score', 0.0),
                dependencies=tech_data.get('dependencies', []),
                compute_requirements=compute_req
            )
        
        # ビジネスメタデータの変換
        business = None
        if biz_data:
            # ROI指標の変換
            roi = None
            if biz_data.get('roi_indicators'):
                roi_data = biz_data['roi_indicators']
                roi = ROIIndicators(
                    payback_period=roi_data.get('payback_period'),
                    cost_reduction=roi_data.get('cost_reduction'),
                    revenue_increase=roi_data.get('revenue_increase')
                )
            
            # 事例研究の変換
            case_studies = []
            for case in biz_data.get('case_studies', []):
                if all(k in case for k in ['company', 'industry', 'results', 'timeline']):
                    case_studies.append(CaseStudy(
                        company=case['company'],
                        industry=case['industry'],
                        results=case['results'],
                        timeline=case['timeline']
                    ))
            
            # 資金調達情報の変換
            funding = None
            if biz_data.get('funding_info'):
                fund_data = biz_data['funding_info']
                funding = FundingInfo(
                    amount=fund_data.get('amount'),
                    round=fund_data.get('round'),
                    investors=fund_data.get('investors', [])
                )
            
            # 実装コストの変換
            impl_cost = None
            if biz_data.get('implementation_cost'):
                try:
                    impl_cost = ImplementationCost(biz_data['implementation_cost'])
                except ValueError:
                    pass
            
            business = BusinessMetadata(
                market_size=biz_data.get('market_size'),
                growth_rate=biz_data.get('growth_rate'),
                roi_indicators=roi,
                case_studies=case_studies,
                implementation_cost=impl_cost,
                time_to_value=biz_data.get('time_to_value'),
                competitive_advantage=biz_data.get('competitive_advantage'),
                funding_info=funding
            )
        
        # エンティティの変換
        entities = ArticleEntities(
            companies=entities_data.get('companies', []),
            technologies=entities_data.get('technologies', []),
            people=entities_data.get('people', []),
            concepts=entities_data.get('concepts', []),
            products=entities_data.get('products', [])
        ) if entities_data else None
        
        # 根拠の変換
        evidence = None
        if evidence_data:
            primary_sources = []
            for source in evidence_data.get('primary_sources', []):
                if 'type' in source and 'url' in source:
                    try:
                        source_type = EvidenceType(source['type'])
                        primary_sources.append(EvidenceSource(
                            type=source_type,
                            url=source['url'],
                            credibility_score=source.get('credibility_score', 0.5)
                        ))
                    except ValueError:
                        continue
            
            evidence = Evidence(
                primary_sources=primary_sources,
                citations=evidence_data.get('citations', []),
                supporting_data=evidence_data.get('supporting_data', [])
            )
        
        # 要約の変換
        summaries = Summaries(
            executive_summary=summaries_data.get('executive_summary'),
            technical_summary=summaries_data.get('technical_summary'),
            business_implications=summaries_data.get('business_implications'),
            key_takeaways=summaries_data.get('key_takeaways', []),
            action_items=summaries_data.get('action_items', [])
        ) if summaries_data else None
        
        # 基本情報から記事オブジェクトを作成
        from datetime import datetime
        from ..models.schemas import SourceTier
        
        article = Article(
            id=article_id,
            title=basic.get('title', 'Unknown Title'),
            url=url,
            source=self._extract_source_name(url),
            source_tier=SourceTier.TIER_2,  # デフォルト
            published_date=datetime.now(),
            content=basic.get('content_summary'),
            category=basic.get('category'),
            technical=technical,
            business=business,
            entities=entities,
            evidence=evidence,
            summaries=summaries
        )
        
        return article
    
    def _extract_source_name(self, url: str) -> str:
        """URLからソース名を抽出"""
        try:
            domain = urlparse(url).netloc
            # サブドメインを除去
            parts = domain.split('.')
            if len(parts) >= 2:
                return parts[-2]  # example.com -> example
            return domain
        except:
            return "unknown"
#!/usr/bin/env python3
"""
Daily AI News System v2.0 - 簡易ビルドスクリプト
Python 3.13互換性 + 依存関係最小化版
"""
import os
import json
import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

print("🚀 Daily AI News System v2.0 (簡易版)")
print("   基本機能のみ + Fast Mode")
print()

# 環境変数の設定
os.environ['NEWS_FAST_MODE'] = '1'

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent
import sys
sys.path.insert(0, str(project_root))

# ログディレクトリの作成
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

# ログ設定
log_handlers = [logging.StreamHandler()]
log_file = log_dir / 'build-simple.log'
try:
    log_handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
except Exception as e:
    print(f"Warning: Could not create log file: {e}")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=log_handlers
)
logger = logging.getLogger(__name__)

def create_sample_output():
    """サンプル出力データの作成"""
    
    # ディレクトリの作成
    news_dir = Path('news')
    news_dir.mkdir(exist_ok=True)
    
    # サンプルデータ
    sample_data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "system_version": "2.0-simple",
        "highlight": {
            "id": "sample-001",
            "title": "Daily AI News System v2.0 がリリースされました",
            "url": "https://github.com/user/daily-ai-news-v2",
            "source": "GitHub",
            "source_tier": 1,
            "published_date": datetime.now().isoformat(),
            "category": "tools",
            "content_summary": "多層評価システム、Gemini URL Context分析、ハイブリッド検索エンジンを備えたAIニュース分析プラットフォーム",
            "key_takeaways": [
                "5層の評価アルゴリズムによる高品質コンテンツ選別",
                "エンジニア・ビジネスマン向けペルソナ最適化",
                "Gemini AIによるURL直接分析",
                "React + TypeScript インテリジェントダッシュボード"
            ],
            "action_items": [
                "GEMINI_API_KEY を設定してAI分析を有効化",
                "requirements-v2.txt で完全な依存関係をインストール",
                "フロントエンドの開発とカスタマイズ"
            ],
            "evaluation": {
                "engineer_score": 0.9,
                "business_score": 0.8,
                "score_breakdown": {
                    "quality": 0.9,
                    "relevance": 0.9,
                    "temporal": 0.8,
                    "trust": 0.9,
                    "actionability": 0.8
                }
            },
            "technical_metadata": {
                "difficulty_level": "advanced",
                "implementation_ready": True,
                "code_available": True,
                "github_repo": "https://github.com/user/daily-ai-news-v2",
                "reproducibility_score": 0.9
            },
            "entities": {
                "companies": ["Anthropic", "Google"],
                "technologies": ["Python", "React", "TypeScript", "Gemini", "AI"],
                "concepts": ["Multi-layer evaluation", "Persona optimization", "Hybrid search"],
                "products": ["Daily AI News v2.0"]
            },
            "evidence_score": 0.8
        },
        "categories": {
            "engineer": [
                {
                    "id": "sample-eng-001",
                    "title": "Multi-Layer Article Evaluation System の実装",
                    "url": "#",
                    "source": "Internal",
                    "source_tier": 1,
                    "published_date": datetime.now().isoformat(),
                    "category": "research",
                    "content_summary": "記事の品質を5つの軸で評価する多層評価システム",
                    "key_takeaways": ["品質、関連性、時間価値、信頼性、実行可能性の5軸評価"],
                    "evaluation": {
                        "engineer_score": 0.85,
                        "business_score": 0.7,
                        "score_breakdown": {
                            "quality": 0.9,
                            "relevance": 0.8,
                            "temporal": 0.8,
                            "trust": 0.9,
                            "actionability": 0.8
                        }
                    },
                    "technical_metadata": {
                        "difficulty_level": "intermediate",
                        "implementation_ready": True,
                        "code_available": True,
                        "reproducibility_score": 0.8
                    },
                    "evidence_score": 0.7
                }
            ],
            "business": [
                {
                    "id": "sample-biz-001",
                    "title": "AI-Powered Content Analysis for Business Intelligence",
                    "url": "#",
                    "source": "Internal",
                    "source_tier": 1,
                    "published_date": datetime.now().isoformat(),
                    "category": "business",
                    "content_summary": "ビジネス価値に特化したAI記事分析システム",
                    "key_takeaways": ["ROI指標の自動抽出", "競争分析の効率化", "意思決定支援の高度化"],
                    "evaluation": {
                        "engineer_score": 0.7,
                        "business_score": 0.9,
                        "score_breakdown": {
                            "quality": 0.8,
                            "relevance": 0.9,
                            "temporal": 0.9,
                            "trust": 0.8,
                            "actionability": 0.9
                        }
                    },
                    "business_metadata": {
                        "implementation_cost": "medium",
                        "time_to_value": "2-4週間",
                        "competitive_advantage": "高度なAI分析による差別化"
                    },
                    "evidence_score": 0.8
                }
            ],
            "research": [],
            "tools": []
        },
        "metadata": {
            "total_articles_processed": 2,
            "total_sources": 2,
            "evaluation_thresholds": {
                "engineer": 0.75,
                "business": 0.75
            },
            "quality_indicators": {
                "average_evidence_score": 0.75,
                "articles_with_code": 2,
                "articles_with_case_studies": 1
            }
        }
    }
    
    # JSONファイルの出力
    latest_path = news_dir / 'latest.json'
    with open(latest_path, 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, ensure_ascii=False, indent=2)
    
    # 日付別ファイル
    today = datetime.now().strftime('%Y-%m-%d')
    daily_path = news_dir / f'{today}.json'
    with open(daily_path, 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"📄 Output files created: {latest_path}, {daily_path}")
    
    return sample_data

def main():
    """メイン処理"""
    logger.info("🚀 Starting Daily AI News System v2.0 (Simple Mode)")
    
    try:
        # ログディレクトリ作成
        Path('logs').mkdir(exist_ok=True)
        
        logger.info("📦 Creating sample output (Full system requires additional dependencies)")
        sample_data = create_sample_output()
        
        logger.info("✅ Build completed successfully!")
        logger.info(f"   - Sample articles: {len(sample_data['categories']['engineer']) + len(sample_data['categories']['business'])}")
        logger.info(f"   - Output: news/latest.json")
        
        print()
        print("✅ Daily AI News System v2.0 (簡易版) 完了!")
        print(f"   - サンプル記事: {len(sample_data['categories']['engineer']) + len(sample_data['categories']['business'])}件")
        print("   - 出力: news/latest.json")
        print()
        print("🔄 完全版を使用するには:")
        print("   1. PowerShellで: ./setup-env.ps1")
        print("   2. Gemini API設定: $env:GEMINI_API_KEY='your-key'") 
        print("   3. 完全版実行: python build.py")
        print()
        print("🌐 フロントエンド開発:")
        print("   1. cd frontend")
        print("   2. npm install")
        print("   3. npm run dev")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Build failed: {e}", exc_info=True)
        print(f"❌ ビルドに失敗しました: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
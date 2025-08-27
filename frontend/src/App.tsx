/**
 * Daily AI News v2.0 - メインアプリケーション（簡略版）
 */
import React, { useState, useEffect } from 'react';

interface Article {
  id: string;
  title: string;
  url: string;
  source: string;
  content_summary?: string;
  evaluation?: {
    engineer_score: number;
    business_score: number;
  };
}

interface NewsData {
  generated_at: string;
  highlight?: Article;
  categories: {
    engineer: Article[];
    business: Article[];
  };
}

function App() {
  const [newsData, setNewsData] = useState<NewsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'engineer' | 'business'>('engineer');

  useEffect(() => {
    // サンプルデータを直接設定（開発用）
    const sampleData: NewsData = {
      "generated_at": "2025-08-25T22:51:30.270912+00:00",
      "highlight": {
        "id": "sample-001",
        "title": "Daily AI News System v2.0 がリリースされました",
        "url": "https://github.com/user/daily-ai-news-v2",
        "source": "GitHub",
        "content_summary": "多層評価システム、Gemini URL Context分析、ハイブリッド検索エンジンを備えたAIニュース分析プラットフォーム",
        "evaluation": {
          "engineer_score": 0.9,
          "business_score": 0.8
        }
      },
      "categories": {
        "engineer": [
          {
            "id": "sample-eng-001",
            "title": "Multi-Layer Article Evaluation System の実装",
            "url": "#",
            "source": "Internal",
            "content_summary": "記事の品質を5つの軸で評価する多層評価システム",
            "evaluation": {
              "engineer_score": 0.85,
              "business_score": 0.7
            }
          }
        ],
        "business": [
          {
            "id": "sample-biz-001",
            "title": "AI-Powered Content Analysis for Business Intelligence",
            "url": "#",
            "source": "Internal",
            "content_summary": "ビジネス価値に特化したAI記事分析システム",
            "evaluation": {
              "engineer_score": 0.7,
              "business_score": 0.9
            }
          }
        ]
      }
    };
    
    setNewsData(sampleData);
    setLoading(false);
    
    // 実際のデータをフェッチ（利用可能な場合）
    fetch('/news/latest.json')
      .then(res => res.json())
      .then(data => {
        setNewsData(data);
      })
      .catch(err => {
        console.log('Using sample data, actual news fetch failed:', err);
      });
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  if (!newsData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl text-red-500">Failed to load news data</div>
      </div>
    );
  }

  const currentArticles = newsData.categories[activeTab] || [];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-gray-900">
            Daily AI News v2.0
          </h1>
          <p className="text-sm text-gray-600">
            {new Date(newsData.generated_at).toLocaleString('ja-JP')}
          </p>
        </div>
      </header>

      {/* Highlight */}
      {newsData.highlight && (
        <section className="max-w-7xl mx-auto px-4 py-6">
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-lg">
            <h2 className="text-lg font-semibold mb-3">今日のハイライト</h2>
            <div className="bg-white p-4 rounded-lg">
              <h3 className="text-xl font-bold mb-2">{newsData.highlight.title}</h3>
              <p className="text-gray-600 mb-3">{newsData.highlight.content_summary}</p>
              <div className="flex items-center gap-4 text-sm">
                <span className="text-gray-500">Source: {newsData.highlight.source}</span>
                {newsData.highlight.evaluation && (
                  <>
                    <span className="text-blue-600">
                      Engineer: {(newsData.highlight.evaluation.engineer_score * 100).toFixed(0)}%
                    </span>
                    <span className="text-green-600">
                      Business: {(newsData.highlight.evaluation.business_score * 100).toFixed(0)}%
                    </span>
                  </>
                )}
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Tabs */}
      <div className="max-w-7xl mx-auto px-4">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab('engineer')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'engineer'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              エンジニア向け ({newsData.categories.engineer?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab('business')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'business'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              ビジネス向け ({newsData.categories.business?.length || 0})
            </button>
          </nav>
        </div>
      </div>

      {/* Articles */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid gap-4 md:grid-cols-2">
          {currentArticles.map(article => (
            <div key={article.id} className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
              <h3 className="font-semibold text-lg mb-2">{article.title}</h3>
              <p className="text-gray-600 text-sm mb-3">{article.content_summary}</p>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-500">{article.source}</span>
                {article.evaluation && (
                  <div className="flex gap-3">
                    <span className="text-blue-600">
                      Eng: {(article.evaluation.engineer_score * 100).toFixed(0)}%
                    </span>
                    <span className="text-green-600">
                      Biz: {(article.evaluation.business_score * 100).toFixed(0)}%
                    </span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {currentArticles.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            記事がありません
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
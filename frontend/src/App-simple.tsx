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
    // Fetch news data from local file
    fetch('/news/latest.json')
      .then(res => res.json())
      .then(data => {
        setNewsData(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load news:', err);
        // Try loading from parent directory (for dev)
        fetch('../news/latest.json')
          .then(res => res.json())
          .then(data => {
            setNewsData(data);
            setLoading(false);
          })
          .catch(() => setLoading(false));
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
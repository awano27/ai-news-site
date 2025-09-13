/**
 * インテリジェントダッシュボード - メインコンポーネント
 */
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Brain, TrendingUp, Code, Building, Search, Filter, Zap } from 'lucide-react';
import { Header } from './layout/Header';
import { Sidebar } from './layout/Sidebar';
import { HighlightCard } from './cards/HighlightCard';
import { ArticleCard } from './cards/ArticleCard';
import { ScoreBreakdownChart } from './charts/ScoreBreakdownChart';
import { PersonaToggle } from './ui/PersonaToggle';
import { SmartFilterBar } from './ui/SmartFilterBar';
import { LoadingSpinner } from './ui/LoadingSpinner';
import { ErrorMessage } from './ui/ErrorMessage';
import { useNewsData } from '../hooks/useNewsData';
import { usePersonaStore } from '../store/personaStore';
import { useFiltersStore } from '../store/filtersStore';
import { Article, PersonaType, CategoryType } from '../types/article';

const categoryIcons: Record<CategoryType, React.ComponentType<{ className?: string }>> = {
  engineer: Code,
  business: Building,
  research: Brain,
  tools: Zap,
};

const categoryLabels: Record<CategoryType, string> = {
  engineer: 'エンジニア向け',
  business: 'ビジネス向け',
  research: '研究・論文',
  tools: 'ツール・製品',
};

export function Dashboard() {
  const { currentPersona, setPersona } = usePersonaStore();
  const { filters, updateFilters, clearFilters } = useFiltersStore();
  const [activeCategory, setActiveCategory] = useState<CategoryType>('engineer');
  
  const { data: newsData, isLoading, error, refetch } = useNewsData();
  
  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50">
        <Header />
        <div className="flex">
          <Sidebar />
          <main className="flex-1 ml-64 p-8">
            <LoadingSpinner size="large" message="最新AIニュースを分析中..." />
          </main>
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="min-h-screen bg-slate-50">
        <Header />
        <div className="flex">
          <Sidebar />
          <main className="flex-1 ml-64 p-8">
            <ErrorMessage 
              message="ニュースデータの取得に失敗しました" 
              onRetry={() => refetch()}
            />
          </main>
        </div>
      </div>
    );
  }
  
  if (!newsData) {
    return null;
  }
  
  const currentArticles = newsData.categories[activeCategory] || [];
  const totalArticles = Object.values(newsData.categories).flat().length;
  
  return (
    <div className="min-h-screen bg-slate-50">
      <Header />
      
      <div className="flex">
        <Sidebar />
        
        <main className="flex-1 ml-64">
          {/* ヘッダー統計 */}
          <div className="bg-white border-b border-slate-200 px-8 py-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h1 className="text-2xl font-bold text-slate-900">
                  Daily AI News v2.0
                </h1>
                <p className="text-slate-600 mt-1">
                  {new Date(newsData.generated_at).toLocaleString('ja-JP')} 更新
                </p>
              </div>
              
              <PersonaToggle
                currentPersona={currentPersona}
                onPersonaChange={setPersona}
              />
            </div>
            
            {/* 統計カード */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-slate-50 rounded-lg p-4">
                <div className="text-2xl font-bold text-slate-900">
                  {newsData.metadata.total_articles_processed}
                </div>
                <div className="text-sm text-slate-600">処理済み記事</div>
              </div>
              
              <div className="bg-slate-50 rounded-lg p-4">
                <div className="text-2xl font-bold text-slate-900">
                  {newsData.metadata.total_sources}
                </div>
                <div className="text-sm text-slate-600">情報源</div>
              </div>
              
              <div className="bg-slate-50 rounded-lg p-4">
                <div className="text-2xl font-bold text-slate-900">
                  {newsData.metadata.quality_indicators.articles_with_code}
                </div>
                <div className="text-sm text-slate-600">コード付き記事</div>
              </div>
              
              <div className="bg-slate-50 rounded-lg p-4">
                <div className="text-2xl font-bold text-slate-900">
                  {Math.round(newsData.metadata.quality_indicators.average_evidence_score * 100)}%
                </div>
                <div className="text-sm text-slate-600">平均エビデンス</div>
              </div>
            </div>
          </div>
          
          {/* ハイライトセクション */}
          {newsData.highlight && (
            <section className="px-8 py-6 bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-slate-200">
              <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center">
                <TrendingUp className="w-5 h-5 mr-2 text-blue-600" />
                今日のハイライト
              </h2>
              <HighlightCard article={newsData.highlight} />
            </section>
          )}
          
          {/* フィルター&検索バー */}
          <div className="px-8 py-4 bg-white border-b border-slate-200">
            <SmartFilterBar
              filters={filters}
              onFiltersChange={updateFilters}
              onClear={clearFilters}
              persona={currentPersona}
            />
          </div>
          
          {/* カテゴリタブ */}
          <div className="px-8 py-4 bg-white border-b border-slate-200">
            <nav className="flex space-x-1">
              {(Object.keys(categoryLabels) as CategoryType[]).map((category) => {
                const Icon = categoryIcons[category];
                const count = newsData.categories[category]?.length || 0;
                const isActive = activeCategory === category;
                
                return (
                  <button
                    key={category}
                    onClick={() => setActiveCategory(category)}
                    className={`
                      flex items-center px-4 py-2 rounded-lg font-medium transition-colors
                      ${isActive 
                        ? 'bg-blue-100 text-blue-700 border border-blue-200' 
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                      }
                    `}
                  >
                    <Icon className="w-4 h-4 mr-2" />
                    {categoryLabels[category]}
                    <span className={`
                      ml-2 px-2 py-0.5 rounded-full text-xs font-medium
                      ${isActive 
                        ? 'bg-blue-200 text-blue-800' 
                        : 'bg-slate-200 text-slate-600'
                      }
                    `}>
                      {count}
                    </span>
                  </button>
                );
              })}
            </nav>
          </div>
          
          {/* メインコンテンツ */}
          <div className="px-8 py-6">
            {currentArticles.length === 0 ? (
              <div className="text-center py-12">
                <Search className="w-12 h-12 text-slate-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-slate-900 mb-2">
                  記事が見つかりません
                </h3>
                <p className="text-slate-600">
                  フィルター条件を調整するか、他のカテゴリをご確認ください。
                </p>
              </div>
            ) : (
              <>
                {/* 記事リスト */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {currentArticles.map((article) => (
                    <ArticleCard
                      key={article.id}
                      article={article}
                      persona={currentPersona}
                      showScoreBreakdown={true}
                    />
                  ))}
                </div>
                
                {/* スコア分析セクション */}
                <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                    <h3 className="text-lg font-semibold text-slate-900 mb-4">
                      カテゴリ別スコア分析
                    </h3>
                    <ScoreBreakdownChart 
                      articles={currentArticles}
                      persona={currentPersona}
                    />
                  </div>
                  
                  <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                    <h3 className="text-lg font-semibold text-slate-900 mb-4">
                      品質指標
                    </h3>
                    <div className="space-y-4">
                      <div className="flex justify-between items-center">
                        <span className="text-slate-600">コード利用可能</span>
                        <span className="font-semibold">
                          {currentArticles.filter(a => a.technical_metadata?.code_available).length}/{currentArticles.length}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-slate-600">実装準備完了</span>
                        <span className="font-semibold">
                          {currentArticles.filter(a => a.technical_metadata?.implementation_ready).length}/{currentArticles.length}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-slate-600">平均エビデンス</span>
                        <span className="font-semibold">
                          {Math.round((currentArticles.reduce((acc, a) => acc + a.evidence_score, 0) / currentArticles.length) * 100)}%
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
"""
ハイブリッド検索エンジン v2.0
BM25、セマンティック検索、エンティティ検索、グラフ検索の統合
"""
import math
import re
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict, Counter
from dataclasses import dataclass
# NumPy import with fallback
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("Warning: numpy not available, using pure Python fallbacks")
    # Create a minimal numpy-like interface
    class np:
        @staticmethod
        def zeros(shape):
            if isinstance(shape, tuple):
                if len(shape) == 2:
                    return [[0.0] * shape[1] for _ in range(shape[0])]
                return [0.0] * shape[0]
            return [0.0] * shape
        
        @staticmethod
        def array(data):
            return data

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("Warning: sentence-transformers not available, semantic search disabled")
    
    # Simple cosine similarity fallback
    def cosine_similarity(a, b):
        """Simple cosine similarity implementation"""
        if not NUMPY_AVAILABLE:
            return [[0.0] * len(b) for _ in range(len(a))]
        return np.zeros((len(a), len(b)))

from ..models.schemas import Article, ArticleEntities
from ..config.settings import settings


@dataclass
class SearchResult:
    """検索結果"""
    article: Article
    score: float
    score_breakdown: Dict[str, float]
    rank: int


class BM25Scorer:
    """BM25スコア計算"""
    
    def __init__(self, k1: float = 1.2, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_freqs = {}
        self.idf = {}
        self.doc_lengths = {}
        self.avgdl = 0
        self.corpus_size = 0
    
    def fit(self, corpus: List[str]):
        """コーパスでBM25パラメータを学習"""
        self.corpus_size = len(corpus)
        doc_lengths = []
        term_doc_counts = defaultdict(int)
        
        # 各文書の処理
        for doc_id, doc in enumerate(corpus):
            words = self._tokenize(doc)
            doc_length = len(words)
            doc_lengths.append(doc_length)
            
            # 文書内の単語頻度
            word_counts = Counter(words)
            for word in word_counts.keys():
                term_doc_counts[word] += 1
        
        self.avgdl = sum(doc_lengths) / len(doc_lengths)
        
        # IDF計算
        for term, doc_count in term_doc_counts.items():
            self.idf[term] = math.log((self.corpus_size - doc_count + 0.5) / (doc_count + 0.5))
    
    def score(self, query: str, doc: str) -> float:
        """クエリと文書のBM25スコア計算"""
        query_words = self._tokenize(query)
        doc_words = self._tokenize(doc)
        doc_word_counts = Counter(doc_words)
        doc_length = len(doc_words)
        
        score = 0
        for word in query_words:
            if word in doc_word_counts:
                tf = doc_word_counts[word]
                idf = self.idf.get(word, 0)
                
                # BM25スコア計算
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_length / self.avgdl)
                score += idf * (numerator / denominator)
        
        return max(0, score)
    
    def _tokenize(self, text: str) -> List[str]:
        """テキストのトークン化"""
        # 日本語・英語対応の簡易トークナイザー
        text = text.lower()
        # 英語単語とカタカナ・ひらがな・漢字を抽出
        tokens = re.findall(r'\b[a-zA-Z]+\b|[ア-ヴー]+|[ひ-ゟ]+|[一-龯]+', text)
        return [token for token in tokens if len(token) >= 2]


class SemanticSearchEngine:
    """セマンティック検索エンジン"""
    
    def __init__(self):
        self.model = None
        self.embeddings_cache = {}
        
        if TRANSFORMERS_AVAILABLE:
            try:
                self.model = SentenceTransformer(settings.models.embedding_model)
            except Exception as e:
                print(f"Warning: Failed to load embedding model: {e}")
    
    def encode(self, texts: List[str]) -> np.ndarray:
        """テキストをベクトル化"""
        if not self.model:
            return np.zeros((len(texts), 384))  # ダミーベクトル
        
        # キャッシュチェック
        cached_embeddings = []
        new_texts = []
        new_indices = []
        
        for i, text in enumerate(texts):
            if text in self.embeddings_cache:
                cached_embeddings.append((i, self.embeddings_cache[text]))
            else:
                new_texts.append(text)
                new_indices.append(i)
        
        # 新しいテキストのエンコード
        if new_texts:
            try:
                new_embeddings = self.model.encode(new_texts, convert_to_numpy=True)
                # キャッシュに保存
                for text, embedding in zip(new_texts, new_embeddings):
                    self.embeddings_cache[text] = embedding
            except Exception as e:
                print(f"Warning: Encoding failed: {e}")
                new_embeddings = np.zeros((len(new_texts), 384))
        else:
            new_embeddings = np.array([])
        
        # 結果をマージ
        all_embeddings = np.zeros((len(texts), 384))
        
        # キャッシュされた埋め込みを配置
        for i, embedding in cached_embeddings:
            all_embeddings[i] = embedding
        
        # 新しい埋め込みを配置
        if len(new_embeddings) > 0:
            for idx, i in enumerate(new_indices):
                all_embeddings[i] = new_embeddings[idx]
        
        return all_embeddings
    
    def similarity_search(self, query: str, documents: List[str], top_k: int = 10) -> List[Tuple[int, float]]:
        """類似度検索"""
        if not documents:
            return []
        
        # クエリと文書をエンコード
        query_embedding = self.encode([query])
        doc_embeddings = self.encode(documents)
        
        # コサイン類似度計算
        try:
            similarities = cosine_similarity(query_embedding, doc_embeddings)[0]
        except:
            similarities = np.zeros(len(documents))
        
        # スコア順でソート
        scored_docs = [(i, float(score)) for i, score in enumerate(similarities)]
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        return scored_docs[:top_k]


class EntitySearchEngine:
    """エンティティベース検索"""
    
    def __init__(self):
        self.entity_index = defaultdict(set)  # entity -> set of doc_ids
        self.doc_entities = {}  # doc_id -> entities
    
    def index_entities(self, articles: List[Article]):
        """記事のエンティティをインデックス化"""
        for i, article in enumerate(articles):
            if not article.entities:
                continue
            
            # 全エンティティを収集
            all_entities = (
                article.entities.companies +
                article.entities.technologies +
                article.entities.people +
                article.entities.concepts +
                article.entities.products
            )
            
            self.doc_entities[i] = all_entities
            
            # エンティティごとのインデックス更新
            for entity in all_entities:
                self.entity_index[entity.lower()].add(i)
    
    def search_by_entities(self, query_entities: List[str], top_k: int = 10) -> List[Tuple[int, float]]:
        """エンティティベース検索"""
        if not query_entities:
            return []
        
        doc_scores = defaultdict(float)
        
        for entity in query_entities:
            entity_lower = entity.lower()
            if entity_lower in self.entity_index:
                # エンティティを含む文書にスコアを付与
                for doc_id in self.entity_index[entity_lower]:
                    doc_scores[doc_id] += 1.0
        
        # エンティティの重複度でスコア調整
        for doc_id in doc_scores:
            if doc_id in self.doc_entities:
                entity_overlap = len(set(e.lower() for e in query_entities) & 
                                   set(e.lower() for e in self.doc_entities[doc_id]))
                doc_scores[doc_id] = entity_overlap / len(query_entities)
        
        # スコア順でソート
        scored_docs = list(doc_scores.items())
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        return scored_docs[:top_k]


class GraphSearchEngine:
    """グラフベース関連検索"""
    
    def __init__(self):
        self.similarity_graph = {}  # doc_id -> {related_doc_id: similarity}
        self.entity_graph = defaultdict(set)  # entity -> related_entities
    
    def build_similarity_graph(self, articles: List[Article], threshold: float = 0.3):
        """記事間の類似度グラフを構築"""
        if not articles:
            return
        
        # セマンティック検索エンジンを使用
        semantic_engine = SemanticSearchEngine()
        
        # 全記事のテキストを準備
        texts = []
        for article in articles:
            text = f"{article.title} {article.content or ''}"
            if article.summaries and article.summaries.executive_summary:
                text += " " + article.summaries.executive_summary
            texts.append(text)
        
        # 記事間の類似度を計算
        embeddings = semantic_engine.encode(texts)
        
        try:
            similarity_matrix = cosine_similarity(embeddings)
            
            for i in range(len(articles)):
                self.similarity_graph[i] = {}
                for j in range(len(articles)):
                    if i != j and similarity_matrix[i][j] >= threshold:
                        self.similarity_graph[i][j] = float(similarity_matrix[i][j])
        except:
            # フォールバック: エンティティベースの類似度
            self._build_entity_similarity_graph(articles)
    
    def _build_entity_similarity_graph(self, articles: List[Article]):
        """エンティティベースの類似度グラフ（フォールバック）"""
        for i, article1 in enumerate(articles):
            if not article1.entities:
                continue
                
            entities1 = set(
                e.lower() for e in (
                    article1.entities.companies +
                    article1.entities.technologies +
                    article1.entities.concepts
                )
            )
            
            self.similarity_graph[i] = {}
            
            for j, article2 in enumerate(articles):
                if i == j or not article2.entities:
                    continue
                
                entities2 = set(
                    e.lower() for e in (
                        article2.entities.companies +
                        article2.entities.technologies +
                        article2.entities.concepts
                    )
                )
                
                # Jaccardインデックス
                intersection = len(entities1 & entities2)
                union = len(entities1 | entities2)
                
                if union > 0:
                    similarity = intersection / union
                    if similarity >= 0.2:  # 閾値
                        self.similarity_graph[i][j] = similarity
    
    def graph_search(self, seed_doc_ids: List[int], max_hops: int = 2, top_k: int = 10) -> List[Tuple[int, float]]:
        """グラフベース検索（関連記事の探索）"""
        visited = set(seed_doc_ids)
        current_level = {doc_id: 1.0 for doc_id_id in seed_doc_ids}
        results = {}
        
        for hop in range(max_hops):
            next_level = {}
            
            for doc_id, current_score in current_level.items():
                if doc_id in self.similarity_graph:
                    for related_id, similarity in self.similarity_graph[doc_id].items():
                        if related_id not in visited:
                            # スコアの減衰
                            decay_factor = 0.7 ** (hop + 1)
                            new_score = current_score * similarity * decay_factor
                            
                            if related_id not in next_level or next_level[related_id] < new_score:
                                next_level[related_id] = new_score
            
            # 結果に追加
            for doc_id, score in next_level.items():
                if doc_id not in results or results[doc_id] < score:
                    results[doc_id] = score
            
            # 次のレベルに移動
            visited.update(next_level.keys())
            current_level = next_level
            
            if not current_level:  # 探索終了
                break
        
        # スコア順でソート
        scored_docs = list(results.items())
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        return scored_docs[:top_k]


class HybridSearchEngine:
    """ハイブリッド検索エンジンのメインクラス"""
    
    def __init__(self):
        self.bm25 = BM25Scorer()
        self.semantic = SemanticSearchEngine()
        self.entity = EntitySearchEngine()
        self.graph = GraphSearchEngine()
        
        self.articles = []
        self.is_fitted = False
    
    def fit(self, articles: List[Article]):
        """記事データでサーチエンジンを学習"""
        self.articles = articles
        
        if not articles:
            return
        
        # BM25の学習
        texts = []
        for article in articles:
            text = f"{article.title} {article.content or ''}"
            if article.summaries:
                if article.summaries.executive_summary:
                    text += " " + article.summaries.executive_summary
                if article.summaries.technical_summary:
                    text += " " + article.summaries.technical_summary
            texts.append(text)
        
        self.bm25.fit(texts)
        
        # エンティティインデックスの構築
        self.entity.index_entities(articles)
        
        # グラフの構築
        self.graph.build_similarity_graph(articles)
        
        self.is_fitted = True
    
    def search(self, query: str, filters: Optional[Dict] = None, 
              persona: Optional[str] = None, top_k: int = 20) -> List[SearchResult]:
        """ハイブリッド検索の実行"""
        if not self.is_fitted or not self.articles:
            return []
        
        # 1. キーワード検索（BM25）
        keyword_results = self._bm25_search(query)
        
        # 2. セマンティック検索
        semantic_results = self._semantic_search(query)
        
        # 3. エンティティベース検索
        entities = self._extract_entities(query)
        entity_results = self._entity_search(entities)
        
        # 4. グラフベース関連検索
        graph_results = self._graph_search(query)
        
        # 5. 結果の統合
        combined_results = self._merge_results({
            'keyword': keyword_results,
            'semantic': semantic_results,
            'entity': entity_results,
            'graph': graph_results
        })
        
        # 6. ペルソナ別最適化
        if persona:
            combined_results = self._apply_persona_optimization(combined_results, persona)
        
        # 7. フィルタリング
        if filters:
            combined_results = self._apply_filters(combined_results, filters)
        
        # 8. 最終スコアでソート
        combined_results.sort(key=lambda x: x.score, reverse=True)
        
        # ランクを設定
        for i, result in enumerate(combined_results[:top_k]):
            result.rank = i + 1
        
        return combined_results[:top_k]
    
    def _bm25_search(self, query: str) -> List[Tuple[int, float]]:
        """BM25検索"""
        results = []
        for i, article in enumerate(self.articles):
            text = f"{article.title} {article.content or ''}"
            score = self.bm25.score(query, text)
            if score > 0:
                results.append((i, score))
        
        return sorted(results, key=lambda x: x[1], reverse=True)
    
    def _semantic_search(self, query: str) -> List[Tuple[int, float]]:
        """セマンティック検索"""
        texts = []
        for article in self.articles:
            text = f"{article.title} {article.content or ''}"
            texts.append(text)
        
        return self.semantic.similarity_search(query, texts)
    
    def _entity_search(self, entities: List[str]) -> List[Tuple[int, float]]:
        """エンティティ検索"""
        return self.entity.search_by_entities(entities)
    
    def _graph_search(self, query: str) -> List[Tuple[int, float]]:
        """グラフ検索"""
        # 最初にキーワード検索で種記事を見つける
        keyword_results = self._bm25_search(query)
        if not keyword_results:
            return []
        
        # 上位の記事を種として関連記事を探索
        seed_ids = [doc_id for doc_id, _ in keyword_results[:3]]
        return self.graph.graph_search(seed_ids)
    
    def _extract_entities(self, query: str) -> List[str]:
        """クエリからエンティティを抽出（簡易版）"""
        # 固有名詞的なパターンを抽出
        entities = re.findall(r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\b', query)
        
        # 技術用語パターン
        tech_patterns = [
            r'\bGPT-?\d*\b', r'\bBERT\b', r'\bTransformer\b', r'\bLLM\b',
            r'\bAI\b', r'\bML\b', r'\bDL\b', r'\bNLP\b', r'\bCV\b'
        ]
        
        for pattern in tech_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            entities.extend(matches)
        
        return list(set(entities))
    
    def _merge_results(self, results_dict: Dict[str, List[Tuple[int, float]]]) -> List[SearchResult]:
        """複数の検索結果をマージ"""
        # 検索手法別の重み
        weights = {
            'keyword': settings.search.hybrid_weight,
            'semantic': 1.0 - settings.search.hybrid_weight,
            'entity': 0.6,
            'graph': 0.4
        }
        
        # スコア正規化のための最大値計算
        max_scores = {}
        for method, results in results_dict.items():
            if results:
                max_scores[method] = max(score for _, score in results)
            else:
                max_scores[method] = 1.0
        
        # 記事ごとのスコア統合
        article_scores = defaultdict(lambda: {'total': 0.0, 'breakdown': {}})
        
        for method, results in results_dict.items():
            weight = weights.get(method, 0.5)
            max_score = max_scores[method]
            
            for doc_id, score in results:
                normalized_score = score / max_score if max_score > 0 else 0
                weighted_score = normalized_score * weight
                
                article_scores[doc_id]['total'] += weighted_score
                article_scores[doc_id]['breakdown'][method] = weighted_score
        
        # SearchResultオブジェクトを作成
        search_results = []
        for doc_id, score_info in article_scores.items():
            if doc_id < len(self.articles):
                search_results.append(SearchResult(
                    article=self.articles[doc_id],
                    score=score_info['total'],
                    score_breakdown=score_info['breakdown'],
                    rank=0  # 後で設定
                ))
        
        return search_results
    
    def _apply_persona_optimization(self, results: List[SearchResult], persona: str) -> List[SearchResult]:
        """ペルソナ別最適化"""
        for result in results:
            if persona == 'engineer':
                result.score *= self._engineer_boost_factor(result.article)
            elif persona == 'business':
                result.score *= self._business_boost_factor(result.article)
        
        return results
    
    def _engineer_boost_factor(self, article: Article) -> float:
        """エンジニア向けブーストファクター"""
        boost = 1.0
        
        # 技術的詳細の有無でブースト
        if article.technical:
            if article.technical.code_available:
                boost *= 1.2
            if article.technical.github_repo:
                boost *= 1.15
            if article.technical.implementation_ready:
                boost *= 1.1
        
        return boost
    
    def _business_boost_factor(self, article: Article) -> float:
        """ビジネス向けブーストファクター"""
        boost = 1.0
        
        # ビジネス価値の有無でブースト
        if article.business:
            if article.business.case_studies:
                boost *= 1.2
            if article.business.roi_indicators:
                boost *= 1.15
            if article.business.funding_info:
                boost *= 1.1
        
        return boost
    
    def _apply_filters(self, results: List[SearchResult], filters: Dict) -> List[SearchResult]:
        """フィルタリングの適用"""
        filtered = []
        
        for result in results:
            article = result.article
            
            # 難易度フィルター
            if 'difficulty_level' in filters:
                if not article.technical or article.technical.difficulty_level.value != filters['difficulty_level']:
                    continue
            
            # カテゴリフィルター
            if 'category' in filters:
                if article.category != filters['category']:
                    continue
            
            # 最小スコアフィルター
            if 'min_score' in filters:
                if result.score < filters['min_score']:
                    continue
            
            # 日付範囲フィルター
            if 'date_range' in filters:
                date_range = filters['date_range']
                if article.published_date < date_range.get('start') or article.published_date > date_range.get('end'):
                    continue
            
            filtered.append(result)
        
        return filtered
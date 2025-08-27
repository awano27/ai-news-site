# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview - Daily AI News System v2.0

This is an advanced AI news intelligence platform that automatically collects, analyzes, and curates AI-related content for two distinct personas: AI engineers and AI business professionals. The system uses multi-layer evaluation algorithms, hybrid search engines, and Gemini URL Context analysis to provide high-quality, actionable intelligence.

**Key Innovation**: Beyond simple aggregation, this is a knowledge distillation system that applies 5-layer evaluation (quality, relevance, temporal value, trust, actionability) with persona-specific optimization.

## Architecture Overview

### Backend (Python 3.11+)
- **Multi-Layer Evaluator**: 5-dimensional scoring system for content quality
- **Gemini URL Context Analyzer**: AI-powered content analysis and extraction
- **Hybrid Search Engine**: BM25 + semantic + entity + graph search
- **Tier-based Source Management**: Hierarchical information source prioritization
- **Persona Optimization**: Engineer vs Business content filtering

### Frontend (React 18 + TypeScript)
- **Intelligence Dashboard**: High-density information display
- **Smart Filtering**: Persona-aware content selection
- **Score Visualization**: Transparent evaluation breakdown
- **Evidence Tracking**: Source credibility and citation management

## Build and Development Commands

### Backend Development
```bash
# Setup environment (v2.0 dependencies)
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-v2.txt

# Run full pipeline
python -m src.main

# Development mode (faster, limited analysis)
NEWS_FAST_MODE=1 python -m src.main
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev          # Development server
npm run build        # Production build
npm run type-check   # TypeScript validation
```

### Linting and Testing
```bash
# Backend
black src/ --line-length 100
isort src/
mypy src/
pytest tests/

# Frontend  
npm run lint
npm run test
```

## Essential Environment Variables

### AI Analysis (Required)
- `GEMINI_API_KEY`: Google Gemini for URL context analysis
- `GEMINI_MODEL`: Model version (default: gemini-2.5-flash-lite)

### Enhanced Features
- `EMBEDDING_MODEL`: Sentence transformer model for semantic search
- `EVALUATION_DB_URL`: PostgreSQL for evaluation storage
- `GITHUB_TOKEN`: GitHub API for trending repositories
- `X_BEARER_TOKEN`: Twitter API for social signals

### Performance Tuning
- `GEMINI_URL_CONTEXT_BATCH`: Batch size for URL analysis (default: 20)
- `SEARCH_HYBRID_WEIGHT`: BM25 vs semantic balance (default: 0.7)
- `RECOMMENDATION_THRESHOLD`: Quality filter threshold (default: 0.75)
- `HALF_LIFE_HOURS`: Content freshness decay (default: 72)

## Data Architecture

### Article Schema v2.0
- **Basic**: title, url, source, tier, dates, content
- **Technical Metadata**: difficulty, code availability, reproducibility
- **Business Metadata**: ROI indicators, case studies, implementation cost
- **Evaluation**: multi-dimensional scores with breakdown
- **Relationships**: related articles, prerequisites, follow-ups
- **Evidence**: sources, citations, bias assessment

### Persona Weighting
```python
# Engineer priorities
technical_depth: 0.35
implementation: 0.25  
novelty: 0.20
reproducibility: 0.15
community_impact: 0.05

# Business priorities  
business_impact: 0.40
roi_potential: 0.25
market_validation: 0.20
implementation_ease: 0.10
strategic_value: 0.05
```

## Quality Assurance

### Multi-Layer Evaluation
1. **Content Quality**: Structure, citations, technical depth
2. **Persona Relevance**: Engineer/business-specific value
3. **Temporal Value**: Freshness + evergreen potential  
4. **Trust Score**: E-E-A-T compliance, source credibility
5. **Actionability**: Concrete next steps, implementation guidance

### Performance Targets
- Article processing: <500ms per article
- Search response: <200ms
- UI first paint: <1.5s
- Evaluation accuracy: nDCG@10 > 0.8

## Development Workflow

### Adding New Features
1. Update schema in `src/models/schemas.py`
2. Implement evaluator logic in `src/evaluators/`
3. Add frontend types in `frontend/src/types/`
4. Create UI components with score visualization
5. Write tests covering persona-specific scenarios

### Source Integration
1. Add source to `sources.yaml` with appropriate tier
2. Implement collector in `src/collectors/`
3. Test evaluation pipeline with new content
4. Monitor quality metrics and adjust weights

## Project Structure

```
src/
├── config/          # Settings and environment management
├── models/          # Data schemas and type definitions  
├── collectors/      # Source management and data collection
├── evaluators/      # Multi-layer evaluation system
├── search/          # Hybrid search and ranking
└── utils/           # Logging, utilities

frontend/
├── src/
│   ├── components/  # React components
│   ├── hooks/       # Custom hooks  
│   ├── store/       # State management
│   ├── types/       # TypeScript definitions
│   └── utils/       # Frontend utilities
```

## Monitoring and Analytics

### Key Metrics
- Article quality distribution by source tier
- Persona-specific engagement and feedback
- Search relevance and user satisfaction
- Processing performance and error rates
- Content freshness and coverage gaps

### Quality Indicators  
- Evidence score (citation density)
- Bias neutrality assessment
- Implementation readiness ratio
- Business case study coverage
- Community validation signals

## Deployment

### GitHub Actions
- Daily content refresh at 06:25 JST
- Automated quality checks and validation
- Performance monitoring and alerting
- Fallback to cached content on errors

### Scalability Notes
- Vector database for semantic search (Qdrant/Pinecone)
- Redis caching for search results
- PostgreSQL for evaluation history
- CDN distribution for frontend assets

This system prioritizes information quality over quantity, emphasizing actionable intelligence and transparent evaluation for informed decision-making.
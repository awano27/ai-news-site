#!/usr/bin/env python3
"""
Daily AI News System v2.0 - ビルドスクリプト
要件定義書に基づいたエントリーポイント
"""
import asyncio
import sys
from pathlib import Path

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.main import main

if __name__ == "__main__":
    print("🚀 Daily AI News System v2.0")
    print("   Advanced AI Intelligence Platform")
    print("   Multi-layer evaluation • Hybrid search • Persona optimization")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Build interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Build failed: {e}")
        sys.exit(1)
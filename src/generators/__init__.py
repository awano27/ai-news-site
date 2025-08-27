"""
プレゼンテーション・レポート生成機能

このモジュールは毎日のAIニュースデータを基に、月次プレゼンテーション用の
HTMLスライドを生成する機能を提供します。
"""

from .slide_generator import SlideGenerator

__all__ = ["SlideGenerator"]
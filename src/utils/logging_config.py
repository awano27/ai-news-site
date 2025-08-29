"""
ロギング設定 v2.0
構造化ロギングとパフォーマンス監視
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import structlog

from ..config.settings import settings


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """ロギングシステムの初期化"""
    
    # ログディレクトリの作成
    log_dir = settings.root_dir / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    # ログファイル名
    log_file = log_dir / f"news-system-{datetime.now().strftime('%Y-%m-%d')}.log"
    
    # 基本設定
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # structlogの設定
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # メインロガーを取得
    logger = logging.getLogger('daily_ai_news')
    
    # 外部ライブラリのログレベルを調整
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('feedparser').setLevel(logging.WARNING)
    
    return logger


class PerformanceLogger:
    """パフォーマンス測定用ログ"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.start_times = {}
    
    def start_timer(self, operation: str):
        """タイマー開始"""
        self.start_times[operation] = datetime.now()
        self.logger.info(f"⏱️  Started: {operation}")
    
    def end_timer(self, operation: str, additional_info: Optional[dict] = None):
        """タイマー終了とログ出力"""
        if operation not in self.start_times:
            self.logger.warning(f"Timer for '{operation}' was not started")
            return
        
        elapsed = datetime.now() - self.start_times[operation]
        elapsed_ms = elapsed.total_seconds() * 1000
        
        log_data = {
            'operation': operation,
            'elapsed_ms': elapsed_ms,
            'elapsed_seconds': elapsed.total_seconds()
        }
        
        if additional_info:
            log_data.update(additional_info)
        
        self.logger.info(f"✅ Completed: {operation} ({elapsed_ms:.2f}ms)", extra=log_data)
        
        del self.start_times[operation]


def get_logger(name: str = None) -> logging.Logger:
    """ロガーの取得"""
    return logging.getLogger(name or 'daily_ai_news')
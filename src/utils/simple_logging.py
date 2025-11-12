"""
簡単なロギング設定 (structlog代替)
Python 3.13互換性対応
"""
import logging
import sys
import re
from datetime import datetime
from pathlib import Path
from typing import Optional


class SensitiveDataFilter(logging.Filter):
    """Filter to mask sensitive data like API keys in log messages"""

    # Patterns to match API keys and tokens
    SENSITIVE_PATTERNS = [
        (re.compile(r'(api[_-]?key["\']?\s*[:=]\s*["\']?)([a-zA-Z0-9_\-]{20,})(["\']?)', re.IGNORECASE), r'\1***\3'),
        (re.compile(r'(token["\']?\s*[:=]\s*["\']?)([a-zA-Z0-9_\-]{20,})(["\']?)', re.IGNORECASE), r'\1***\3'),
        (re.compile(r'(bearer\s+)([a-zA-Z0-9_\-]{20,})', re.IGNORECASE), r'\1***'),
        (re.compile(r'(password["\']?\s*[:=]\s*["\']?)([^"\']+)(["\']?)', re.IGNORECASE), r'\1***\3'),
        # Generic pattern for long alphanumeric strings that look like keys
        (re.compile(r'\b([a-zA-Z0-9_\-]{32,})\b'), r'***'),
    ]

    def filter(self, record):
        """Mask sensitive data in log message"""
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            message = record.msg
            for pattern, replacement in self.SENSITIVE_PATTERNS:
                message = pattern.sub(replacement, message)
            record.msg = message
        return True

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """ロギングシステムの初期化（簡易版）"""
    
    # ログディレクトリの作成
    try:
        from ..config.settings import settings
        log_dir = settings.root_dir / 'logs'
    except:
        log_dir = Path(__file__).parent.parent.parent / 'logs'
    
    log_dir.mkdir(exist_ok=True)
    
    # ログファイル名
    log_file = log_dir / f"news-system-{datetime.now().strftime('%Y-%m-%d')}.log"
    
    # カスタムフォーマッター
    class ColoredFormatter(logging.Formatter):
        """色付きログフォーマッター"""
        
        COLORS = {
            'DEBUG': '\033[36m',    # Cyan
            'INFO': '\033[32m',     # Green  
            'WARNING': '\033[33m',  # Yellow
            'ERROR': '\033[31m',    # Red
            'CRITICAL': '\033[35m', # Magenta
            'RESET': '\033[0m'      # Reset
        }
        
        def format(self, record):
            # 色付きレベル名
            if hasattr(record, 'levelname'):
                color = self.COLORS.get(record.levelname, '')
                reset = self.COLORS['RESET']
                record.levelname = f"{color}{record.levelname}{reset}"
            
            return super().format(record)
    
    # フォーマッター設定
    console_formatter = ColoredFormatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    file_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # ハンドラー設定
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(SensitiveDataFilter())  # Add security filter

    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(file_formatter)
    file_handler.addFilter(SensitiveDataFilter())  # Add security filter

    # ロガー設定
    logger = logging.getLogger('daily_ai_news')
    logger.setLevel(getattr(logging, log_level.upper()))
    logger.handlers.clear()  # 既存のハンドラーをクリア
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # 外部ライブラリのログレベルを調整
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('feedparser').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """ロガーの取得"""
    return logging.getLogger(name or 'daily_ai_news')


class PerformanceLogger:
    """パフォーマンス測定用ログ（簡易版）"""
    
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
        
        info_str = f"✅ Completed: {operation} ({elapsed_ms:.2f}ms)"
        if additional_info:
            info_parts = [f"{k}={v}" for k, v in additional_info.items()]
            info_str += f" [{', '.join(info_parts)}]"
        
        self.logger.info(info_str)
        del self.start_times[operation]
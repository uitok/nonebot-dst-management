"""
AI 辅助功能模块

提供统一的 AI 调用基础能力与 Provider 实现。
"""

from .base import (
    AIAuthError,
    AIError,
    AIProviderError,
    AIResponseParseError,
    AIRateLimitError,
    AITimeoutError,
    AITransientError,
    ChatMessage,
    RetryPolicy,
    format_ai_error,
)
from .client import AIClient, ClaudeProvider, MockProvider, OllamaProvider, OpenAIProvider
from .analyzer import ServerConfigAnalyzer
from .archive_analyzer import ArchiveAnalyzer
from .mod_parser import ModConfigParser
from .qa import QASystem
from .recommender import ModRecommender
from .config import AIConfig

__all__ = [
    "AIAuthError",
    "AIError",
    "AIProviderError",
    "AIResponseParseError",
    "AIRateLimitError",
    "AITimeoutError",
    "AITransientError",
    "ChatMessage",
    "RetryPolicy",
    "format_ai_error",
    "AIClient",
    "ClaudeProvider",
    "MockProvider",
    "OllamaProvider",
    "OpenAIProvider",
    "ServerConfigAnalyzer",
    "ArchiveAnalyzer",
    "ModConfigParser",
    "QASystem",
    "ModRecommender",
    "AIConfig",
]

"""
分析器配置管理
"""
import os
from typing import Dict, Optional
from utils.config_loader import config


class AnalyzerConfig:
    """分析器配置类"""
    
    def __init__(self):
        """初始化配置"""
        self._config = config._config.get('analyzer', {})
        self.deepseek_config = self._config.get('deepseek', {})
    
    def get_deepseek_config(self) -> Dict:
        """获取 DeepSeek 配置"""
        return {
            'api_key': os.getenv('DEEPSEEK_API_KEY', self.deepseek_config.get('api_key', '')),
            'api_url': self.deepseek_config.get('api_url', 'https://api.deepseek.com/v1/chat/completions'),
            'model': self.deepseek_config.get('model', 'deepseek-chat'),
            'timeout': self.deepseek_config.get('timeout', 30),
            'max_retries': self.deepseek_config.get('max_retries', 3),
            'cache_enabled': self.deepseek_config.get('cache_enabled', True),
            'cache_ttl_hours': self.deepseek_config.get('cache_ttl_hours', 24),
            'batch_size': self.deepseek_config.get('batch_size', 5),
            'batch_delay': self.deepseek_config.get('batch_delay', 1.0)
        }

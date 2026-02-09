"""
引擎配置
"""
import sys
import os
from typing import Dict, List, Optional, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.config_loader import config


class EngineConfig:
    """引擎配置"""
    
    def __init__(self, config_dict: Optional[Dict] = None):
        """
        初始化配置
        
        Args:
            config_dict: 配置字典，如果为None则从config.json加载
        """
        if config_dict is None:
            # 使用全局config实例获取引擎配置
            engine_config = config.get_engine_config()
        else:
            engine_config = config_dict
        
        # 基础配置
        self.max_concurrent_tasks = engine_config.get('max_concurrent_tasks', 10)
        self.task_timeout = engine_config.get('task_timeout', 3600)
        
        # 插件配置
        self.plugins = engine_config.get('plugins', [])
        
        # 可观测性配置
        self.observability = engine_config.get('observability', {
            'logging': {
                'level': 'INFO',
                'format': 'json',
                'file': 'logs/engine.log'
            },
            'metrics': {
                'enabled': True,
                'interval': 60
            },
            'tracing': {
                'enabled': True
            }
        })
        
        # 容错配置
        self.fault_tolerance = engine_config.get('fault_tolerance', {
            'max_retries': 3,
            'retry_delay': 1.0,
            'backoff_factor': 2.0,
            'circuit_breaker': {
                'enabled': True,
                'failure_threshold': 5,
                'timeout': 60
            }
        })

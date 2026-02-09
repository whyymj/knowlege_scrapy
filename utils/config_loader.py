"""
统一配置加载模块
支持从 config.json 和环境变量读取配置
环境变量优先级高于配置文件
"""
import json
import os
from pathlib import Path
from typing import Dict, Any


class ConfigLoader:
    """配置加载器"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        # 获取项目根目录
        current_dir = Path(__file__).parent
        project_root = current_dir.parent
        
        # 查找 config.json
        config_file = project_root / 'config.json'
        
        if not config_file.exists():
            raise FileNotFoundError(f'配置文件不存在: {config_file}')
        
        # 读取配置文件
        with open(config_file, 'r', encoding='utf-8') as f:
            self._config = json.load(f)
        
        # 应用环境变量覆盖
        self._apply_env_overrides()
    
    def _apply_env_overrides(self):
        """应用环境变量覆盖配置"""
        # 数据库配置
        if os.getenv('MYSQL_HOST'):
            self._config['database']['host'] = os.getenv('MYSQL_HOST')
        if os.getenv('MYSQL_PORT'):
            self._config['database']['port'] = int(os.getenv('MYSQL_PORT'))
        if os.getenv('MYSQL_DB'):
            self._config['database']['db'] = os.getenv('MYSQL_DB')
        if os.getenv('MYSQL_USER'):
            self._config['database']['user'] = os.getenv('MYSQL_USER')
        if os.getenv('MYSQL_PASSWORD'):
            self._config['database']['password'] = os.getenv('MYSQL_PASSWORD')
        
        # 后端配置
        if os.getenv('BACKEND_HOST'):
            self._config['backend']['host'] = os.getenv('BACKEND_HOST')
        if os.getenv('BACKEND_PORT'):
            self._config['backend']['port'] = int(os.getenv('BACKEND_PORT'))
        if os.getenv('FLASK_ENV'):
            self._config['backend']['debug'] = os.getenv('FLASK_ENV') == 'development'
        
        # 前端配置
        if os.getenv('FRONTEND_PORT'):
            self._config['frontend']['port'] = int(os.getenv('FRONTEND_PORT'))
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值
        支持点号分隔的路径，如 'database.host'
        """
        keys = key_path.split('.')
        value = self._config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_database_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        return self._config.get('database', {})
    
    def get_backend_config(self) -> Dict[str, Any]:
        """获取后端配置"""
        return self._config.get('backend', {})
    
    def get_scrapy_config(self) -> Dict[str, Any]:
        """获取 Scrapy 配置"""
        return self._config.get('scrapy', {})
    
    def get_docker_config(self) -> Dict[str, Any]:
        """获取 Docker 配置"""
        return self._config.get('docker', {})
    
    def reload(self):
        """重新加载配置"""
        self._config = None
        self._load_config()


# 全局配置实例
config = ConfigLoader()

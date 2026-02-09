"""
可观测性管理
"""
import logging
import json
import time
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
from datetime import datetime


class ObservabilityManager:
    """可观测性管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化可观测性管理器
        
        Args:
            config: 可观测性配置
        """
        self.config = config
        self.metrics: Dict[str, Any] = {}
        self.traces: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []
        
        # 初始化日志
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志"""
        log_config = self.config.get('logging', {})
        level = getattr(logging, log_config.get('level', 'INFO'))
        format_type = log_config.get('format', 'json')
        log_file = log_config.get('file')
        
        # 创建logger
        self.logger = logging.getLogger('crawler_engine')
        self.logger.setLevel(level)
        
        # 清除现有处理器
        self.logger.handlers.clear()
        
        # 控制台处理器
        if format_type == 'json':
            handler = logging.StreamHandler()
            handler.setFormatter(JsonFormatter())
        else:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
        
        self.logger.addHandler(handler)
        
        # 文件处理器
        if log_file:
            # 确保日志目录存在
            import os
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            if format_type == 'json':
                file_handler.setFormatter(JsonFormatter())
            else:
                file_handler.setFormatter(logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                ))
            self.logger.addHandler(file_handler)
    
    def initialize(self):
        """初始化可观测性"""
        if self.config.get('metrics', {}).get('enabled', True):
            self._start_metrics_collection()
    
    def _start_metrics_collection(self):
        """启动指标收集"""
        # 初始化指标
        self.metrics = {
            'tasks_started': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'items_processed': 0,
            'errors_count': 0
        }
    
    @contextmanager
    def start_trace(self, trace_id: str):
        """开始追踪"""
        trace = {
            'id': trace_id,
            'start_time': time.time(),
            'stages': []
        }
        
        try:
            yield trace
        finally:
            trace['end_time'] = time.time()
            trace['duration'] = trace['end_time'] - trace['start_time']
            self.traces.append(trace)
    
    @contextmanager
    def start_stage(self, stage_name: str):
        """开始阶段追踪"""
        stage = {
            'name': stage_name,
            'start_time': time.time()
        }
        
        try:
            yield stage
        finally:
            stage['end_time'] = time.time()
            stage['duration'] = stage['end_time'] - stage['start_time']
    
    def record_metric(self, metric_name: str, value: Any = None, tags: Optional[Dict] = None):
        """
        记录指标
        
        Args:
            metric_name: 指标名称
            value: 指标值（None表示递增计数器，dict表示合并字典，其他表示直接设置）
            tags: 标签（暂未使用）
        """
        if value is None:
            # 递增计数器（仅当指标是数字类型时）
            if metric_name not in self.metrics:
                self.metrics[metric_name] = 0
            elif isinstance(self.metrics[metric_name], dict):
                # 如果已经是字典，不能递增，记录警告
                self.logger.warning(f"指标 {metric_name} 是字典类型，无法递增，跳过")
                return
            self.metrics[metric_name] += 1
        elif isinstance(value, dict):
            # 合并字典指标
            if metric_name not in self.metrics or not isinstance(self.metrics[metric_name], dict):
                # 如果之前是数字或其他类型，转换为字典
                self.metrics[metric_name] = {}
            self.metrics[metric_name].update(value)
        else:
            # 直接设置值
            self.metrics[metric_name] = value
    
    def record_error(self, context: str, error: Exception):
        """
        记录错误
        
        Args:
            context: 错误上下文
            error: 异常对象
        """
        error_record = {
            'timestamp': datetime.now().isoformat(),
            'context': context,
            'error_type': type(error).__name__,
            'error_message': str(error)
        }
        
        self.errors.append(error_record)
        self.metrics['errors_count'] = len(self.errors)
        
        self.logger.error(json.dumps(error_record))
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取指标"""
        return self.metrics.copy()
    
    def get_traces(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取追踪记录"""
        return self.traces[-limit:]
    
    def get_errors(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取错误记录"""
        return self.errors[-limit:]
    
    def shutdown(self):
        """关闭可观测性"""
        # 输出最终指标
        self.logger.info(json.dumps({
            'type': 'metrics_summary',
            'metrics': self.metrics
        }))


class JsonFormatter(logging.Formatter):
    """JSON格式化器"""
    
    def format(self, record):
        """格式化日志记录为JSON"""
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage()
        }
        
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)

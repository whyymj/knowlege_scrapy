"""
容错恢复管理
"""
import asyncio
import logging
from typing import Dict, Optional, Callable, Any
from datetime import datetime, timedelta


class FaultToleranceManager:
    """容错管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化容错管理器
        
        Args:
            config: 容错配置
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 熔断器状态
        self.circuit_breakers: Dict[str, Dict] = {}
        
        # 重试统计
        self.retry_stats: Dict[str, int] = {}
    
    def initialize(self):
        """初始化容错管理器"""
        circuit_config = self.config.get('circuit_breaker', {})
        if circuit_config.get('enabled', True):
            self.logger.info("熔断器已启用")
    
    async def execute_with_retry(
        self,
        func: Callable,
        max_retries: Optional[int] = None,
        retry_delay: Optional[float] = None,
        backoff_factor: Optional[float] = None
    ) -> Any:
        """
        带重试的执行
        
        Args:
            func: 要执行的函数
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            backoff_factor: 退避因子
            
        Returns:
            执行结果
        """
        max_retries = max_retries or self.config.get('max_retries', 3)
        retry_delay = retry_delay or self.config.get('retry_delay', 1.0)
        backoff_factor = backoff_factor or self.config.get('backoff_factor', 2.0)
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func()
                else:
                    return func()
            except Exception as e:
                last_exception = e
                
                if attempt < max_retries:
                    delay = retry_delay * (backoff_factor ** attempt)
                    self.logger.warning(
                        f"执行失败，{delay:.2f}秒后重试 ({attempt + 1}/{max_retries}): {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(f"执行失败，已达最大重试次数: {e}")
        
        raise last_exception
    
    async def should_continue(self, stage: str, error: Exception) -> bool:
        """
        判断是否应该继续执行
        
        Args:
            stage: 阶段名称
            error: 错误
            
        Returns:
            是否继续
        """
        # 检查熔断器
        if self._is_circuit_open(stage):
            self.logger.warning(f"熔断器已打开，跳过阶段: {stage}")
            return False
        
        # 根据错误类型决定
        error_type = type(error).__name__
        
        # 致命错误，不继续
        fatal_errors = ['ValueError', 'KeyError', 'AttributeError']
        if error_type in fatal_errors:
            return False
        
        return True
    
    def _is_circuit_open(self, key: str) -> bool:
        """
        检查熔断器是否打开
        
        Args:
            key: 熔断器键
            
        Returns:
            是否打开
        """
        circuit_config = self.config.get('circuit_breaker', {})
        if not circuit_config.get('enabled', True):
            return False
        
        if key not in self.circuit_breakers:
            self.circuit_breakers[key] = {
                'state': 'closed',  # closed, open, half_open
                'failure_count': 0,
                'last_failure_time': None
            }
        
        circuit = self.circuit_breakers[key]
        
        # 检查是否需要重置
        timeout = circuit_config.get('timeout', 60)
        if circuit['state'] == 'open':
            if circuit['last_failure_time']:
                elapsed = (datetime.now() - circuit['last_failure_time']).total_seconds()
                if elapsed >= timeout:
                    circuit['state'] = 'half_open'
                    circuit['failure_count'] = 0
        
        return circuit['state'] == 'open'
    
    async def handle_failure(self, context: str, error: Exception):
        """
        处理失败
        
        Args:
            context: 上下文
            error: 错误
        """
        # 更新熔断器
        circuit_config = self.config.get('circuit_breaker', {})
        if circuit_config.get('enabled', True):
            if context not in self.circuit_breakers:
                self.circuit_breakers[context] = {
                    'state': 'closed',
                    'failure_count': 0,
                    'last_failure_time': None
                }
            
            circuit = self.circuit_breakers[context]
            circuit['failure_count'] += 1
            circuit['last_failure_time'] = datetime.now()
            
            failure_threshold = circuit_config.get('failure_threshold', 5)
            if circuit['failure_count'] >= failure_threshold:
                circuit['state'] = 'open'
                self.logger.warning(f"熔断器打开: {context}")
    
    def record_success(self, context: str):
        """
        记录成功
        
        Args:
            context: 上下文
        """
        if context in self.circuit_breakers:
            circuit = self.circuit_breakers[context]
            if circuit['state'] == 'half_open':
                circuit['state'] = 'closed'
                circuit['failure_count'] = 0
                self.logger.info(f"熔断器关闭: {context}")

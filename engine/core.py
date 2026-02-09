"""
通用抓取引擎核心
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from .config import EngineConfig
from .pipeline import CrawlerPipeline
from .registry import ComponentRegistry
from .observability import ObservabilityManager
from .fault_tolerance import FaultToleranceManager


class CrawlerEngine:
    """通用抓取引擎"""
    
    def __init__(self, config: Optional[EngineConfig] = None):
        """
        初始化抓取引擎
        
        Args:
            config: 引擎配置
        """
        self.config = config or EngineConfig()
        self.logger = logging.getLogger(__name__)
        
        # 组件注册表
        self.registry = ComponentRegistry()
        
        # 可观测性管理器
        self.observability = ObservabilityManager(self.config.observability)
        
        # 容错管理器
        self.fault_tolerance = FaultToleranceManager(self.config.fault_tolerance)
        
        # 管道实例
        self.pipelines: Dict[str, CrawlerPipeline] = {}
        
        # 运行状态
        self.running = False
        self.tasks: Dict[str, Any] = {}
    
    def initialize(self):
        """初始化引擎"""
        self.logger.info("初始化抓取引擎...")
        
        # 加载组件
        self._load_components()
        
        # 初始化可观测性
        self.observability.initialize()
        
        # 初始化容错恢复
        self.fault_tolerance.initialize()
        
        self.logger.info("抓取引擎初始化完成")
    
    def _load_components(self):
        """加载组件"""
        self.logger.info("加载组件...")
        
        # 注册内置组件
        from components.adapters import HttpAdapter, ApiAdapter
        from components.parsers import HtmlParser, JsonParser
        from components.extractors import CssExtractor, XPathExtractor, RegexExtractor
        from components.transformers import DataTransformer, NormalizerTransformer
        from components.outputs import DatabaseOutput, FileOutput
        from components.validators import DataValidator, QualityValidator
        from components.filters import AIFilter
        
        # 注册源适配器
        self.registry.register_adapter('http', HttpAdapter)
        self.registry.register_adapter('api', ApiAdapter)
        
        # 注册解析器
        self.registry.register_parser('html', HtmlParser)
        self.registry.register_parser('json', JsonParser)
        
        # 注册提取器
        self.registry.register_extractor('css', CssExtractor)
        self.registry.register_extractor('xpath', XPathExtractor)
        self.registry.register_extractor('regex', RegexExtractor)
        
        # 注册转换器
        self.registry.register_transformer('data', DataTransformer)
        self.registry.register_transformer('normalizer', NormalizerTransformer)
        
        # 注册输出器
        self.registry.register_output('database', DatabaseOutput)
        self.registry.register_output('file', FileOutput)
        
        # 注册验证器
        self.registry.register_validator('data', DataValidator)
        self.registry.register_validator('quality', QualityValidator)
        
        # 注册筛选器
        self.registry.register_filter('ai', AIFilter)
        
        # 加载自定义插件
        self._load_plugins()
        
        self.logger.info(f"组件加载完成，共 {len(self.registry.get_all_components())} 个组件")
    
    def _load_plugins(self):
        """加载自定义插件"""
        plugins = self.config.plugins or []
        for plugin_config in plugins:
            try:
                plugin_path = plugin_config.get('path')
                plugin_name = plugin_config.get('name')
                
                # 动态加载插件
                import importlib.util
                spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
                plugin_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(plugin_module)
                
                # 注册插件组件
                if hasattr(plugin_module, 'register_components'):
                    plugin_module.register_components(self.registry)
                
                self.logger.info(f"插件加载成功: {plugin_name}")
            except Exception as e:
                self.logger.error(f"插件加载失败: {plugin_config.get('name')}, 错误: {e}")
    
    def create_pipeline(self, task_config: Dict[str, Any], progress_callback=None) -> CrawlerPipeline:
        """
        创建抓取管道
        
        Args:
            task_config: 任务配置
            progress_callback: 进度更新回调函数
            
        Returns:
            抓取管道实例
        """
        task_id = task_config.get('id', f"task_{datetime.now().timestamp()}")
        
        pipeline = CrawlerPipeline(
            task_id=task_id,
            config=task_config,
            registry=self.registry,
            observability=self.observability,
            fault_tolerance=self.fault_tolerance,
            progress_callback=progress_callback
        )
        
        self.pipelines[task_id] = pipeline
        return pipeline
    
    async def run_task(self, task_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行抓取任务
        
        Args:
            task_config: 任务配置
            
        Returns:
            任务结果
        """
        task_id = task_config.get('id')
        
        with self.observability.start_trace(task_id):
            try:
                # 创建管道
                pipeline = self.create_pipeline(task_config)
                
                # 记录任务开始
                self.observability.record_metric('task_started', {'task_id': task_id})
                
                # 执行管道
                result = await self.fault_tolerance.execute_with_retry(
                    pipeline.run,
                    max_retries=self.config.fault_tolerance.get('max_retries', 3)
                )
                
                # 记录任务完成
                self.observability.record_metric('task_completed', {
                    'task_id': task_id,
                    'items_count': result.get('items_count', 0)
                })
                
                return result
                
            except Exception as e:
                self.logger.error(f"任务执行失败: {task_id}, 错误: {e}")
                self.observability.record_error(task_id, e)
                
                # 容错处理
                await self.fault_tolerance.handle_failure(task_id, e)
                
                raise
    
    async def run_tasks(self, tasks_config: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量运行任务
        
        Args:
            tasks_config: 任务配置列表
            
        Returns:
            任务结果列表
        """
        results = []
        
        # 并发控制
        semaphore = asyncio.Semaphore(self.config.max_concurrent_tasks)
        
        async def run_with_semaphore(task_config):
            async with semaphore:
                return await self.run_task(task_config)
        
        tasks = [run_with_semaphore(task_config) for task_config in tasks_config]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return results
    
    def start(self):
        """启动引擎"""
        if self.running:
            self.logger.warning("引擎已在运行")
            return
        
        self.initialize()
        self.running = True
        self.logger.info("抓取引擎已启动")
    
    def stop(self):
        """停止引擎"""
        if not self.running:
            return
        
        self.running = False
        
        # 停止所有管道
        for pipeline in self.pipelines.values():
            pipeline.stop()
        
        # 关闭可观测性
        self.observability.shutdown()
        
        self.logger.info("抓取引擎已停止")
    
    def get_status(self) -> Dict[str, Any]:
        """获取引擎状态"""
        return {
            'running': self.running,
            'pipelines_count': len(self.pipelines),
            'components_count': len(self.registry.get_all_components()),
            'metrics': self.observability.get_metrics()
        }
    
    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop()

"""
抽象抓取管道
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from .registry import ComponentRegistry
from .observability import ObservabilityManager
from .fault_tolerance import FaultToleranceManager

# 进度更新回调函数类型
ProgressCallback = Optional[Callable[[str, Dict[str, Any]], None]]


class PipelineStage(Enum):
    """管道阶段"""
    REQUEST_GENERATION = "request_generation"
    PAGE_FETCHING = "page_fetching"
    CONTENT_PARSING = "content_parsing"
    DATA_EXTRACTION = "data_extraction"
    AI_FILTERING = "ai_filtering"
    DATA_CLEANING = "data_cleaning"
    RESULT_OUTPUT = "result_output"


class CrawlerPipeline:
    """抽象抓取管道"""
    
    def __init__(
        self,
        task_id: str,
        config: Dict[str, Any],
        registry: ComponentRegistry,
        observability: ObservabilityManager,
        fault_tolerance: FaultToleranceManager,
        progress_callback: ProgressCallback = None
    ):
        """
        初始化管道
        
        Args:
            task_id: 任务ID
            config: 任务配置
            registry: 组件注册表
            observability: 可观测性管理器
            fault_tolerance: 容错管理器
            progress_callback: 进度更新回调函数
        """
        self.task_id = task_id
        self.config = config
        self.registry = registry
        self.observability = observability
        self.fault_tolerance = fault_tolerance
        self.progress_callback = progress_callback
        
        self.logger = logging.getLogger(f"{__name__}.{task_id}")
        
        # 管道阶段处理器
        self.stage_handlers: Dict[PipelineStage, Callable] = {
            PipelineStage.REQUEST_GENERATION: self._request_generation,
            PipelineStage.PAGE_FETCHING: self._page_fetching,
            PipelineStage.CONTENT_PARSING: self._content_parsing,
            PipelineStage.DATA_EXTRACTION: self._data_extraction,
            PipelineStage.AI_FILTERING: self._ai_filtering,
            PipelineStage.DATA_CLEANING: self._data_cleaning,
            PipelineStage.RESULT_OUTPUT: self._result_output
        }
        
        # 运行状态
        self.running = False
        self.context: Dict[str, Any] = {}
        
        # 阶段总数（用于计算进度）
        self.total_stages = len(PipelineStage)
    
    async def run(self) -> Dict[str, Any]:
        """
        运行管道
        
        Returns:
            执行结果
        """
        self.running = True
        self.context = {
            'task_id': self.task_id,
            'config': self.config,
            'items': [],
            'errors': []
        }
        
        try:
            # 按顺序执行各个阶段
            stage_index = 0
            for stage in PipelineStage:
                if not self.running:
                    break
                
                stage_index += 1
                stage_name = stage.value
                self.logger.info(f"执行阶段: {stage_name}")
                
                # 更新进度
                self._update_progress(stage_name, stage_index, {
                    'stage': stage_name,
                    'stage_index': stage_index,
                    'total_stages': self.total_stages,
                    'progress_percentage': int((stage_index / self.total_stages) * 100),
                    'items_count': len(self.context.get('items', [])),
                    'errors_count': len(self.context.get('errors', []))
                })
                
                with self.observability.start_stage(stage_name):
                    try:
                        handler = self.stage_handlers[stage]
                        await handler()
                        
                        # 阶段完成后更新进度
                        self._update_progress(stage_name, stage_index, {
                            'stage': stage_name,
                            'stage_index': stage_index,
                            'total_stages': self.total_stages,
                            'progress_percentage': int((stage_index / self.total_stages) * 100),
                            'items_count': len(self.context.get('items', [])),
                            'errors_count': len(self.context.get('errors', [])),
                            'status': 'completed'
                        })
                    except Exception as e:
                        self.logger.error(f"阶段执行失败: {stage_name}, 错误: {e}")
                        self.context['errors'].append({
                            'stage': stage_name,
                            'error': str(e)
                        })
                        
                        # 更新进度（错误状态）
                        self._update_progress(stage_name, stage_index, {
                            'stage': stage_name,
                            'stage_index': stage_index,
                            'total_stages': self.total_stages,
                            'progress_percentage': int((stage_index / self.total_stages) * 100),
                            'items_count': len(self.context.get('items', [])),
                            'errors_count': len(self.context.get('errors', [])),
                            'status': 'error',
                            'error': str(e)
                        })
                        
                        # 容错处理
                        if not await self.fault_tolerance.should_continue(stage_name, e):
                            raise
            
            return {
                'task_id': self.task_id,
                'items_count': len(self.context['items']),
                'errors_count': len(self.context['errors']),
                'items': self.context['items'],
                'errors': self.context['errors']  # 返回错误列表，供后端保存日志
            }
            
        finally:
            self.running = False
    
    def _update_progress(self, stage_name: str, stage_index: int, progress_data: Dict[str, Any]):
        """
        更新任务进度
        
        Args:
            stage_name: 当前阶段名称
            stage_index: 当前阶段索引
            progress_data: 进度数据
        """
        if self.progress_callback:
            try:
                self.progress_callback(self.task_id, progress_data)
            except Exception as e:
                self.logger.warning(f"进度更新回调失败: {e}")
    
    async def _request_generation(self):
        """请求生成阶段"""
        source_config = self.config.get('source', {})
        adapter_type = source_config.get('type', 'http')
        
        # 获取源适配器
        adapter_class = self.registry.get_adapter(adapter_type)
        if not adapter_class:
            raise ValueError(f"未找到适配器: {adapter_type}")
        
        adapter = adapter_class(source_config)
        
        # 生成请求
        requests = await adapter.generate_requests(self.config)
        self.context['requests'] = requests
        
        self.logger.info(f"生成 {len(requests)} 个请求")
    
    async def _page_fetching(self):
        """页面获取阶段"""
        requests = self.context.get('requests', [])
        source_config = self.config.get('source', {})
        adapter_type = source_config.get('type', 'http')
        
        adapter_class = self.registry.get_adapter(adapter_type)
        adapter = adapter_class(source_config)
        
        # 并发获取页面
        pages = []
        semaphore = asyncio.Semaphore(self.config.get('concurrency', 5))
        
        async def fetch_with_semaphore(request):
            async with semaphore:
                return await adapter.fetch(request)
        
        tasks = [fetch_with_semaphore(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"页面获取失败: {result}")
                self.context['errors'].append({
                    'stage': 'page_fetching',
                    'error': str(result)
                })
            else:
                pages.append(result)
        
        self.context['pages'] = pages
        self.logger.info(f"获取 {len(pages)} 个页面")
    
    async def _content_parsing(self):
        """内容解析阶段"""
        pages = self.context.get('pages', [])
        parser_config = self.config.get('parser', {})
        parser_type = parser_config.get('type', 'html')
        
        parser_class = self.registry.get_parser(parser_type)
        if not parser_class:
            raise ValueError(f"未找到解析器: {parser_type}")
        
        parser = parser_class(parser_config)
        
        # 解析页面
        parsed_contents = []
        for page in pages:
            try:
                content = await parser.parse(page)
                parsed_contents.append(content)
            except Exception as e:
                self.logger.error(f"解析失败: {e}")
                self.context['errors'].append({
                    'stage': 'content_parsing',
                    'error': str(e)
                })
        
        self.context['parsed_contents'] = parsed_contents
        self.logger.info(f"解析 {len(parsed_contents)} 个页面")
    
    async def _data_extraction(self):
        """数据提取阶段"""
        parsed_contents = self.context.get('parsed_contents', [])
        extractor_config = self.config.get('extractor', {})
        extractor_type = extractor_config.get('type', 'css')
        
        extractor_class = self.registry.get_extractor(extractor_type)
        if not extractor_class:
            raise ValueError(f"未找到提取器: {extractor_type}")
        
        extractor = extractor_class(extractor_config)
        
        # 提取数据
        extracted_data = []
        total_contents = len(parsed_contents)
        
        for idx, content in enumerate(parsed_contents):
            try:
                data = await extractor.extract(content, self.config.get('fields', {}))
                if isinstance(data, list):
                    for item in data:
                        if item and isinstance(item, dict):
                            extracted_data.append(item)
                            # 更新进度，包含提取到的文章标题
                            title = item.get('title', '') or item.get('url', '')[:50] or '未知标题'
                            self._update_progress('data_extraction', 0, {
                                'stage': 'data_extraction',
                                'items_count': len(extracted_data),
                                'latest_title': title[:100],  # 限制标题长度
                                'progress_percentage': int((idx + 1) / total_contents * 50) if total_contents > 0 else 0
                            })
                else:
                    if data and isinstance(data, dict):
                        extracted_data.append(data)
                        # 更新进度，包含提取到的文章标题
                        title = data.get('title', '') or data.get('url', '')[:50] or '未知标题'
                        self._update_progress('data_extraction', 0, {
                            'stage': 'data_extraction',
                            'items_count': len(extracted_data),
                            'latest_title': title[:100],  # 限制标题长度
                            'progress_percentage': int((idx + 1) / total_contents * 50) if total_contents > 0 else 0
                        })
            except Exception as e:
                self.logger.error(f"提取失败: {e}")
                self.context['errors'].append({
                    'stage': 'data_extraction',
                    'error': str(e)
                })
        
        self.context['extracted_data'] = extracted_data
        self.logger.info(f"提取 {len(extracted_data)} 条数据")
        
        # 提取完成后更新一次进度
        if extracted_data:
            # 获取最后一条数据的标题
            last_item = extracted_data[-1]
            last_title = ''
            if isinstance(last_item, dict):
                last_title = last_item.get('title', '') or last_item.get('url', '')[:50] or '未知标题'
            
            self._update_progress('data_extraction', 0, {
                'stage': 'data_extraction',
                'items_count': len(extracted_data),
                'latest_title': last_title[:100] if last_title else '',
                'progress_percentage': 50
            })
    
    async def _ai_filtering(self):
        """AI筛选阶段 - 根据AI描述筛选文章"""
        extracted_data = self.context.get('extracted_data', [])
        filter_config = self.config.get('filter', {})
        
        # 如果没有配置筛选器，跳过
        if not filter_config or not filter_config.get('enabled', False):
            self.logger.info("AI筛选未启用，跳过筛选阶段")
            self.context['filtered_data'] = extracted_data
            return
        
        filter_type = filter_config.get('type', 'ai')
        filter_class = self.registry.get_filter(filter_type)
        
        if not filter_class:
            self.logger.warning(f"未找到筛选器: {filter_type}，跳过筛选")
            self.context['filtered_data'] = extracted_data
            return
        
        # 创建筛选器实例
        filter_instance = filter_class(filter_config)
        
        # 执行筛选
        try:
            filtered_data = await filter_instance.filter(extracted_data)
            self.context['filtered_data'] = filtered_data
            self.logger.info(f"AI筛选完成，原始: {len(extracted_data)}, 通过: {len(filtered_data)}")
        except Exception as e:
            self.logger.error(f"AI筛选失败: {e}")
            self.context['errors'].append({
                'stage': 'ai_filtering',
                'error': str(e)
            })
            # 筛选失败时，保留所有数据（容错）
            self.context['filtered_data'] = extracted_data
    
    async def _data_cleaning(self):
        """数据清洗阶段"""
        # 使用筛选后的数据（如果有），否则使用提取的数据
        extracted_data = self.context.get('filtered_data', self.context.get('extracted_data', []))
        transformer_config = self.config.get('transformer', {})
        
        # 应用转换器
        transformers = []
        for tf_config in transformer_config.get('pipeline', []):
            tf_type = tf_config.get('type')
            tf_class = self.registry.get_transformer(tf_type)
            if tf_class:
                transformers.append(tf_class(tf_config))
        
        # 清洗数据
        cleaned_data = extracted_data
        for transformer in transformers:
            cleaned_data = [transformer.transform(item) for item in cleaned_data]
        
        # 验证数据
        validator_config = self.config.get('validator', {})
        validators = []
        for vd_config in validator_config.get('pipeline', []):
            vd_type = vd_config.get('type')
            vd_class = self.registry.get_validator(vd_type)
            if vd_class:
                validators.append(vd_class(vd_config))
        
        validated_data = []
        for item in cleaned_data:
            valid = True
            for validator in validators:
                if not validator.validate(item):
                    valid = False
                    break
            if valid:
                validated_data.append(item)
        
        self.context['items'] = validated_data
        self.logger.info(f"清洗后剩余 {len(validated_data)} 条有效数据")
    
    async def _result_output(self):
        """结果输出阶段"""
        items = self.context.get('items', [])
        output_config = self.config.get('output', {})
        output_type = output_config.get('type', 'database')
        
        output_class = self.registry.get_output(output_type)
        if not output_class:
            raise ValueError(f"未找到输出器: {output_type}")
        
        output = output_class(output_config)
        
        # 输出数据
        await output.output(items)
        
        self.logger.info(f"输出 {len(items)} 条数据")
    
    def stop(self):
        """停止管道"""
        self.running = False

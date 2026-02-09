"""
DeepSeek API 集成模块
"""
import json
import time
import hashlib
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import requests
from functools import lru_cache


class DeepSeekAnalyzer:
    """DeepSeek API 分析器"""
    
    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None, config: Optional[Dict] = None):
        """
        初始化 DeepSeek 分析器
        
        Args:
            api_key: DeepSeek API 密钥（可选，优先使用）
            api_url: API 端点URL（可选）
            config: 配置字典（可选）
        """
        # 从配置读取
        if config:
            cfg = config
        else:
            # 尝试从全局配置读取
            try:
                from .config import AnalyzerConfig
                analyzer_config = AnalyzerConfig()
                cfg = analyzer_config.get_deepseek_config()
            except:
                cfg = {}
        
        self.api_key = api_key or cfg.get('api_key') or self._get_env('DEEPSEEK_API_KEY', '')
        self.api_url = api_url or cfg.get('api_url') or 'https://api.deepseek.com/v1/chat/completions'
        self.model = cfg.get('model', 'deepseek-chat')
        self.timeout = cfg.get('timeout', 30)
        self.max_retries = cfg.get('max_retries', 3)
        self.cache_enabled = cfg.get('cache_enabled', True)
        cache_ttl_hours = cfg.get('cache_ttl_hours', 24)
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        self.batch_size = cfg.get('batch_size', 5)
        self.batch_delay = cfg.get('batch_delay', 1.0)
        
        if not self.api_key:
            raise ValueError('DeepSeek API Key 未配置，请设置 DEEPSEEK_API_KEY 环境变量或在 config.json 中配置')
        
        # 分析策略配置
        self.strategies = {
            'technical_trend': {
                'prompt_template': """分析以下AI技术信息，提取关键技术点、影响程度和时间线。

内容：
{content}

请按照以下格式输出JSON：
{{
    "technologies": ["技术1", "技术2", ...],
    "impact_level": "高/中/低",
    "timeline": "短期/中期/长期",
    "key_points": ["关键点1", "关键点2", ...],
    "summary": "简要总结"
}}""",
                'output_schema': {
                    'technologies': [],
                    'impact_level': '',
                    'timeline': '',
                    'key_points': [],
                    'summary': ''
                }
            },
            'market_sentiment': {
                'prompt_template': """分析以下财经信息，评估市场情绪、关键事件和风险因素。

内容：
{content}

请按照以下格式输出JSON：
{{
    "sentiment_score": 0.0,
    "sentiment_label": "看涨/看跌/中性",
    "key_events": ["事件1", "事件2", ...],
    "risk_factors": ["风险1", "风险2", ...],
    "opportunities": ["机会1", "机会2", ...],
    "summary": "市场情绪分析总结"
}}""",
                'output_schema': {
                    'sentiment_score': 0.0,
                    'sentiment_label': '',
                    'key_events': [],
                    'risk_factors': [],
                    'opportunities': [],
                    'summary': ''
                }
            },
            'correlation_analysis': {
                'prompt_template': """分析AI新闻与相关股票价格的关联性，评估滞后效应和给出建议。

AI新闻内容：
{ai_content}

股票信息：
{stock_info}

请按照以下格式输出JSON：
{{
    "correlation": [
        {{"factor": "因素1", "impact": "正面/负面/中性", "strength": 0.0}}
    ],
    "lag_effect": "即时/短期/中期/长期",
    "recommendations": ["建议1", "建议2", ...],
    "confidence": 0.0,
    "summary": "关联性分析总结"
}}""",
                'output_schema': {
                    'correlation': [],
                    'lag_effect': '',
                    'recommendations': [],
                    'confidence': 0.0,
                    'summary': ''
                }
            }
        }
        
        # 缓存配置
        self.cache_enabled = True
        self.cache_ttl = timedelta(hours=24)  # 缓存24小时
        self.cache = {}  # 内存缓存
        
        # 批处理配置
        self.batch_size = 5  # 每批处理5条
        self.batch_delay = 1.0  # 批次间延迟（秒）
        
        # 请求配置
        self.timeout = 30
        self.max_retries = 3
        self.retry_delay = 1.0
    
    def _get_env(self, key: str, default: str = '') -> str:
        """获取环境变量"""
        import os
        return os.getenv(key, default)
    
    def _generate_cache_key(self, strategy: str, content: str) -> str:
        """生成缓存键"""
        key_str = f"{strategy}:{content}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """从缓存获取"""
        if not self.cache_enabled:
            return None
        
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if datetime.now() - cached_time < self.cache_ttl:
                return cached_data
            else:
                # 缓存过期，删除
                del self.cache[cache_key]
        
        return None
    
    def _set_cache(self, cache_key: str, data: Dict):
        """设置缓存"""
        if self.cache_enabled:
            self.cache[cache_key] = (data, datetime.now())
    
    def _call_api(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        调用 DeepSeek API
        
        Args:
            prompt: 用户提示
            system_prompt: 系统提示（可选）
            
        Returns:
            API 响应
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': prompt})
        
        data = {
            'model': self.model,
            'messages': messages,
            'temperature': 0.7,
            'max_tokens': 2000
        }
        
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=data,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                result = response.json()
                
                # 提取回复内容
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0]['message']['content']
                    
                    # 尝试解析JSON
                    try:
                        # 提取JSON部分（如果包含markdown代码块）
                        if '```json' in content:
                            json_start = content.find('```json') + 7
                            json_end = content.find('```', json_start)
                            content = content[json_start:json_end].strip()
                        elif '```' in content:
                            json_start = content.find('```') + 3
                            json_end = content.find('```', json_start)
                            content = content[json_start:json_end].strip()
                        
                        parsed = json.loads(content)
                        return {'success': True, 'data': parsed, 'raw': result}
                    except json.JSONDecodeError:
                        # 如果不是JSON，返回原始文本
                        return {'success': True, 'data': {'text': content}, 'raw': result}
                else:
                    return {'success': False, 'error': 'No choices in response', 'raw': result}
                    
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    return {'success': False, 'error': str(e)}
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        return {'success': False, 'error': 'Max retries exceeded'}
    
    def analyze(self, strategy: str, content: str, **kwargs) -> Dict[str, Any]:
        """
        执行分析
        
        Args:
            strategy: 分析策略名称
            content: 要分析的内容
            **kwargs: 额外参数（用于策略模板）
            
        Returns:
            分析结果
        """
        if strategy not in self.strategies:
            raise ValueError(f'未知的分析策略: {strategy}')
        
        # 检查缓存
        cache_key = self._generate_cache_key(strategy, content)
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return {'success': True, 'data': cached_result, 'cached': True}
        
        # 构建提示
        strategy_config = self.strategies[strategy]
        prompt = strategy_config['prompt_template'].format(content=content, **kwargs)
        
        # 调用API
        result = self._call_api(prompt)
        
        if result.get('success'):
            data = result.get('data', {})
            # 验证输出格式
            schema = strategy_config['output_schema']
            validated_data = self._validate_schema(data, schema)
            
            # 缓存结果
            self._set_cache(cache_key, validated_data)
            
            return {
                'success': True,
                'data': validated_data,
                'strategy': strategy,
                'cached': False
            }
        else:
            return {
                'success': False,
                'error': result.get('error', 'Unknown error'),
                'strategy': strategy
            }
    
    def _validate_schema(self, data: Dict, schema: Dict) -> Dict:
        """
        验证和填充输出模式
        
        Args:
            data: API返回的数据
            schema: 期望的模式
            
        Returns:
            验证后的数据
        """
        validated = {}
        
        for key, default_value in schema.items():
            if key in data:
                validated[key] = data[key]
            else:
                # 使用默认值
                if isinstance(default_value, list):
                    validated[key] = []
                elif isinstance(default_value, dict):
                    validated[key] = {}
                elif isinstance(default_value, (int, float)):
                    validated[key] = 0.0 if isinstance(default_value, float) else 0
                else:
                    validated[key] = ''
        
        return validated
    
    def analyze_batch(self, strategy: str, items: List[Dict[str, Any]], merge_similar: bool = True) -> List[Dict[str, Any]]:
        """
        批量分析
        
        Args:
            strategy: 分析策略
            items: 数据项列表
            merge_similar: 是否合并相似内容
            
        Returns:
            分析结果列表
        """
        if merge_similar:
            # 合并相似内容
            grouped_items = self._group_similar_items(items)
            results = []
            
            for group_key, group_items in grouped_items.items():
                # 合并内容
                merged_content = self._merge_content(group_items)
                
                # 分析合并后的内容
                result = self.analyze(strategy, merged_content)
                
                # 为每个原始项分配结果
                for item in group_items:
                    item_result = result.copy()
                    item_result['item_id'] = item.get('item_id') or item.get('url', '')
                    results.append(item_result)
            
            return results
        else:
            # 逐个分析
            results = []
            for i, item in enumerate(items):
                content = item.get('content') or item.get('description') or item.get('title', '')
                if content:
                    result = self.analyze(strategy, content)
                    result['item_id'] = item.get('item_id') or item.get('url', '')
                    results.append(result)
                
                # 批次延迟
                if (i + 1) % self.batch_size == 0:
                    time.sleep(self.batch_delay)
            
            return results
    
    def _group_similar_items(self, items: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
        """
        将相似的内容分组
        
        Args:
            items: 数据项列表
            
        Returns:
            分组后的字典
        """
        groups = defaultdict(list)
        
        for item in items:
            # 使用标题和内容的前100字符作为分组键
            title = item.get('title', '')[:50]
            content_preview = (item.get('content') or item.get('description') or '')[:100]
            group_key = hashlib.md5(f"{title}:{content_preview}".encode()).hexdigest()
            
            groups[group_key].append(item)
        
        return groups
    
    def _merge_content(self, items: List[Dict[str, Any]]) -> str:
        """
        合并多个数据项的内容
        
        Args:
            items: 数据项列表
            
        Returns:
            合并后的内容
        """
        merged_parts = []
        
        for i, item in enumerate(items, 1):
            title = item.get('title', '')
            content = item.get('content') or item.get('description', '')
            
            if title:
                merged_parts.append(f"【{i}】{title}")
            if content:
                merged_parts.append(content[:500])  # 限制每个内容长度
        
        return '\n\n'.join(merged_parts)
    
    async def analyze_async(self, strategy: str, content: str, **kwargs) -> Dict[str, Any]:
        """
        异步分析（用于提高吞吐量）
        
        Args:
            strategy: 分析策略
            content: 内容
            **kwargs: 额外参数
            
        Returns:
            分析结果
        """
        # 在线程池中执行同步调用
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.analyze, strategy, content, **kwargs)
    
    async def analyze_batch_async(self, strategy: str, items: List[Dict[str, Any]], merge_similar: bool = True) -> List[Dict[str, Any]]:
        """
        异步批量分析
        
        Args:
            strategy: 分析策略
            items: 数据项列表
            merge_similar: 是否合并相似内容
            
        Returns:
            分析结果列表
        """
        if merge_similar:
            grouped_items = self._group_similar_items(items)
            tasks = []
            
            for group_key, group_items in grouped_items.items():
                merged_content = self._merge_content(group_items)
                task = self.analyze_async(strategy, merged_content)
                tasks.append((task, group_items))
            
            # 并发执行
            results = []
            for task, group_items in tasks:
                result = await task
                
                # 为每个原始项分配结果
                for item in group_items:
                    item_result = result.copy()
                    item_result['item_id'] = item.get('item_id') or item.get('url', '')
                    results.append(item_result)
            
            return results
        else:
            # 分批并发处理
            results = []
            for i in range(0, len(items), self.batch_size):
                batch = items[i:i + self.batch_size]
                tasks = []
                
                for item in batch:
                    content = item.get('content') or item.get('description') or item.get('title', '')
                    if content:
                        task = self.analyze_async(strategy, content)
                        tasks.append((task, item))
                
                # 等待当前批次完成
                batch_results = await asyncio.gather(*[t[0] for t in tasks])
                
                for (task_result, item) in zip(batch_results, [t[1] for t in tasks]):
                    task_result['item_id'] = item.get('item_id') or item.get('url', '')
                    results.append(task_result)
            
            return results
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total = len(self.cache)
        valid = 0
        expired = 0
        
        now = datetime.now()
        for cache_key, (data, cached_time) in self.cache.items():
            if now - cached_time < self.cache_ttl:
                valid += 1
            else:
                expired += 1
        
        return {
            'total': total,
            'valid': valid,
            'expired': expired,
            'cache_enabled': self.cache_enabled
        }

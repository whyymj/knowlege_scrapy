"""
文章细节分析器
基于LangChain实现文章深度分析
"""
from typing import Dict, Any, Optional, List
from .recommender import AIRecommender
import asyncio


class ArticleAnalyzer:
    """文章分析器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化文章分析器
        
        Args:
            config: 配置字典
        """
        self.recommender = AIRecommender(config)
        self.config = config or {}
        self.cache = {}  # 简单的内存缓存
    
    def analyze(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析文章细节
        
        Args:
            article: 文章数据
            
        Returns:
            分析结果
        """
        # 检查缓存
        article_id = article.get('id') or article.get('url', '')
        cache_key = f"article_{hash(article_id)}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # 调用AI分析
        details = self.recommender.analyze_article_details(article)
        
        # 构建结果（details 现在是字典）
        result = {
            'article_id': article_id,
            'summary': details.get('summary', ''),
            'key_points': details.get('key_points', []),
            'sentiment': details.get('sentiment', 'neutral'),
            'entities': details.get('entities', []),
            'tags': details.get('tags', []),
            'analysis': {
                'word_count': len(article.get('content', '').split()),
                'read_time': self._estimate_read_time(article.get('content', '')),
                'complexity': self._estimate_complexity(article.get('content', ''))
            }
        }
        
        # 缓存结果
        self.cache[cache_key] = result
        
        return result
    
    def batch_analyze(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量分析文章
        
        Args:
            articles: 文章列表
            
        Returns:
            分析结果列表
        """
        results = []
        for article in articles:
            try:
                result = self.analyze(article)
                results.append(result)
            except Exception as e:
                # 如果分析失败，返回基本信息
                results.append({
                    'article_id': article.get('id') or article.get('url', ''),
                    'error': str(e)
                })
        return results
    
    async def analyze_async(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        异步分析文章
        
        Args:
            article: 文章数据
            
        Returns:
            分析结果
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.analyze, article)
    
    def _estimate_read_time(self, content: str) -> int:
        """
        估算阅读时间（分钟）
        
        Args:
            content: 文章内容
            
        Returns:
            阅读时间（分钟）
        """
        word_count = len(content.split())
        # 假设每分钟阅读200字
        return max(1, word_count // 200)
    
    def _estimate_complexity(self, content: str) -> str:
        """
        估算文章复杂度
        
        Args:
            content: 文章内容
            
        Returns:
            复杂度等级：simple/medium/complex
        """
        words = content.split()
        if len(words) < 300:
            return 'simple'
        elif len(words) < 1000:
            return 'medium'
        else:
            return 'complex'

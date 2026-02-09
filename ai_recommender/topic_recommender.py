"""
主题推荐器
基于LangChain实现智能主题推荐
"""
from typing import List, Dict, Any, Optional
from .recommender import AIRecommender
import asyncio


class TopicRecommender:
    """主题推荐器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化主题推荐器
        
        Args:
            config: 配置字典
        """
        self.recommender = AIRecommender(config)
        self.config = config or {}
    
    def recommend(self, articles: List[Dict[str, Any]], 
                 num_topics: int = 5,
                 min_articles_per_topic: int = 2) -> Dict[str, Any]:
        """
        推荐主题
        
        Args:
            articles: 文章列表
            num_topics: 推荐主题数量
            min_articles_per_topic: 每个主题最少文章数
            
        Returns:
            推荐结果
        """
        if not articles:
            return {
                'topics': [],
                'recommendations': []
            }
        
        # 调用AI推荐
        recommendation = self.recommender.recommend_topics(articles, num_topics)
        
        # recommendation 现在是字典
        topics = recommendation.get('topics', [])
        reasons = recommendation.get('reasons', [])
        categories = recommendation.get('categories', [])
        
        # 为每个主题匹配文章
        topic_articles = {}
        for topic in topics:
            topic_articles[topic] = self._match_articles_to_topic(articles, topic)
        
        # 过滤掉文章数不足的主题
        filtered_topics = {
            topic: articles_list 
            for topic, articles_list in topic_articles.items()
            if len(articles_list) >= min_articles_per_topic
        }
        
        return {
            'topics': list(filtered_topics.keys()),
            'recommendations': [
                {
                    'topic': topic,
                    'reason': reasons[i] if i < len(reasons) else '',
                    'category': categories[i] if i < len(categories) else '',
                    'article_count': len(articles_list),
                    'articles': articles_list[:5]  # 返回前5篇
                }
                for i, (topic, articles_list) in enumerate(filtered_topics.items())
            ]
        }
    
    def _match_articles_to_topic(self, articles: List[Dict[str, Any]], 
                                 topic: str) -> List[Dict[str, Any]]:
        """
        将文章匹配到主题
        
        Args:
            articles: 文章列表
            topic: 主题
            
        Returns:
            匹配的文章列表
        """
        matched = []
        
        # 简单的关键词匹配
        topic_keywords = topic.lower().split()
        
        for article in articles:
            title = article.get('title', '').lower()
            content = article.get('content', '').lower()
            
            # 计算匹配度
            title_matches = sum(1 for keyword in topic_keywords if keyword in title)
            content_matches = sum(1 for keyword in topic_keywords if keyword in content)
            
            score = title_matches * 2 + content_matches  # 标题权重更高
            
            if score > 0:
                article_copy = article.copy()
                article_copy['relevance_score'] = score
                matched.append(article_copy)
        
        # 按相关性排序
        matched.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        return matched
    
    async def recommend_async(self, articles: List[Dict[str, Any]], 
                             num_topics: int = 5) -> Dict[str, Any]:
        """
        异步推荐主题
        
        Args:
            articles: 文章列表
            num_topics: 推荐主题数量
            
        Returns:
            推荐结果
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.recommend, articles, num_topics)

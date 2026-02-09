"""
AI推荐模块
基于LangChain实现主题推荐、文章细节分析和手动选择功能
"""
from .recommender import AIRecommender
from .topic_recommender import TopicRecommender
from .article_analyzer import ArticleAnalyzer
from .selector import ManualSelector

__all__ = [
    'AIRecommender',
    'TopicRecommender',
    'ArticleAnalyzer',
    'ManualSelector'
]

"""
AI推荐服务
整合主题推荐、文章分析和手动选择功能
"""
import logging
from typing import List, Dict, Any, Optional
from .topic_recommender import TopicRecommender
from .article_analyzer import ArticleAnalyzer
from .selector import ManualSelector

logger = logging.getLogger(__name__)


class AIRecommendationService:
    """AI推荐服务"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化推荐服务
        
        Args:
            config: 配置字典
        """
        self.topic_recommender = TopicRecommender(config)
        self.article_analyzer = ArticleAnalyzer(config)
        self.manual_selector = ManualSelector(config)
        self.config = config or {}
    
    def get_topic_recommendations(self, articles: List[Dict[str, Any]],
                                  num_topics: int = 5) -> Dict[str, Any]:
        """
        获取主题推荐
        
        Args:
            articles: 文章列表
            num_topics: 推荐主题数量
            
        Returns:
            推荐结果
        """
        return self.topic_recommender.recommend(articles, num_topics)
    
    def analyze_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析文章细节
        
        Args:
            article: 文章数据
            
        Returns:
            分析结果
        """
        return self.article_analyzer.analyze(article)
    
    def batch_analyze_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量分析文章
        
        Args:
            articles: 文章列表
            
        Returns:
            分析结果列表
        """
        return self.article_analyzer.batch_analyze(articles)
    
    def manual_select_topics(self, user_id: str, topics: List[str],
                            articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        手动选择主题
        
        Args:
            user_id: 用户ID
            topics: 选择的主题列表
            articles: 相关文章列表
            
        Returns:
            选择结果
        """
        return self.manual_selector.select_topics(user_id, topics, articles)
    
    def manual_select_articles(self, user_id: str, article_ids: List[str],
                              reason: Optional[str] = None) -> Dict[str, Any]:
        """
        手动选择文章
        
        Args:
            user_id: 用户ID
            article_ids: 选择的文章ID列表
            reason: 选择理由
            
        Returns:
            选择结果
        """
        return self.manual_selector.select_articles(user_id, article_ids, reason)
    
    def get_user_selections(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户的选择记录
        
        Args:
            user_id: 用户ID
            
        Returns:
            选择记录和统计
        """
        selections = self.manual_selector.get_selections(user_id)
        stats = self.manual_selector.get_selection_stats(user_id)
        
        return {
            'selections': selections,
            'stats': stats
        }
    
    def get_recommendation_pipeline(self, articles: List[Dict[str, Any]],
                                   user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取完整的推荐流程结果
        
        Args:
            articles: 文章列表
            user_id: 用户ID（可选）
            
        Returns:
            完整的推荐结果
        """
        # 1. 主题推荐
        topic_recommendations = self.get_topic_recommendations(articles)
        
        # 2. 文章分析（选择前5篇）
        analyzed_articles = []
        for article in articles[:5]:
            try:
                analysis = self.analyze_article(article)
                analyzed_articles.append(analysis)
            except Exception as e:
                analyzed_articles.append({
                    'article_id': article.get('id'),
                    'error': str(e)
                })
        
        # 3. 用户历史选择（如果有）
        user_selections = None
        if user_id:
            user_selections = self.get_user_selections(user_id)
        
        return {
            'topic_recommendations': topic_recommendations,
            'article_analyses': analyzed_articles,
            'user_selections': user_selections,
            'total_articles': len(articles)
        }
    
    def recommend_sites_for_topic(self, topic: str, num_sites: int = 10) -> Dict[str, Any]:
        """
        基于主题推荐相关网站
        
        Args:
            topic: 抓取主题（例如：最新的AI进展）
            num_sites: 推荐网站数量
            
        Returns:
            推荐网站列表
        """
        from .recommender import AIRecommender
        
        # 强制使用直接API调用，避免LangChain的Pydantic兼容性问题
        recommender = AIRecommender(self.config)
        # 强制设置为直接API模式
        recommender.use_direct_api = True
        recommender.api_key = self.config.get('api_key') or recommender.config.get('api_key')
        recommender.api_url = self.config.get('api_url') or recommender.config.get('api_url', 'https://api.deepseek.com/v1/chat/completions')
        recommender.model_name = self.config.get('model', 'deepseek-chat')
        recommender.temperature = self.config.get('temperature', 0.7)
        recommender.provider = self.config.get('provider', 'deepseek')
        
        # 构建提示词
        system_prompt = """你是一个专业的网站推荐专家。根据用户提供的主题描述，推荐最相关的网站URL。

推荐原则：
1. 优先推荐包含该主题最新内容、高质量文章的网站
2. 优先推荐知名科技媒体网站（如TechCrunch、ArXiv、GitHub、Medium等）
3. 优先推荐专业博客和论坛（如Stack Overflow、Reddit相关版块）
4. 优先推荐新闻网站的相关版块（如BBC Technology、Reuters Technology）
5. 优先推荐学术论文网站（如ArXiv、Google Scholar）
6. 优先推荐官方博客和文档网站
7. 确保推荐的网站可以直接访问，且包含相关内容

请以JSON格式输出，包含sites字段，每个网站包含：
- url: 网站URL（必须是完整的、可访问的URL）
- name: 网站名称
- reason: 推荐理由（说明为什么这个网站适合该主题）

注意：
- URL必须是真实可访问的
- 优先推荐英文网站，但也可以推荐中文网站
- 确保网站内容与主题高度相关"""
        
        user_prompt = f"""请为以下主题推荐{num_sites}个最相关的网站：

主题描述：{topic}

请仔细分析主题描述，理解用户想要抓取的内容类型和领域，然后推荐能够获取该主题最新、高质量内容的网站。

如果主题描述比较模糊，请根据关键词推断可能的领域和内容类型，然后推荐相关网站。"""
        
        # 调用LLM（始终使用直接API调用）
        try:
            # 直接API调用
            response_text = recommender._call_api_direct(
                system_prompt,
                user_prompt
            )
            
            # 尝试解析JSON
            try:
                import json
                import re
                # 尝试提取JSON部分
                if '```json' in response_text:
                    json_start = response_text.find('```json') + 7
                    json_end = response_text.find('```', json_start)
                    response_text = response_text[json_start:json_end].strip()
                elif '```' in response_text:
                    json_start = response_text.find('```') + 3
                    json_end = response_text.find('```', json_start)
                    response_text = response_text[json_start:json_end].strip()
                
                # 尝试提取JSON对象
                json_match = re.search(r'\{[^{}]*"sites"[^{}]*\}', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group()
                
                result = json.loads(response_text)
            except Exception as parse_error:
                logger.warning(f"JSON解析失败: {parse_error}, 响应内容: {response_text[:200]}")
                # 如果解析失败，使用默认网站列表
                result = self._get_default_sites_for_topic(topic, num_sites)
        except Exception as e:
            # 如果AI调用失败，返回默认网站列表
            logger.warning(f"AI推荐网站失败，使用默认列表: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            result = self._get_default_sites_for_topic(topic, num_sites)
        
        sites = result.get('sites', [])
        
        return {
            'sites': sites,
            'topic': topic,
            'count': len(sites)
        }
    
    def _get_default_sites_for_topic(self, topic: str, num_sites: int) -> Dict[str, Any]:
        """获取默认网站列表（当AI调用失败时使用）"""
        # 根据主题关键词匹配默认网站
        topic_lower = topic.lower()
        
        default_sites = []
        
        # AI/机器学习相关
        if any(keyword in topic_lower for keyword in ['ai', '人工智能', '机器学习', '深度学习', 'chatgpt', 'gpt']):
            default_sites.extend([
                {'url': 'https://arxiv.org/list/cs.AI/recent', 'name': 'ArXiv AI', 'reason': 'AI领域最新论文'},
                {'url': 'https://www.technologyreview.com/topic/artificial-intelligence/', 'name': 'MIT Technology Review', 'reason': 'AI技术深度报道'},
                {'url': 'https://openai.com/blog', 'name': 'OpenAI Blog', 'reason': 'OpenAI官方博客'},
                {'url': 'https://www.deepmind.com/blog', 'name': 'DeepMind Blog', 'reason': 'DeepMind研究进展'},
                {'url': 'https://venturebeat.com/ai/', 'name': 'VentureBeat AI', 'reason': 'AI商业新闻'},
            ])
        
        # 技术/编程相关
        if any(keyword in topic_lower for keyword in ['技术', '编程', '开发', 'code', 'tech']):
            default_sites.extend([
                {'url': 'https://github.com/trending', 'name': 'GitHub Trending', 'reason': '热门开源项目'},
                {'url': 'https://techcrunch.com', 'name': 'TechCrunch', 'reason': '科技新闻'},
                {'url': 'https://www.theverge.com', 'name': 'The Verge', 'reason': '科技资讯'},
                {'url': 'https://news.ycombinator.com', 'name': 'Hacker News', 'reason': '技术社区'},
            ])
        
        # 通用新闻网站
        default_sites.extend([
            {'url': 'https://www.bbc.com/news/technology', 'name': 'BBC Technology', 'reason': 'BBC科技新闻'},
            {'url': 'https://www.reuters.com/technology', 'name': 'Reuters Technology', 'reason': '路透社科技新闻'},
        ])
        
        return {
            'sites': default_sites[:num_sites]
        }

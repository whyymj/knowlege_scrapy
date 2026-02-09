"""
AI推荐器主类
基于LangChain实现
"""
import os
import logging
from typing import List, Dict, Any, Optional, TypedDict

# 完全避免导入 LangChain 和 Pydantic，因为它们会在 Python 3.12 中触发 ForwardRef 错误
# 默认使用直接 API 调用模式
ChatOpenAI = None
ChatPromptTemplate = None
PydanticOutputParser = None

# 只有在明确要求时才尝试导入 LangChain（但即使导入成功，也默认不使用）
# 这样可以避免在导入阶段就触发 Pydantic 错误
if False:  # 默认不导入，避免触发错误
    try:
        from langchain_openai import ChatOpenAI
        from langchain.prompts import ChatPromptTemplate
    except ImportError:
        try:
            from langchain.chat_models import ChatOpenAI
            from langchain.prompts import ChatPromptTemplate
        except ImportError:
            pass

import json
import requests
from typing import TypedDict

logger = logging.getLogger(__name__)

# 完全避免使用 Pydantic BaseModel，使用 TypedDict 代替
# 这样可以避免 Python 3.12 中的 ForwardRef 兼容性问题
class TopicRecommendation(TypedDict, total=False):
    """主题推荐结果"""
    topics: List[str]
    reasons: List[str]
    categories: List[str]


class ArticleDetails(TypedDict, total=False):
    """文章细节"""
    summary: str
    key_points: List[str]
    sentiment: str
    entities: List[str]
    tags: List[str]


class AIRecommender:
    """AI推荐器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化AI推荐器
        
        Args:
            config: 配置字典
        """
        if config is None:
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from utils.config_loader import config as global_config
            ai_config = global_config.get('ai_recommender', {})
        else:
            ai_config = config
        
        self.config = ai_config
        
        # 初始化LLM
        self._init_llm()
        
        # 初始化输出解析器（如果可用）
        # 注意：在 Python 3.12 中，PydanticOutputParser 可能触发 ForwardRef 兼容性问题
        # 因此默认禁用，使用直接 JSON 解析
        self.topic_parser = None
        self.article_parser = None
        
        # 只有在明确要求且 LangChain 可用时才尝试初始化解析器
        if self.config.get('use_pydantic_parser', False) and PydanticOutputParser:
            try:
                self.topic_parser = PydanticOutputParser(pydantic_object=TopicRecommendation)
                self.article_parser = PydanticOutputParser(pydantic_object=ArticleDetails)
                logger.info("PydanticOutputParser 初始化成功")
            except Exception as e:
                logger.warning(f"PydanticOutputParser 初始化失败，将使用直接 JSON 解析: {e}")
                self.topic_parser = None
                self.article_parser = None
    
    def _init_llm(self):
        """初始化语言模型"""
        provider = self.config.get('provider', 'deepseek')
        api_key = self.config.get('api_key') or os.getenv('DEEPSEEK_API_KEY') or os.getenv('OPENAI_API_KEY')
        model_name = self.config.get('model', 'deepseek-chat')
        temperature = self.config.get('temperature', 0.7)
        
        # 优先使用直接API调用，避免LangChain的Pydantic兼容性问题
        # 特别是对于Python 3.12，LangChain可能存在ForwardRef问题
        self.use_direct_api = True
        self.api_key = api_key
        self.api_url = self.config.get('api_url', 'https://api.deepseek.com/v1/chat/completions')
        self.model_name = model_name
        self.temperature = temperature
        self.provider = provider
        
        # 如果明确要求使用LangChain且LangChain可用，才使用LangChain
        if self.config.get('use_langchain', False) and ChatOpenAI is not None:
            try:
                self.use_direct_api = False
                # 尝试初始化LangChain（可能会失败）
                if provider == 'openai':
                    if not api_key:
                        raise ValueError("OpenAI API Key未配置")
                    self.llm = ChatOpenAI(
                        model=model_name,
                        temperature=temperature,
                        api_key=api_key
                    )
                elif provider == 'deepseek':
                    api_url = self.config.get('api_url', 'https://api.deepseek.com/v1/chat/completions')
                    self.llm = ChatOpenAI(
                        model=model_name,
                        temperature=temperature,
                        api_key=api_key,
                        base_url=api_url
                    )
                else:
                    raise ValueError(f"不支持的LLM提供商: {provider}")
            except Exception as e:
                # 如果LangChain初始化失败，回退到直接API调用
                logger.warning(f"LangChain初始化失败，使用直接API调用: {e}")
                self.use_direct_api = True
                self.api_key = api_key
                self.api_url = self.config.get('api_url', 'https://api.deepseek.com/v1/chat/completions')
                self.model_name = model_name
                self.temperature = temperature
                self.provider = provider
        
        # 如果使用直接API，不需要初始化LangChain
        if self.use_direct_api:
            return
    
    def recommend_topics(self, articles: List[Dict[str, Any]], 
                        num_topics: int = 5) -> Dict[str, Any]:
        """
        推荐主题
        
        Args:
            articles: 文章列表
            num_topics: 推荐主题数量
            
        Returns:
            主题推荐结果
        """
        # 构建文章摘要
        articles_summary = []
        for article in articles[:10]:  # 限制前10篇
            title = article.get('title', '')
            content = article.get('content', '')[:500]  # 限制长度
            articles_summary.append(f"标题: {title}\n内容: {content[:200]}...")
        
        articles_text = "\n\n".join(articles_summary)
        
        # 构建提示词
        system_prompt = """你是一个专业的内容分析师。根据提供的文章列表，分析并推荐最相关的主题。
请以JSON格式输出，包含topics（主题列表）、reasons（推荐理由列表）、categories（分类列表）字段。"""
        
        user_prompt = f"""请分析以下文章，推荐{num_topics}个最相关的主题：

文章列表：
{articles_text}

请推荐主题，并说明推荐理由和分类。"""
        
        # 调用LLM
        if self.use_direct_api:
            response_text = self._call_api_direct(system_prompt, user_prompt)
        else:
            if ChatPromptTemplate:
                prompt_template = ChatPromptTemplate.from_messages([
                    ("system", system_prompt),
                    ("human", user_prompt)
                ])
                prompt = prompt_template.format_messages()
                response = self.llm.invoke(prompt)
                response_text = response.content if hasattr(response, 'content') else str(response)
            else:
                response_text = self._call_api_direct(system_prompt, user_prompt)
        
        # 解析输出
        try:
            if self.topic_parser and not self.use_direct_api:
                result = self.topic_parser.parse(response_text)
                return result
            else:
                return self._parse_topic_recommendation(response_text)
        except Exception as e:
            # 如果解析失败，尝试手动解析
            return self._parse_topic_recommendation(response_text)
    
    def analyze_article_details(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析文章细节
        
        Args:
            article: 文章数据
            
        Returns:
            文章细节分析结果
        """
        title = article.get('title', '')
        content = article.get('content', '')[:2000]  # 限制内容长度
        
        # 构建提示词
        system_prompt = """你是一个专业的内容分析师。请详细分析文章内容，提取关键信息。
请以JSON格式输出，包含summary（摘要）、key_points（关键要点列表）、sentiment（情感倾向）、entities（关键实体列表）、tags（标签列表）字段。"""
        
        user_prompt = f"""请分析以下文章：

标题：{title}

内容：
{content}

请提供详细的文章分析，包括摘要、关键要点、情感倾向、关键实体和标签。"""
        
        # 调用LLM
        if self.use_direct_api:
            response_text = self._call_api_direct(system_prompt, user_prompt)
        else:
            if ChatPromptTemplate:
                prompt_template = ChatPromptTemplate.from_messages([
                    ("system", system_prompt),
                    ("human", user_prompt)
                ])
                prompt = prompt_template.format_messages()
                response = self.llm.invoke(prompt)
                response_text = response.content if hasattr(response, 'content') else str(response)
            else:
                response_text = self._call_api_direct(system_prompt, user_prompt)
        
        # 解析输出
        try:
            if self.article_parser and not self.use_direct_api:
                result = self.article_parser.parse(response_text)
                return result
            else:
                return self._parse_article_details(response_text)
        except Exception as e:
            # 如果解析失败，尝试手动解析
            return self._parse_article_details(response_text)
    
    def _call_api_direct(self, system_prompt: str, user_prompt: str) -> str:
        """
        直接调用API（当LangChain不可用时）
        
        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            
        Returns:
            API响应文本
        """
        if not self.api_key:
            raise ValueError("API Key未配置")
        
        # 确定API URL
        if self.provider == 'deepseek':
            api_url = self.api_url or 'https://api.deepseek.com/v1/chat/completions'
        else:
            api_url = 'https://api.openai.com/v1/chat/completions'
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        data = {
            'model': self.model_name,
            'temperature': self.temperature,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ]
        }
        
        try:
            response = requests.post(api_url, json=data, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content']
        except Exception as e:
            raise Exception(f"API调用失败: {e}")
    
    def _parse_topic_recommendation(self, text: str) -> Dict[str, Any]:
        """手动解析主题推荐结果"""
        # 尝试从JSON中提取
        try:
            import re
            # 尝试提取JSON部分
            json_match = re.search(r'\{[^{}]*"topics"[^{}]*\}', text, re.DOTALL)
            if json_match:
                json_text = json_match.group()
            elif '```json' in text:
                json_text = text.split('```json')[1].split('```')[0].strip()
            elif '```' in text:
                json_text = text.split('```')[1].split('```')[0].strip()
            else:
                json_text = text
            
            data = json.loads(json_text)
            # 确保返回的字典包含所有必需字段
            return {
                'topics': data.get('topics', []),
                'reasons': data.get('reasons', []),
                'categories': data.get('categories', [])
            }
        except Exception as e:
            logger.warning(f"解析主题推荐失败: {e}")
            # 如果JSON解析失败，返回默认值
            return {
                'topics': [],
                'reasons': [],
                'categories': []
            }
    
    def _parse_article_details(self, text: str) -> Dict[str, Any]:
        """手动解析文章细节"""
        try:
            import re
            # 尝试提取JSON部分
            json_match = re.search(r'\{[^{}]*"summary"[^{}]*\}', text, re.DOTALL)
            if json_match:
                json_text = json_match.group()
            elif '```json' in text:
                json_text = text.split('```json')[1].split('```')[0].strip()
            elif '```' in text:
                json_text = text.split('```')[1].split('```')[0].strip()
            else:
                json_text = text
            
            data = json.loads(json_text)
            # 确保返回的字典包含所有必需字段
            return {
                'summary': data.get('summary', ''),
                'key_points': data.get('key_points', []),
                'sentiment': data.get('sentiment', 'neutral'),
                'entities': data.get('entities', []),
                'tags': data.get('tags', [])
            }
        except Exception as e:
            logger.warning(f"解析文章细节失败: {e}")
            # 如果解析失败，返回默认值
            return {
                'summary': '',
                'key_points': [],
                'sentiment': 'neutral',
                'entities': [],
                'tags': []
            }

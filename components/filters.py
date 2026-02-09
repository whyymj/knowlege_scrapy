"""
数据筛选器实现
"""
import logging
from typing import Dict, List, Any, Optional
from .base import BaseFilter

logger = logging.getLogger(__name__)


class AIFilter(BaseFilter):
    """AI筛选器 - 根据AI描述筛选文章"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化AI筛选器
        
        Args:
            config: 配置字典，包含：
                - filter_description: 筛选描述（用户提供的描述）
                - ai_service: AI服务实例（可选）
        """
        super().__init__(config)
        self.filter_description = config.get('filter_description', '')
        self.ai_service = config.get('ai_service')
        self.enabled = bool(self.filter_description and self.filter_description.strip())
    
    async def filter(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        筛选数据项
        
        Args:
            items: 数据项列表
            
        Returns:
            筛选后的数据项列表
        """
        if not self.enabled:
            logger.info("AI筛选未启用，跳过筛选")
            return items
        
        if not items:
            return items
        
        logger.info(f"开始AI筛选，原始数据量: {len(items)}")
        
        filtered_items = []
        skipped_count = 0
        
        for item in items:
            try:
                # 提取标题和简介
                title = item.get('title', '')
                description = item.get('description', '')
                content_preview = item.get('content', '')[:500] if item.get('content') else ''  # 只取前500字符
                
                # 如果没有标题，跳过
                if not title:
                    skipped_count += 1
                    logger.debug(f"跳过无标题项: {item.get('url', 'unknown')}")
                    continue
                
                # 调用AI判断是否符合描述
                is_match = await self._check_match(title, description, content_preview)
                
                if is_match:
                    filtered_items.append(item)
                    logger.debug(f"通过筛选: {title[:50]}...")
                else:
                    skipped_count += 1
                    logger.debug(f"未通过筛选: {title[:50]}...")
                    
            except Exception as e:
                logger.error(f"筛选失败: {e}")
                # 如果筛选失败，默认保留该项（容错处理）
                filtered_items.append(item)
        
        logger.info(f"AI筛选完成，通过: {len(filtered_items)}, 跳过: {skipped_count}")
        return filtered_items
    
    async def _check_match(self, title: str, description: str, content_preview: str) -> bool:
        """
        检查文章是否符合筛选描述
        
        Args:
            title: 文章标题
            description: 文章简介
            content_preview: 内容预览
            
        Returns:
            是否符合描述
        """
        if not self.ai_service:
            # 如果没有AI服务，使用简单的关键词匹配作为降级方案
            return self._simple_keyword_match(title, description, content_preview)
        
        try:
            # 构建提示词
            system_prompt = """你是一个专业的内容筛选专家。根据用户提供的筛选描述，判断文章是否符合要求。

请仔细分析文章的标题、简介和内容预览，判断是否与筛选描述相关。

请以JSON格式输出，包含：
- match: true/false（是否符合）
- reason: 判断理由（简要说明）"""
            
            article_info = f"""标题：{title}

简介：{description if description else '无'}

内容预览：{content_preview if content_preview else '无'}"""
            
            user_prompt = f"""请判断以下文章是否符合以下筛选描述：

筛选描述：{self.filter_description}

文章信息：
{article_info}

请判断该文章是否与筛选描述相关，并给出理由。"""
            
            # 调用AI服务
            response_text = None
            if self.ai_service:
                # 尝试使用AI服务的recommender
                if hasattr(self.ai_service, 'recommender'):
                    recommender = self.ai_service.recommender
                    if hasattr(recommender, 'use_direct_api') and recommender.use_direct_api:
                        response_text = recommender._call_api_direct(system_prompt, user_prompt)
                    elif hasattr(recommender, 'llm'):
                        from langchain_core.prompts import ChatPromptTemplate
                        prompt_template = ChatPromptTemplate.from_messages([
                            ("system", system_prompt),
                            ("human", user_prompt)
                        ])
                        prompt = prompt_template.format_messages()
                        response = recommender.llm.invoke(prompt)
                        response_text = response.content if hasattr(response, 'content') else str(response)
            
            # 如果没有AI服务或调用失败，尝试直接创建AIRecommender
            if not response_text:
                from ai_recommender.recommender import AIRecommender
                recommender = AIRecommender({})
                if hasattr(recommender, 'use_direct_api') and recommender.use_direct_api:
                    response_text = recommender._call_api_direct(system_prompt, user_prompt)
                elif hasattr(recommender, 'llm'):
                    from langchain_core.prompts import ChatPromptTemplate
                    prompt_template = ChatPromptTemplate.from_messages([
                        ("system", system_prompt),
                        ("human", user_prompt)
                    ])
                    prompt = prompt_template.format_messages()
                    response = recommender.llm.invoke(prompt)
                    response_text = response.content if hasattr(response, 'content') else str(response)
            
            if not response_text:
                logger.warning("无法获取AI响应，使用降级方案")
                return self._simple_keyword_match(title, description, content_preview)
            
            # 解析响应
            import json
            import re
            
            # 尝试提取JSON
            json_match = re.search(r'\{[^{}]*"match"[^{}]*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                match = result.get('match', False)
                reason = result.get('reason', '')
                logger.debug(f"AI筛选结果: match={match}, reason={reason}")
                return bool(match)
            else:
                # 如果无法解析JSON，尝试从文本中提取
                if 'true' in response_text.lower() or '符合' in response_text or '相关' in response_text:
                    return True
                elif 'false' in response_text.lower() or '不符合' in response_text or '不相关' in response_text:
                    return False
                else:
                    # 默认返回True（容错）
                    logger.warning(f"无法解析AI响应，默认通过: {response_text[:100]}")
                    return True
                    
        except Exception as e:
            logger.error(f"AI筛选调用失败: {e}")
            # 降级到简单关键词匹配
            return self._simple_keyword_match(title, description, content_preview)
    
    def _simple_keyword_match(self, title: str, description: str, content_preview: str) -> bool:
        """
        简单的关键词匹配（降级方案）
        
        Args:
            title: 文章标题
            description: 文章简介
            content_preview: 内容预览
            
        Returns:
            是否匹配
        """
        if not self.filter_description:
            return True
        
        # 提取关键词（简单的分词）
        keywords = self.filter_description.lower().split()
        text = f"{title} {description} {content_preview}".lower()
        
        # 检查是否包含关键词
        match_count = sum(1 for keyword in keywords if keyword in text)
        
        # 如果匹配的关键词超过50%，认为匹配
        return match_count >= len(keywords) * 0.5

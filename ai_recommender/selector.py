"""
手动选择器
提供手动选择主题和文章的功能
"""
from typing import List, Dict, Any, Optional
from datetime import datetime


class ManualSelector:
    """手动选择器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化手动选择器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.selections = {}  # 存储选择记录
    
    def select_topics(self, user_id: str, topics: List[str], 
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
        selection_id = f"selection_{datetime.now().timestamp()}"
        
        selection = {
            'id': selection_id,
            'user_id': user_id,
            'type': 'topics',
            'topics': topics,
            'articles': articles,
            'created_at': datetime.now().isoformat(),
            'status': 'active'
        }
        
        self.selections[selection_id] = selection
        
        return selection
    
    def select_articles(self, user_id: str, article_ids: List[str],
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
        selection_id = f"selection_{datetime.now().timestamp()}"
        
        selection = {
            'id': selection_id,
            'user_id': user_id,
            'type': 'articles',
            'article_ids': article_ids,
            'reason': reason,
            'created_at': datetime.now().isoformat(),
            'status': 'active'
        }
        
        self.selections[selection_id] = selection
        
        return selection
    
    def get_selections(self, user_id: Optional[str] = None,
                      selection_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取选择记录
        
        Args:
            user_id: 用户ID（可选）
            selection_type: 选择类型（topics/articles，可选）
            
        Returns:
            选择记录列表
        """
        results = list(self.selections.values())
        
        if user_id:
            results = [r for r in results if r.get('user_id') == user_id]
        
        if selection_type:
            results = [r for r in results if r.get('type') == selection_type]
        
        # 按创建时间倒序
        results.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return results
    
    def update_selection(self, selection_id: str, updates: Dict[str, Any]) -> bool:
        """
        更新选择记录
        
        Args:
            selection_id: 选择ID
            updates: 更新内容
            
        Returns:
            是否成功
        """
        if selection_id not in self.selections:
            return False
        
        self.selections[selection_id].update(updates)
        self.selections[selection_id]['updated_at'] = datetime.now().isoformat()
        
        return True
    
    def delete_selection(self, selection_id: str) -> bool:
        """
        删除选择记录
        
        Args:
            selection_id: 选择ID
            
        Returns:
            是否成功
        """
        if selection_id in self.selections:
            del self.selections[selection_id]
            return True
        return False
    
    def get_selection_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取选择统计
        
        Args:
            user_id: 用户ID（可选）
            
        Returns:
            统计数据
        """
        selections = self.get_selections(user_id)
        
        topic_selections = [s for s in selections if s.get('type') == 'topics']
        article_selections = [s for s in selections if s.get('type') == 'articles']
        
        return {
            'total_selections': len(selections),
            'topic_selections': len(topic_selections),
            'article_selections': len(article_selections),
            'active_selections': len([s for s in selections if s.get('status') == 'active'])
        }

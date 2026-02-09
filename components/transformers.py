"""
转换器实现
"""
from typing import Dict, Any
from datetime import datetime
from .base import BaseTransformer

# 可选导入 DataNormalizer（可能依赖 jieba）
try:
    from pipeline.normalizer import DataNormalizer
    NORMALIZER_AVAILABLE = True
except ImportError:
    NORMALIZER_AVAILABLE = False
    DataNormalizer = None


class DataTransformer(BaseTransformer):
    """数据转换器"""
    
    def transform(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """转换数据格式"""
        # 添加时间戳
        if 'created_at' not in item:
            item['created_at'] = datetime.now().isoformat()
        
        # 数据类型转换
        transforms = self.config.get('transforms', {})
        for field, transform_type in transforms.items():
            if field in item:
                if transform_type == 'int':
                    try:
                        item[field] = int(item[field])
                    except:
                        pass
                elif transform_type == 'float':
                    try:
                        item[field] = float(item[field])
                    except:
                        pass
                elif transform_type == 'date':
                    try:
                        item[field] = datetime.fromisoformat(item[field]).isoformat()
                    except:
                        pass
        
        return item


class NormalizerTransformer(BaseTransformer):
    """标准化转换器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        if NORMALIZER_AVAILABLE and DataNormalizer:
            try:
                self.normalizer = DataNormalizer(config)
            except Exception:
                self.normalizer = None
        else:
            self.normalizer = None
    
    def transform(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """标准化数据"""
        if self.normalizer is None:
            # 如果 normalizer 不可用，只做基本的文本清理
            if 'content' in item and isinstance(item['content'], str):
                item['content'] = item['content'].strip()
            if 'title' in item and isinstance(item['title'], str):
                item['title'] = item['title'].strip()
            return item
        
        # 文本清洗
        if 'content' in item:
            item['content'] = self.normalizer.clean_text(item['content'])
        
        if 'title' in item:
            item['title'] = self.normalizer.clean_text(item['title'])
        
        # 结构化提取
        structured = self.normalizer.extract_structure(item)
        item.update(structured)
        
        return item

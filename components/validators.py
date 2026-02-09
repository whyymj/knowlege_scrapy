"""
验证器实现
"""
from typing import Dict, Any
from pipeline.quality_monitor import DataQualityMonitor
from .base import BaseValidator


class DataValidator(BaseValidator):
    """数据验证器"""
    
    def validate(self, item: Dict[str, Any]) -> bool:
        """验证数据完整性"""
        required_fields = self.config.get('required_fields', [])
        
        for field in required_fields:
            if field not in item or not item[field]:
                return False
        
        return True


class QualityValidator(BaseValidator):
    """质量验证器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.monitor = DataQualityMonitor(config)
    
    def validate(self, item: Dict[str, Any]) -> bool:
        """验证数据质量"""
        # 完整性检查
        if not self.monitor.check_completeness(item):
            return False
        
        # 重复检测
        if not self.monitor.check_duplication(item):
            return False
        
        return True

"""
数据处理管道主类
整合标准化和质量监控
"""
from typing import Dict, List, Optional, Any, Tuple
from .normalizer import DataNormalizer
from .quality_monitor import DataQualityMonitor


class DataProcessor:
    """数据处理管道主类"""
    
    def __init__(self, quality_config: Optional[Dict[str, Any]] = None):
        """
        初始化数据处理器
        
        Args:
            quality_config: 质量监控配置
        """
        self.normalizer = DataNormalizer()
        self.quality_monitor = DataQualityMonitor(quality_config)
    
    def process(self, item: Dict[str, Any], check_quality: bool = True) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """
        处理数据项
        
        Args:
            item: 原始数据项
            check_quality: 是否进行质量检查
            
        Returns:
            (处理后的数据项, 质量报告)
        """
        # 数据标准化
        normalized_item = self.normalizer.normalize(item)
        
        # 质量检查
        quality_report = None
        if check_quality:
            passed, quality_report = self.quality_monitor.check(normalized_item)
            normalized_item['quality_passed'] = passed
            normalized_item['quality_score'] = quality_report.get('overall_score', 0.0)
        
        return normalized_item, quality_report
    
    def process_batch(self, items: List[Dict[str, Any]], check_quality: bool = True) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        批量处理数据
        
        Args:
            items: 数据项列表
            check_quality: 是否进行质量检查
            
        Returns:
            (处理后的数据列表, 批量质量报告)
        """
        processed_items = []
        
        for item in items:
            processed_item, _ = self.process(item, check_quality=False)
            processed_items.append(processed_item)
        
        # 批量质量检查
        batch_report = None
        if check_quality:
            batch_report = self.quality_monitor.generate_quality_report(processed_items)
            
            # 为每个数据项添加质量信息
            for i, item in enumerate(processed_items):
                passed, quality_report = self.quality_monitor.check(item)
                item['quality_passed'] = passed
                item['quality_score'] = quality_report.get('overall_score', 0.0)
        
        return processed_items, batch_report

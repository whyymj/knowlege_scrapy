"""
输出器实现
"""
from typing import Dict, List, Any
from storage import StorageManager
from .base import BaseOutput


class DatabaseOutput(BaseOutput):
    """数据库输出器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.storage_manager = StorageManager()
        self.output_type = config.get('output_type', 'mysql')
        self.collection = config.get('collection', 'items')
    
    async def output(self, items: List[Dict[str, Any]]):
        """输出到数据库"""
        for item in items:
            if self.output_type == 'mysql':
                # MySQL输出（通过现有pipeline）
                pass
            elif self.output_type == 'mongodb':
                self.storage_manager.store_document(self.collection, item)
            elif self.output_type == 'timeseries':
                self.storage_manager.store_timeseries(self.collection, item)


class FileOutput(BaseOutput):
    """文件输出器"""
    
    async def output(self, items: List[Dict[str, Any]]):
        """输出到文件"""
        import json
        import os
        
        output_file = self.config.get('file', 'output.json')
        output_format = self.config.get('format', 'json')
        
        # 确保目录存在
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
        
        if output_format == 'json':
            with open(output_file, 'a', encoding='utf-8') as f:
                for item in items:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
        elif output_format == 'csv':
            import csv
            if items:
                with open(output_file, 'a', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=items[0].keys())
                    if os.path.getsize(output_file) == 0:
                        writer.writeheader()
                    writer.writerows(items)

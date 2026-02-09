"""
文档数据库存储（MongoDB/Elasticsearch）
用于非结构化文本、分析结果
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from .base import BaseStorage, StorageType

try:
    from pymongo import MongoClient
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    MongoClient = None

try:
    from elasticsearch import Elasticsearch
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False
    Elasticsearch = None


class MongoDBStorage(BaseStorage):
    """MongoDB 文档数据库存储"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.storage_type = StorageType.MONGODB
        self.client = None
        self.db = None
        self.database_name = config.get('database', 'scrapy_doc')
    
    def connect(self) -> bool:
        """连接 MongoDB"""
        if not MONGODB_AVAILABLE:
            raise ImportError('pymongo 未安装，请运行: pip install pymongo')
        
        try:
            host = self.config.get('host', 'localhost')
            port = self.config.get('port', 27017)
            username = self.config.get('username')
            password = self.config.get('password')
            
            if username and password:
                uri = f'mongodb://{username}:{password}@{host}:{port}/'
            else:
                uri = f'mongodb://{host}:{port}/'
            
            self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            self.db = self.client[self.database_name]
            
            # 测试连接
            self.client.server_info()
            
            self.connected = True
            return True
        except Exception as e:
            print(f'MongoDB 连接失败: {e}')
            self.connected = False
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.client:
            self.client.close()
            self.connected = False
    
    def insert(self, collection: str, data: Dict[str, Any]) -> bool:
        """插入文档"""
        if not self.connected:
            return False
        
        try:
            # 添加时间戳
            if 'created_at' not in data:
                data['created_at'] = datetime.now()
            data['updated_at'] = datetime.now()
            
            self.db[collection].insert_one(data)
            return True
        except Exception as e:
            print(f'MongoDB 插入失败: {e}')
            return False
    
    def query(self, collection: str, filters: Optional[Dict] = None, limit: Optional[int] = None) -> List[Dict]:
        """查询文档"""
        if not self.connected:
            return []
        
        try:
            query = filters or {}
            cursor = self.db[collection].find(query)
            
            if limit:
                cursor = cursor.limit(limit)
            
            results = list(cursor)
            # 转换 ObjectId 为字符串
            for result in results:
                if '_id' in result:
                    result['_id'] = str(result['_id'])
            
            return results
        except Exception as e:
            print(f'MongoDB 查询失败: {e}')
            return []
    
    def update(self, collection: str, filters: Dict, data: Dict[str, Any]) -> bool:
        """更新文档"""
        if not self.connected:
            return False
        
        try:
            data['updated_at'] = datetime.now()
            result = self.db[collection].update_many(
                filters,
                {'$set': data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f'MongoDB 更新失败: {e}')
            return False
    
    def delete(self, collection: str, filters: Dict) -> bool:
        """删除文档"""
        if not self.connected:
            return False
        
        try:
            result = self.db[collection].delete_many(filters)
            return result.deleted_count > 0
        except Exception as e:
            print(f'MongoDB 删除失败: {e}')
            return False
    
    def create_index(self, collection: str, fields: List[str], unique: bool = False):
        """
        创建索引
        
        Args:
            collection: 集合名
            fields: 字段列表
            unique: 是否唯一索引
        """
        if not self.connected:
            return False
        
        try:
            index_fields = [(field, 1) for field in fields]
            self.db[collection].create_index(index_fields, unique=unique)
            return True
        except Exception as e:
            print(f'MongoDB 创建索引失败: {e}')
            return False


class ElasticsearchStorage(BaseStorage):
    """Elasticsearch 文档数据库存储"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.storage_type = StorageType.ELASTICSEARCH
        self.client = None
        self.index_prefix = config.get('index_prefix', 'scrapy')
    
    def connect(self) -> bool:
        """连接 Elasticsearch"""
        if not ELASTICSEARCH_AVAILABLE:
            raise ImportError('elasticsearch 未安装，请运行: pip install elasticsearch')
        
        try:
            hosts = [{
                'host': self.config.get('host', 'localhost'),
                'port': self.config.get('port', 9200)
            }]
            
            self.client = Elasticsearch(
                hosts=hosts,
                http_auth=(self.config.get('username', ''), self.config.get('password', '')) if self.config.get('username') else None,
                timeout=30
            )
            
            # 测试连接
            if not self.client.ping():
                raise ConnectionError('Elasticsearch 连接失败')
            
            self.connected = True
            return True
        except Exception as e:
            print(f'Elasticsearch 连接失败: {e}')
            self.connected = False
            return False
    
    def disconnect(self):
        """断开连接"""
        self.client = None
        self.connected = False
    
    def _get_index_name(self, collection: str) -> str:
        """获取索引名称"""
        return f"{self.index_prefix}_{collection}"
    
    def insert(self, collection: str, data: Dict[str, Any]) -> bool:
        """插入文档"""
        if not self.connected:
            return False
        
        try:
            index_name = self._get_index_name(collection)
            
            # 添加时间戳
            if '@timestamp' not in data:
                data['@timestamp'] = datetime.now().isoformat()
            
            self.client.index(index=index_name, body=data)
            return True
        except Exception as e:
            print(f'Elasticsearch 插入失败: {e}')
            return False
    
    def query(self, collection: str, filters: Optional[Dict] = None, limit: Optional[int] = None) -> List[Dict]:
        """查询文档"""
        if not self.connected:
            return []
        
        try:
            index_name = self._get_index_name(collection)
            
            query_body = {
                'query': {'match_all': {}}
            }
            
            if filters:
                # 构建查询条件
                must_conditions = []
                for key, value in filters.items():
                    must_conditions.append({'match': {key: value}})
                query_body['query'] = {'bool': {'must': must_conditions}}
            
            if limit:
                query_body['size'] = limit
            
            response = self.client.search(index=index_name, body=query_body)
            
            results = []
            for hit in response['hits']['hits']:
                result = hit['_source']
                result['_id'] = hit['_id']
                results.append(result)
            
            return results
        except Exception as e:
            print(f'Elasticsearch 查询失败: {e}')
            return []
    
    def search_text(self, collection: str, query_text: str, fields: List[str] = None, limit: int = 10) -> List[Dict]:
        """
        全文搜索
        
        Args:
            collection: 集合名
            query_text: 搜索文本
            fields: 搜索字段（默认所有字段）
            limit: 返回数量
            
        Returns:
            搜索结果列表
        """
        if not self.connected:
            return []
        
        try:
            index_name = self._get_index_name(collection)
            
            query_body = {
                'query': {
                    'multi_match': {
                        'query': query_text,
                        'fields': fields or ['*']
                    }
                },
                'size': limit
            }
            
            response = self.client.search(index=index_name, body=query_body)
            
            results = []
            for hit in response['hits']['hits']:
                result = hit['_source']
                result['_id'] = hit['_id']
                result['_score'] = hit['_score']
                results.append(result)
            
            return results
        except Exception as e:
            print(f'Elasticsearch 全文搜索失败: {e}')
            return []
    
    def update(self, collection: str, filters: Dict, data: Dict[str, Any]) -> bool:
        """更新文档"""
        if not self.connected:
            return False
        
        try:
            index_name = self._get_index_name(collection)
            
            # Elasticsearch 使用 script 更新
            script = {
                'source': ' '.join([f'ctx._source.{k} = params.{k};' for k in data.keys()]),
                'params': data
            }
            
            self.client.update_by_query(
                index=index_name,
                body={
                    'query': {'match': filters},
                    'script': script
                }
            )
            return True
        except Exception as e:
            print(f'Elasticsearch 更新失败: {e}')
            return False
    
    def delete(self, collection: str, filters: Dict) -> bool:
        """删除文档"""
        if not self.connected:
            return False
        
        try:
            index_name = self._get_index_name(collection)
            self.client.delete_by_query(
                index=index_name,
                body={'query': {'match': filters}}
            )
            return True
        except Exception as e:
            print(f'Elasticsearch 删除失败: {e}')
            return False

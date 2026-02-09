"""
向量数据库存储（Qdrant/Pinecone/Weaviate）
用于AI论文/新闻的语义检索
"""
from typing import Dict, List, Optional, Any
import numpy as np
from .base import BaseStorage, StorageType

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    QdrantClient = None

try:
    import pinecone
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    pinecone = None


class QdrantStorage(BaseStorage):
    """Qdrant 向量数据库存储"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.storage_type = StorageType.QDRANT
        self.client = None
        self.collection_name = config.get('collection', 'vectors')
        self.vector_size = config.get('vector_size', 1536)  # OpenAI embedding 维度
    
    def connect(self) -> bool:
        """连接 Qdrant"""
        if not QDRANT_AVAILABLE:
            raise ImportError('qdrant-client 未安装，请运行: pip install qdrant-client')
        
        try:
            self.client = QdrantClient(
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 6333),
                api_key=self.config.get('api_key'),
                timeout=self.config.get('timeout', 30)
            )
            
            # 创建集合（如果不存在）
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
            
            self.connected = True
            return True
        except Exception as e:
            print(f'Qdrant 连接失败: {e}')
            self.connected = False
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.client:
            self.client.close()
            self.connected = False
    
    def insert(self, collection: str, data: Dict[str, Any]) -> bool:
        """插入向量数据"""
        if not self.connected:
            return False
        
        try:
            vector = data.get('vector')
            if vector is None:
                return False
            
            # 转换为列表（如果是numpy数组）
            if isinstance(vector, np.ndarray):
                vector = vector.tolist()
            
            point = PointStruct(
                id=data.get('id', hash(str(data))),
                vector=vector,
                payload={
                    'text': data.get('text', ''),
                    'metadata': {k: v for k, v in data.items() if k not in ['vector', 'id']}
                }
            )
            
            self.client.upsert(
                collection_name=collection or self.collection_name,
                points=[point]
            )
            return True
        except Exception as e:
            print(f'Qdrant 插入失败: {e}')
            return False
    
    def query(self, collection: str, filters: Optional[Dict] = None, limit: Optional[int] = None) -> List[Dict]:
        """查询向量数据"""
        if not self.connected:
            return []
        
        try:
            # 向量相似度搜索
            query_vector = filters.get('vector') if filters else None
            if not query_vector:
                # 如果没有查询向量，返回所有数据
                scroll_result = self.client.scroll(
                    collection_name=collection or self.collection_name,
                    limit=limit or 10
                )
                points = scroll_result[0]
            else:
                # 向量搜索
                if isinstance(query_vector, np.ndarray):
                    query_vector = query_vector.tolist()
                
                search_result = self.client.search(
                    collection_name=collection or self.collection_name,
                    query_vector=query_vector,
                    limit=limit or 10
                )
                points = [hit for hit in search_result]
            
            results = []
            for point in points:
                if hasattr(point, 'payload'):
                    result = {
                        'id': point.id,
                        'score': getattr(point, 'score', None),
                        **point.payload.get('metadata', {}),
                        'text': point.payload.get('text', '')
                    }
                else:
                    result = {
                        'id': point.id,
                        **point.payload.get('metadata', {}),
                        'text': point.payload.get('text', '')
                    }
                results.append(result)
            
            return results
        except Exception as e:
            print(f'Qdrant 查询失败: {e}')
            return []
    
    def search_similar(self, collection: str, query_vector: List[float], limit: int = 10, 
                      score_threshold: float = 0.7) -> List[Dict]:
        """
        相似度搜索
        
        Args:
            collection: 集合名
            query_vector: 查询向量
            limit: 返回数量
            score_threshold: 相似度阈值
            
        Returns:
            相似结果列表
        """
        if not self.connected:
            return []
        
        try:
            if isinstance(query_vector, np.ndarray):
                query_vector = query_vector.tolist()
            
            search_result = self.client.search(
                collection_name=collection or self.collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold
            )
            
            results = []
            for hit in search_result:
                result = {
                    'id': hit.id,
                    'score': hit.score,
                    **hit.payload.get('metadata', {}),
                    'text': hit.payload.get('text', '')
                }
                results.append(result)
            
            return results
        except Exception as e:
            print(f'Qdrant 相似度搜索失败: {e}')
            return []
    
    def update(self, collection: str, filters: Dict, data: Dict[str, Any]) -> bool:
        """更新向量数据"""
        # Qdrant 使用 upsert，直接插入即可
        return self.insert(collection, {**filters, **data})
    
    def delete(self, collection: str, filters: Dict) -> bool:
        """删除向量数据"""
        if not self.connected:
            return False
        
        try:
            point_id = filters.get('id')
            if point_id:
                self.client.delete(
                    collection_name=collection or self.collection_name,
                    points_selector=[point_id]
                )
                return True
            return False
        except Exception as e:
            print(f'Qdrant 删除失败: {e}')
            return False


class PineconeStorage(BaseStorage):
    """Pinecone 向量数据库存储"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.storage_type = StorageType.PINECONE
        self.index = None
        self.index_name = config.get('index_name', 'scrapy-vectors')
    
    def connect(self) -> bool:
        """连接 Pinecone"""
        if not PINECONE_AVAILABLE:
            raise ImportError('pinecone-client 未安装，请运行: pip install pinecone-client')
        
        try:
            api_key = self.config.get('api_key')
            if not api_key:
                raise ValueError('Pinecone API Key 未配置')
            
            pinecone.init(api_key=api_key, environment=self.config.get('environment', 'us-east1-gcp'))
            
            # 获取或创建索引
            if self.index_name not in pinecone.list_indexes():
                pinecone.create_index(
                    name=self.index_name,
                    dimension=self.config.get('vector_size', 1536),
                    metric='cosine'
                )
            
            self.index = pinecone.Index(self.index_name)
            self.connected = True
            return True
        except Exception as e:
            print(f'Pinecone 连接失败: {e}')
            self.connected = False
            return False
    
    def disconnect(self):
        """断开连接"""
        self.index = None
        self.connected = False
    
    def insert(self, collection: str, data: Dict[str, Any]) -> bool:
        """插入向量数据"""
        if not self.connected:
            return False
        
        try:
            vector = data.get('vector')
            vector_id = data.get('id', str(hash(str(data))))
            
            if vector is None:
                return False
            
            if isinstance(vector, np.ndarray):
                vector = vector.tolist()
            
            metadata = {k: v for k, v in data.items() if k not in ['vector', 'id']}
            
            self.index.upsert([(vector_id, vector, metadata)])
            return True
        except Exception as e:
            print(f'Pinecone 插入失败: {e}')
            return False
    
    def query(self, collection: str, filters: Optional[Dict] = None, limit: Optional[int] = None) -> List[Dict]:
        """查询向量数据"""
        if not self.connected:
            return []
        
        try:
            query_vector = filters.get('vector') if filters else None
            if not query_vector:
                return []
            
            if isinstance(query_vector, np.ndarray):
                query_vector = query_vector.tolist()
            
            results = self.index.query(
                vector=query_vector,
                top_k=limit or 10,
                include_metadata=True
            )
            
            return [
                {
                    'id': match.id,
                    'score': match.score,
                    **match.metadata
                }
                for match in results.matches
            ]
        except Exception as e:
            print(f'Pinecone 查询失败: {e}')
            return []
    
    def update(self, collection: str, filters: Dict, data: Dict[str, Any]) -> bool:
        """更新向量数据"""
        return self.insert(collection, {**filters, **data})
    
    def delete(self, collection: str, filters: Dict) -> bool:
        """删除向量数据"""
        if not self.connected:
            return False
        
        try:
            vector_id = filters.get('id')
            if vector_id:
                self.index.delete(ids=[vector_id])
                return True
            return False
        except Exception as e:
            print(f'Pinecone 删除失败: {e}')
            return False

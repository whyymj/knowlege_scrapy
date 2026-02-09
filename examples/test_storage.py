"""
存储层测试示例
"""
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from storage import StorageManager, StorageType


def test_redis():
    """测试 Redis 缓存"""
    print("=" * 50)
    print("测试 Redis 缓存")
    print("=" * 50)
    
    try:
        manager = StorageManager()
        
        # 存储缓存
        print("\n存储缓存数据...")
        success = manager.store_cache('test_key', {'name': 'test', 'value': 123}, ttl=60)
        print(f"存储结果: {success}")
        
        # 获取缓存
        print("\n获取缓存数据...")
        value = manager.get_cache('test_key')
        print(f"获取结果: {value}")
        
    except Exception as e:
        print(f"测试失败: {e}")


def test_timeseries():
    """测试时序数据库"""
    print("\n" + "=" * 50)
    print("测试时序数据库（InfluxDB）")
    print("=" * 50)
    
    try:
        manager = StorageManager()
        
        # 存储时序数据
        print("\n存储时序数据...")
        data = {
            'time': datetime.now(),
            'symbol': 'AAPL',
            'price': 150.25,
            'volume': 1000000,
            'tags': {'market': 'NASDAQ'}
        }
        success = manager.store_timeseries('stock_prices', data)
        print(f"存储结果: {success}")
        
        # 查询时间范围数据
        print("\n查询时间范围数据...")
        start_time = datetime.now() - timedelta(days=1)
        end_time = datetime.now()
        results = manager.query_timeseries('stock_prices', start_time, end_time, {'symbol': 'AAPL'})
        print(f"查询结果数量: {len(results)}")
        
    except Exception as e:
        print(f"测试失败: {e}")
        print("提示: 请确保 InfluxDB 已启动并配置")


def test_vector():
    """测试向量数据库"""
    print("\n" + "=" * 50)
    print("测试向量数据库（Qdrant）")
    print("=" * 50)
    
    try:
        manager = StorageManager()
        
        # 存储向量数据
        print("\n存储向量数据...")
        import numpy as np
        vector = np.random.rand(1536).tolist()  # 模拟embedding向量
        
        data = {
            'id': 'doc_1',
            'vector': vector,
            'text': '这是一篇关于AI技术的文章',
            'title': 'AI技术突破',
            'category': 'AI'
        }
        success = manager.store_vector('documents', data)
        print(f"存储结果: {success}")
        
        # 相似度搜索
        print("\n相似度搜索...")
        query_vector = np.random.rand(1536).tolist()
        results = manager.search_similar('documents', query_vector, limit=5)
        print(f"搜索结果数量: {len(results)}")
        
    except Exception as e:
        print(f"测试失败: {e}")
        print("提示: 请确保 Qdrant 已启动并配置")


def test_document():
    """测试文档数据库"""
    print("\n" + "=" * 50)
    print("测试文档数据库（MongoDB）")
    print("=" * 50)
    
    try:
        manager = StorageManager()
        
        # 存储文档
        print("\n存储文档...")
        data = {
            'title': 'AI技术分析报告',
            'content': '这是一份详细的AI技术分析报告...',
            'author': '分析师',
            'tags': ['AI', '技术', '分析'],
            'analysis_result': {
                'sentiment': 'positive',
                'score': 0.85
            }
        }
        success = manager.store_document('reports', data)
        print(f"存储结果: {success}")
        
        # 全文搜索
        print("\n全文搜索...")
        results = manager.search_text('reports', 'AI技术', limit=10, use_elasticsearch=False)
        print(f"搜索结果数量: {len(results)}")
        
    except Exception as e:
        print(f"测试失败: {e}")
        print("提示: 请确保 MongoDB 已启动并配置")


def test_storage_manager():
    """测试存储管理器"""
    print("\n" + "=" * 50)
    print("测试存储管理器")
    print("=" * 50)
    
    try:
        manager = StorageManager()
        
        # 测试获取不同类型的存储
        print("\n获取 Redis 存储...")
        redis_storage = manager.get_storage(StorageType.REDIS)
        if redis_storage:
            print(f"Redis 连接状态: {redis_storage.connected}")
        
        print("\n获取 InfluxDB 存储...")
        influx_storage = manager.get_storage(StorageType.INFLUXDB)
        if influx_storage:
            print(f"InfluxDB 连接状态: {influx_storage.connected}")
        
        print("\n获取 Qdrant 存储...")
        qdrant_storage = manager.get_storage(StorageType.QDRANT)
        if qdrant_storage:
            print(f"Qdrant 连接状态: {qdrant_storage.connected}")
        
        # 关闭所有连接
        manager.close_all()
        print("\n所有存储连接已关闭")
        
    except Exception as e:
        print(f"测试失败: {e}")


if __name__ == '__main__':
    test_redis()
    test_timeseries()
    test_vector()
    test_document()
    test_storage_manager()

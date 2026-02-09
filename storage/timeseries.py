"""
时序数据库存储（InfluxDB/TimescaleDB）
用于存储股价、交易量等时间序列数据
"""
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from .base import BaseStorage, StorageType

try:
    from influxdb import InfluxDBClient
    INFLUXDB_AVAILABLE = True
except ImportError:
    INFLUXDB_AVAILABLE = False
    InfluxDBClient = None

try:
    import psycopg2
    from psycopg2.extras import execute_values
    TIMESCALEDB_AVAILABLE = True
except ImportError:
    TIMESCALEDB_AVAILABLE = False
    psycopg2 = None


class InfluxDBStorage(BaseStorage):
    """InfluxDB 时序数据库存储"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.storage_type = StorageType.INFLUXDB
        self.client = None
        self.database = config.get('database', 'scrapy_ts')
    
    def connect(self) -> bool:
        """连接 InfluxDB"""
        if not INFLUXDB_AVAILABLE:
            raise ImportError('influxdb 未安装，请运行: pip install influxdb')
        
        try:
            self.client = InfluxDBClient(
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 8086),
                username=self.config.get('username', ''),
                password=self.config.get('password', ''),
                database=self.database
            )
            
            # 创建数据库（如果不存在）
            databases = self.client.get_list_database()
            if not any(db['name'] == self.database for db in databases):
                self.client.create_database(self.database)
            
            self.client.switch_database(self.database)
            self.connected = True
            return True
        except Exception as e:
            print(f'InfluxDB 连接失败: {e}')
            self.connected = False
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.client:
            self.client.close()
            self.connected = False
    
    def insert(self, collection: str, data: Dict[str, Any]) -> bool:
        """插入时序数据"""
        if not self.connected:
            return False
        
        try:
            # InfluxDB 数据格式
            point = {
                'measurement': collection,
                'tags': data.get('tags', {}),
                'fields': {k: v for k, v in data.items() if k not in ['tags', 'time']},
                'time': data.get('time', datetime.now())
            }
            
            self.client.write_points([point])
            return True
        except Exception as e:
            print(f'InfluxDB 插入失败: {e}')
            return False
    
    def query(self, collection: str, filters: Optional[Dict] = None, limit: Optional[int] = None) -> List[Dict]:
        """查询时序数据"""
        if not self.connected:
            return []
        
        try:
            # 构建 InfluxQL 查询
            query = f'SELECT * FROM "{collection}"'
            
            if filters:
                conditions = []
                for key, value in filters.items():
                    if isinstance(value, (int, float)):
                        conditions.append(f'{key} = {value}')
                    else:
                        conditions.append(f'{key} = \'{value}\'')
                if conditions:
                    query += ' WHERE ' + ' AND '.join(conditions)
            
            if limit:
                query += f' LIMIT {limit}'
            
            result = self.client.query(query)
            points = list(result.get_points())
            return points
        except Exception as e:
            print(f'InfluxDB 查询失败: {e}')
            return []
    
    def update(self, collection: str, filters: Dict, data: Dict[str, Any]) -> bool:
        """更新数据（InfluxDB 不支持更新，需要删除后插入）"""
        # InfluxDB 是追加写入，不支持更新
        # 可以通过插入新数据点实现
        return self.insert(collection, {**filters, **data})
    
    def delete(self, collection: str, filters: Dict) -> bool:
        """删除数据"""
        if not self.connected:
            return False
        
        try:
            conditions = []
            for key, value in filters.items():
                if isinstance(value, (int, float)):
                    conditions.append(f'{key} = {value}')
                else:
                    conditions.append(f'{key} = \'{value}\'')
            
            if conditions:
                query = f'DELETE FROM "{collection}" WHERE ' + ' AND '.join(conditions)
                self.client.query(query)
                return True
            return False
        except Exception as e:
            print(f'InfluxDB 删除失败: {e}')
            return False
    
    def query_time_range(self, collection: str, start_time: datetime, end_time: datetime, 
                        tags: Optional[Dict] = None) -> List[Dict]:
        """
        查询时间范围内的数据
        
        Args:
            collection: 测量名称
            start_time: 开始时间
            end_time: 结束时间
            tags: 标签过滤
            
        Returns:
            数据列表
        """
        if not self.connected:
            return []
        
        try:
            query = f'SELECT * FROM "{collection}" WHERE time >= \'{start_time.isoformat()}\' AND time <= \'{end_time.isoformat()}\''
            
            if tags:
                tag_conditions = []
                for key, value in tags.items():
                    tag_conditions.append(f'{key} = \'{value}\'')
                if tag_conditions:
                    query += ' AND ' + ' AND '.join(tag_conditions)
            
            result = self.client.query(query)
            return list(result.get_points())
        except Exception as e:
            print(f'InfluxDB 时间范围查询失败: {e}')
            return []


class TimescaleDBStorage(BaseStorage):
    """TimescaleDB 时序数据库存储（基于PostgreSQL）"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.storage_type = StorageType.TIMESCALEDB
        self.conn = None
        self.database = config.get('database', 'scrapy_ts')
    
    def connect(self) -> bool:
        """连接 TimescaleDB"""
        if not TIMESCALEDB_AVAILABLE:
            raise ImportError('psycopg2 未安装，请运行: pip install psycopg2-binary')
        
        try:
            self.conn = psycopg2.connect(
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 5432),
                database=self.database,
                user=self.config.get('user', 'postgres'),
                password=self.config.get('password', '')
            )
            self.connected = True
            return True
        except Exception as e:
            print(f'TimescaleDB 连接失败: {e}')
            self.connected = False
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.conn:
            self.conn.close()
            self.connected = False
    
    def create_hypertable(self, table_name: str, time_column: str = 'time'):
        """
        创建超表（Hypertable）
        
        Args:
            table_name: 表名
            time_column: 时间列名
        """
        if not self.connected:
            return False
        
        try:
            cursor = self.conn.cursor()
            # 检查是否已经是超表
            cursor.execute(f"""
                SELECT * FROM timescaledb_information.hypertables 
                WHERE hypertable_name = '{table_name}'
            """)
            
            if not cursor.fetchone():
                # 转换为超表
                cursor.execute(f"""
                    SELECT create_hypertable('{table_name}', '{time_column}')
                """)
                self.conn.commit()
            
            cursor.close()
            return True
        except Exception as e:
            print(f'创建超表失败: {e}')
            self.conn.rollback()
            return False
    
    def insert(self, collection: str, data: Dict[str, Any]) -> bool:
        """插入时序数据"""
        if not self.connected:
            return False
        
        try:
            cursor = self.conn.cursor()
            
            # 确保表存在
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {collection} (
                    time TIMESTAMPTZ NOT NULL,
                    data JSONB
                )
            """)
            
            # 转换为超表（如果还不是）
            self.create_hypertable(collection)
            
            # 插入数据
            time_value = data.get('time', datetime.now())
            json_data = json.dumps({k: v for k, v in data.items() if k != 'time'})
            
            cursor.execute(f"""
                INSERT INTO {collection} (time, data) 
                VALUES (%s, %s)
            """, (time_value, json_data))
            
            self.conn.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f'TimescaleDB 插入失败: {e}')
            self.conn.rollback()
            return False
    
    def query(self, collection: str, filters: Optional[Dict] = None, limit: Optional[int] = None) -> List[Dict]:
        """查询时序数据"""
        if not self.connected:
            return []
        
        try:
            cursor = self.conn.cursor()
            query = f'SELECT time, data FROM {collection}'
            
            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(f"data->>'{key}' = %s")
                if conditions:
                    query += ' WHERE ' + ' AND '.join(conditions)
            
            query += ' ORDER BY time DESC'
            
            if limit:
                query += f' LIMIT {limit}'
            
            cursor.execute(query, list(filters.values()) if filters else None)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                result = {'time': row[0]}
                result.update(row[1])
                results.append(result)
            
            cursor.close()
            return results
        except Exception as e:
            print(f'TimescaleDB 查询失败: {e}')
            return []
    
    def update(self, collection: str, filters: Dict, data: Dict[str, Any]) -> bool:
        """更新数据"""
        if not self.connected:
            return False
        
        try:
            cursor = self.conn.cursor()
            
            # 构建更新条件
            conditions = []
            params = []
            for key, value in filters.items():
                conditions.append(f"data->>'{key}' = %s")
                params.append(str(value))
            
            # 构建更新数据
            update_data = json.dumps(data)
            
            query = f"""
                UPDATE {collection} 
                SET data = data || %s::jsonb
                WHERE {' AND '.join(conditions)}
            """
            params.append(update_data)
            
            cursor.execute(query, params)
            self.conn.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f'TimescaleDB 更新失败: {e}')
            self.conn.rollback()
            return False
    
    def delete(self, collection: str, filters: Dict) -> bool:
        """删除数据"""
        if not self.connected:
            return False
        
        try:
            cursor = self.conn.cursor()
            conditions = []
            params = []
            
            for key, value in filters.items():
                conditions.append(f"data->>'{key}' = %s")
                params.append(str(value))
            
            query = f'DELETE FROM {collection} WHERE {' AND '.join(conditions)}'
            cursor.execute(query, params)
            self.conn.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f'TimescaleDB 删除失败: {e}')
            self.conn.rollback()
            return False

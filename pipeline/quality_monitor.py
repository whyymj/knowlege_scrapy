"""
数据质量监控模块
"""
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import hashlib
import re


class DataQualityMonitor:
    """数据质量监控类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化数据质量监控器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        
        # 质量阈值配置
        self.min_title_length = self.config.get('min_title_length', 5)
        self.min_content_length = self.config.get('min_content_length', 50)
        self.max_content_length = self.config.get('max_content_length', 1000000)
        self.max_age_days = self.config.get('max_age_days', 365)  # 数据最大时效（天）
        
        # 异常值检测配置
        self.max_title_length = self.config.get('max_title_length', 500)
        self.suspicious_patterns = [
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+])+',  # URL过多
            r'[0-9]{11,}',  # 长数字串（可能是垃圾）
            r'[!@#$%^&*()_+=\[\]{}|;:,.<>?]{5,}',  # 过多特殊字符
        ]
    
    def check(self, item: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        检查数据质量
        
        Args:
            item: 数据项
            
        Returns:
            (是否通过, 质量报告)
        """
        report = {
            'passed': True,
            'issues': [],
            'scores': {},
            'checks': {}
        }
        
        # 完整性检查
        completeness_result = self.check_completeness(item)
        report['checks']['completeness'] = completeness_result
        report['scores']['completeness'] = completeness_result['score']
        if not completeness_result['passed']:
            report['passed'] = False
            report['issues'].extend(completeness_result['issues'])
        
        # 时效性验证
        timeliness_result = self.check_timeliness(item)
        report['checks']['timeliness'] = timeliness_result
        report['scores']['timeliness'] = timeliness_result['score']
        if not timeliness_result['passed']:
            report['passed'] = False
            report['issues'].extend(timeliness_result['issues'])
        
        # 重复检测
        duplicate_result = self.check_duplicate(item)
        report['checks']['duplicate'] = duplicate_result
        report['scores']['duplicate'] = duplicate_result['score']
        if not duplicate_result['passed']:
            report['passed'] = False
            report['issues'].extend(duplicate_result['issues'])
        
        # 异常值检测
        anomaly_result = self.check_anomalies(item)
        report['checks']['anomalies'] = anomaly_result
        report['scores']['anomaly'] = anomaly_result['score']
        if not anomaly_result['passed']:
            report['passed'] = False
            report['issues'].extend(anomaly_result['issues'])
        
        # 计算总体质量分数
        scores = [v for v in report['scores'].values() if isinstance(v, (int, float))]
        if scores:
            report['overall_score'] = sum(scores) / len(scores)
        else:
            report['overall_score'] = 0.0
        
        return report['passed'], report
    
    def check_completeness(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        完整性检查
        
        Args:
            item: 数据项
            
        Returns:
            检查结果
        """
        result = {
            'passed': True,
            'score': 100.0,
            'issues': [],
            'missing_fields': [],
            'empty_fields': []
        }
        
        # 必需字段列表
        required_fields = ['url', 'title']
        
        # 检查必需字段是否存在
        for field in required_fields:
            if field not in item:
                result['missing_fields'].append(field)
                result['issues'].append(f'缺少必需字段: {field}')
                result['passed'] = False
        
        # 检查字段是否为空
        important_fields = ['title', 'content', 'description']
        for field in important_fields:
            if field in item:
                value = item[field]
                if not value or (isinstance(value, str) and len(value.strip()) == 0):
                    result['empty_fields'].append(field)
                    result['issues'].append(f'字段为空: {field}')
        
        # 检查标题长度
        if 'title' in item and item['title']:
            title_len = len(item['title'])
            if title_len < self.min_title_length:
                result['issues'].append(f'标题过短: {title_len} 字符（最小 {self.min_title_length}）')
                result['passed'] = False
            elif title_len > self.max_title_length:
                result['issues'].append(f'标题过长: {title_len} 字符（最大 {self.max_title_length}）')
        
        # 检查内容长度
        content_fields = ['content', 'description', 'abstract']
        has_content = False
        for field in content_fields:
            if field in item and item[field]:
                content_len = len(item[field])
                if content_len >= self.min_content_length:
                    has_content = True
                    if content_len > self.max_content_length:
                        result['issues'].append(f'{field} 过长: {content_len} 字符（最大 {self.max_content_length}）')
                break
        
        if not has_content:
            result['issues'].append(f'缺少有效内容（最小 {self.min_content_length} 字符）')
            result['passed'] = False
        
        # 计算完整性分数
        total_fields = len(required_fields) + len(important_fields)
        missing_count = len(result['missing_fields']) + len(result['empty_fields'])
        result['score'] = max(0, (total_fields - missing_count) / total_fields * 100)
        
        return result
    
    def check_timeliness(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        时效性验证
        
        Args:
            item: 数据项
            
        Returns:
            检查结果
        """
        result = {
            'passed': True,
            'score': 100.0,
            'issues': [],
            'age_days': None,
            'is_fresh': True
        }
        
        # 获取发布时间
        publish_time = None
        time_fields = ['publish_time', 'published_date', 'date', 'created_at']
        
        for field in time_fields:
            if field in item and item[field]:
                publish_time = item[field]
                break
        
        if not publish_time:
            result['issues'].append('缺少发布时间信息')
            result['passed'] = False
            result['score'] = 50.0
            return result
        
        # 解析时间
        try:
            if isinstance(publish_time, str):
                # 尝试解析ISO格式
                if 'T' in publish_time:
                    dt = datetime.fromisoformat(publish_time.replace('Z', '+00:00'))
                else:
                    # 尝试其他格式
                    formats = [
                        '%Y-%m-%d %H:%M:%S',
                        '%Y-%m-%d',
                        '%Y/%m/%d %H:%M:%S',
                    ]
                    dt = None
                    for fmt in formats:
                        try:
                            dt = datetime.strptime(publish_time, fmt)
                            break
                        except:
                            continue
                    if not dt:
                        raise ValueError(f'无法解析时间格式: {publish_time}')
            elif isinstance(publish_time, datetime):
                dt = publish_time
            else:
                raise ValueError(f'不支持的时间类型: {type(publish_time)}')
            
            # 计算数据年龄（天）
            age = datetime.now() - dt
            age_days = age.days
            result['age_days'] = age_days
            
            # 检查是否过期
            if age_days > self.max_age_days:
                result['issues'].append(f'数据过期: {age_days} 天前（最大 {self.max_age_days} 天）')
                result['is_fresh'] = False
                result['passed'] = False
            
            # 计算时效性分数（越新分数越高）
            if age_days <= 1:
                result['score'] = 100.0
            elif age_days <= 7:
                result['score'] = 90.0
            elif age_days <= 30:
                result['score'] = 75.0
            elif age_days <= 90:
                result['score'] = 60.0
            elif age_days <= self.max_age_days:
                result['score'] = 40.0
            else:
                result['score'] = 0.0
                
        except Exception as e:
            result['issues'].append(f'时间解析失败: {str(e)}')
            result['passed'] = False
            result['score'] = 0.0
        
        return result
    
    def check_duplicate(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        重复检测
        
        Args:
            item: 数据项
            
        Returns:
            检查结果
        """
        result = {
            'passed': True,
            'score': 100.0,
            'issues': [],
            'duplicate_signals': []
        }
        
        # 生成内容哈希
        content_parts = []
        if item.get('title'):
            content_parts.append(item['title'])
        if item.get('content'):
            content_parts.append(item['content'][:500])  # 只取前500字符
        elif item.get('description'):
            content_parts.append(item['description'])
        
        if content_parts:
            content_hash = hashlib.md5(' '.join(content_parts).encode()).hexdigest()
            item['content_hash'] = content_hash
        
        # 检查URL重复
        if 'url' in item and item['url']:
            url_hash = hashlib.md5(item['url'].encode()).hexdigest()
            item['url_hash'] = url_hash
        
        # 检查标题相似度（简单版）
        if 'title' in item and item['title']:
            title = item['title'].strip().lower()
            # 如果标题太短，可能是重复的占位符
            if len(title) < 10:
                result['duplicate_signals'].append('标题过短，可能是重复内容')
        
        # 检查内容重复（检查是否有大量重复字符）
        if 'content' in item and item['content']:
            content = item['content']
            # 检查是否有大量重复的字符或单词
            if len(content) > 100:
                # 检查是否有超过50%的重复字符
                char_counts = {}
                for char in content[:500]:
                    char_counts[char] = char_counts.get(char, 0) + 1
                
                max_count = max(char_counts.values()) if char_counts else 0
                if max_count > len(content[:500]) * 0.3:
                    result['duplicate_signals'].append('内容可能存在重复字符')
        
        if result['duplicate_signals']:
            result['score'] = 70.0
            # 注意：这里不标记为失败，只是警告
        
        return result
    
    def check_anomalies(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        异常值检测
        
        Args:
            item: 数据项
            
        Returns:
            检查结果
        """
        result = {
            'passed': True,
            'score': 100.0,
            'issues': [],
            'anomalies': []
        }
        
        # 检查标题异常
        if 'title' in item and item['title']:
            title = item['title']
            
            # 检查可疑模式
            for pattern in self.suspicious_patterns:
                matches = re.findall(pattern, title)
                if len(matches) > 2:  # 如果匹配超过2次
                    result['anomalies'].append(f'标题包含可疑模式: {pattern}')
                    result['score'] -= 10
            
            # 检查是否全是数字或特殊字符
            if re.match(r'^[0-9\s]+$', title):
                result['anomalies'].append('标题全是数字')
                result['score'] -= 20
            
            # 检查是否包含过多特殊字符
            special_char_ratio = len(re.findall(r'[!@#$%^&*()_+=\[\]{}|;:,.<>?]', title)) / max(len(title), 1)
            if special_char_ratio > 0.3:
                result['anomalies'].append('标题包含过多特殊字符')
                result['score'] -= 15
        
        # 检查内容异常
        content_fields = ['content', 'description']
        for field in content_fields:
            if field in item and item[field]:
                content = item[field]
                
                # 检查URL数量
                url_count = len(re.findall(r'http[s]?://', content))
                if url_count > 10:
                    result['anomalies'].append(f'{field} 包含过多URL: {url_count}')
                    result['score'] -= 10
                
                # 检查是否主要是链接
                link_ratio = len(re.findall(r'http[s]?://[^\s]+', content)) / max(len(content.split()), 1)
                if link_ratio > 0.5:
                    result['anomalies'].append(f'{field} 主要是链接')
                    result['score'] -= 20
                
                # 检查是否有异常长的单词或数字
                long_items = re.findall(r'[a-zA-Z0-9]{50,}', content)
                if long_items:
                    result['anomalies'].append(f'{field} 包含异常长的字符串')
                    result['score'] -= 10
        
        # 检查时间异常
        if 'publish_time' in item and item['publish_time']:
            try:
                if isinstance(item['publish_time'], str):
                    dt = datetime.fromisoformat(item['publish_time'].replace('Z', '+00:00'))
                else:
                    dt = item['publish_time']
                
                # 检查是否是未来时间
                if dt > datetime.now():
                    result['anomalies'].append('发布时间是未来时间')
                    result['score'] -= 30
                    result['passed'] = False
                
                # 检查是否太古老（超过10年）
                age = datetime.now() - dt
                if age.days > 3650:
                    result['anomalies'].append('发布时间过于久远')
                    result['score'] -= 20
                    
            except:
                pass
        
        result['score'] = max(0, result['score'])
        
        if result['anomalies']:
            result['issues'].extend(result['anomalies'])
            if result['score'] < 50:
                result['passed'] = False
        
        return result
    
    def generate_quality_report(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        生成批量数据质量报告
        
        Args:
            items: 数据项列表
            
        Returns:
            质量报告
        """
        report = {
            'total': len(items),
            'passed': 0,
            'failed': 0,
            'average_score': 0.0,
            'issues_summary': {},
            'scores_distribution': {
                'excellent': 0,  # 90-100
                'good': 0,       # 70-89
                'fair': 0,       # 50-69
                'poor': 0        # <50
            }
        }
        
        total_score = 0.0
        issues_count = {}
        
        for item in items:
            passed, quality_report = self.check(item)
            
            if passed:
                report['passed'] += 1
            else:
                report['failed'] += 1
            
            score = quality_report.get('overall_score', 0.0)
            total_score += score
            
            # 统计分数分布
            if score >= 90:
                report['scores_distribution']['excellent'] += 1
            elif score >= 70:
                report['scores_distribution']['good'] += 1
            elif score >= 50:
                report['scores_distribution']['fair'] += 1
            else:
                report['scores_distribution']['poor'] += 1
            
            # 统计问题类型
            for issue in quality_report.get('issues', []):
                issue_type = issue.split(':')[0] if ':' in issue else '其他'
                issues_count[issue_type] = issues_count.get(issue_type, 0) + 1
        
        if len(items) > 0:
            report['average_score'] = round(total_score / len(items), 2)
        
        report['issues_summary'] = issues_count
        
        return report

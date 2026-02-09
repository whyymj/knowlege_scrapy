"""
数据标准化模块
"""
import re
import html
from typing import Dict, List, Optional, Any
from datetime import datetime
from bs4 import BeautifulSoup

# 可选依赖：jieba（中文分词）
try:
    import jieba
    import jieba.analyse
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False
    import warnings
    warnings.warn("jieba 模块未安装，中文分词功能将不可用。请运行: pip install jieba")


class DataNormalizer:
    """数据标准化类"""
    
    def __init__(self):
        """初始化数据标准化器"""
        # 初始化 jieba（如果可用）
        if JIEBA_AVAILABLE:
            try:
                jieba.initialize()
            except Exception:
                pass  # jieba 初始化失败时继续，不影响其他功能
        
        # 情感关键词（简化版，实际可以使用更复杂的模型）
        self.positive_keywords = [
            '利好', '上涨', '增长', '突破', '创新', '成功', '优秀', '领先',
            '突破', '提升', '改善', '优化', '进步', '发展', '繁荣', '强劲'
        ]
        self.negative_keywords = [
            '下跌', '下降', '亏损', '失败', '风险', '危机', '问题', '困难',
            '下滑', '恶化', '衰退', '疲软', '担忧', '警告', '负面', '不利'
        ]
        self.neutral_keywords = [
            '维持', '稳定', '持平', '正常', '常规', '标准', '一般', '普通'
        ]
    
    def normalize(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        标准化数据项
        
        Args:
            item: 原始数据项
            
        Returns:
            标准化后的数据项
        """
        normalized = item.copy()
        
        # 文本清洗
        normalized = self._clean_text(normalized)
        
        # 结构化提取
        normalized = self._extract_structure(normalized)
        
        # 情感标签预标注
        normalized = self._label_sentiment(normalized)
        
        # 关键实体识别
        normalized = self._extract_entities(normalized)
        
        # 添加标准化时间戳
        normalized['normalized_time'] = datetime.now().isoformat()
        
        return normalized
    
    def _clean_text(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        文本清洗
        
        Args:
            item: 数据项
            
        Returns:
            清洗后的数据项
        """
        # 清洗标题
        if 'title' in item and item['title']:
            item['title'] = self._clean_html(item['title'])
            item['title'] = self._normalize_encoding(item['title'])
            item['title'] = item['title'].strip()
        
        # 清洗描述
        if 'description' in item and item['description']:
            item['description'] = self._clean_html(item['description'])
            item['description'] = self._normalize_encoding(item['description'])
            item['description'] = item['description'].strip()
        
        # 清洗内容
        if 'content' in item and item['content']:
            item['content'] = self._clean_html(item['content'])
            item['content'] = self._normalize_encoding(item['content'])
            item['content'] = self._remove_extra_whitespace(item['content'])
            item['content'] = item['content'].strip()
        
        # 清洗摘要
        if 'abstract' in item and item['abstract']:
            item['abstract'] = self._clean_html(item['abstract'])
            item['abstract'] = self._normalize_encoding(item['abstract'])
            item['abstract'] = item['abstract'].strip()
        
        return item
    
    def _clean_html(self, text: str) -> str:
        """
        去除HTML标签
        
        Args:
            text: 包含HTML的文本
            
        Returns:
            纯文本
        """
        if not text:
            return ''
        
        # 使用 BeautifulSoup 解析HTML
        try:
            soup = BeautifulSoup(text, 'html.parser')
            # 移除脚本和样式
            for script in soup(["script", "style"]):
                script.decompose()
            # 获取文本
            text = soup.get_text()
        except:
            # 如果解析失败，使用正则表达式简单去除标签
            text = re.sub(r'<[^>]+>', '', text)
        
        # HTML实体解码
        text = html.unescape(text)
        
        return text
    
    def _normalize_encoding(self, text: str) -> str:
        """
        标准化编码
        
        Args:
            text: 文本
            
        Returns:
            标准化后的文本
        """
        if not text:
            return ''
        
        # 统一换行符
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # 去除特殊空白字符
        text = re.sub(r'[\u200b-\u200d\ufeff]', '', text)
        
        # 统一引号
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        return text
    
    def _remove_extra_whitespace(self, text: str) -> str:
        """
        移除多余的空白字符
        
        Args:
            text: 文本
            
        Returns:
            清理后的文本
        """
        if not text:
            return ''
        
        # 多个空格合并为一个
        text = re.sub(r' +', ' ', text)
        
        # 多个换行合并为两个
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text
    
    def _extract_structure(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        结构化提取
        
        Args:
            item: 数据项
            
        Returns:
            包含结构化字段的数据项
        """
        # 提取标题
        if 'title' not in item or not item.get('title'):
            # 尝试从其他字段提取标题
            if 'headline' in item:
                item['title'] = item['headline']
            elif 'name' in item:
                item['title'] = item['name']
        
        # 提取正文
        if 'content' not in item or not item.get('content'):
            # 尝试从其他字段提取内容
            if 'body' in item:
                item['content'] = item['body']
            elif 'text' in item:
                item['content'] = item['text']
            elif 'description' in item:
                item['content'] = item['description']
        
        # 提取发布时间
        item['publish_time'] = self._extract_publish_time(item)
        
        # 提取来源
        item['source'] = self._extract_source(item)
        
        # 提取作者
        if 'author' not in item or not item.get('author'):
            if 'authors' in item:
                # 如果是列表，转换为字符串
                if isinstance(item['authors'], list):
                    item['author'] = ', '.join(item['authors'])
                else:
                    item['author'] = item['authors']
        
        return item
    
    def _extract_publish_time(self, item: Dict[str, Any]) -> Optional[str]:
        """
        提取发布时间
        
        Args:
            item: 数据项
            
        Returns:
            发布时间字符串
        """
        # 优先使用已有字段
        time_fields = ['publish_time', 'published_date', 'date', 'created_at', 'time']
        for field in time_fields:
            if field in item and item[field]:
                return self._normalize_time(item[field])
        
        # 尝试从内容中提取时间
        if 'content' in item and item['content']:
            time_patterns = [
                r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
                r'(\d{4}年\d{1,2}月\d{1,2}日)',
                r'发布时间[：:]\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
            ]
            for pattern in time_patterns:
                match = re.search(pattern, item['content'])
                if match:
                    return self._normalize_time(match.group(1))
        
        return None
    
    def _normalize_time(self, time_str: Any) -> Optional[str]:
        """
        标准化时间格式
        
        Args:
            time_str: 时间字符串或datetime对象
            
        Returns:
            ISO格式时间字符串
        """
        if not time_str:
            return None
        
        # 如果是datetime对象
        if isinstance(time_str, datetime):
            return time_str.isoformat()
        
        # 如果是字符串，尝试解析
        time_str = str(time_str).strip()
        
        # 尝试解析常见格式
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%Y/%m/%d %H:%M:%S',
            '%Y/%m/%d',
            '%Y年%m月%d日',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f',
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(time_str, fmt)
                return dt.isoformat()
            except:
                continue
        
        # 如果无法解析，返回原字符串
        return time_str
    
    def _extract_source(self, item: Dict[str, Any]) -> Optional[str]:
        """
        提取来源
        
        Args:
            item: 数据项
            
        Returns:
            来源字符串
        """
        # 优先使用已有字段
        source_fields = ['source', 'origin', 'from', 'site', 'domain']
        for field in source_fields:
            if field in item and item[field]:
                return str(item[field])
        
        # 从URL提取域名作为来源
        if 'url' in item and item['url']:
            from urllib.parse import urlparse
            parsed = urlparse(item['url'])
            if parsed.netloc:
                return parsed.netloc
        
        return None
    
    def _label_sentiment(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        情感标签预标注
        
        Args:
            item: 数据项
            
        Returns:
            包含情感标签的数据项
        """
        # 合并文本内容
        text = ''
        if item.get('title'):
            text += item['title'] + ' '
        if item.get('content'):
            text += item['content']
        elif item.get('description'):
            text += item['description']
        
        if not text:
            item['sentiment'] = 'neutral'
            item['sentiment_score'] = 0.0
            return item
        
        # 统计情感关键词
        positive_count = sum(1 for keyword in self.positive_keywords if keyword in text)
        negative_count = sum(1 for keyword in self.negative_keywords if keyword in text)
        neutral_count = sum(1 for keyword in self.neutral_keywords if keyword in text)
        
        # 计算情感分数（-1 到 1）
        total_keywords = positive_count + negative_count + neutral_count
        if total_keywords > 0:
            sentiment_score = (positive_count - negative_count) / max(total_keywords, 1)
        else:
            sentiment_score = 0.0
        
        # 确定情感标签
        if sentiment_score > 0.2:
            sentiment = 'positive'
        elif sentiment_score < -0.2:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        item['sentiment'] = sentiment
        item['sentiment_score'] = round(sentiment_score, 3)
        item['sentiment_keywords'] = {
            'positive': positive_count,
            'negative': negative_count,
            'neutral': neutral_count
        }
        
        return item
    
    def _extract_entities(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        关键实体识别
        
        Args:
            item: 数据项
            
        Returns:
            包含实体信息的数据项
        """
        # 合并文本内容
        text = ''
        if item.get('title'):
            text += item['title'] + ' '
        if item.get('content'):
            text += item['content']
        elif item.get('description'):
            text += item['description']
        
        if not text:
            item['entities'] = {
                'companies': [],
                'technologies': [],
                'persons': []
            }
            return item
        
        # 使用 jieba 提取关键词
        if JIEBA_AVAILABLE:
            try:
                keywords = jieba.analyse.extract_tags(text, topK=20, withWeight=False)
            except Exception:
                # jieba 不可用时，使用简单的关键词提取
                keywords = self._simple_keyword_extract(text, topK=20)
        else:
            # jieba 不可用时，使用简单的关键词提取
            keywords = self._simple_keyword_extract(text, topK=20)
        
        # 分类实体（简化版，实际可以使用NER模型）
        entities = {
            'companies': [],
            'technologies': [],
            'persons': []
        }
        
        # 公司关键词模式
        company_patterns = [
            r'(.+公司)',
            r'(.+集团)',
            r'(.+科技)',
            r'(.+股份)',
            r'(.+有限)',
        ]
        
        # 技术关键词
        tech_keywords = [
            'AI', '人工智能', '机器学习', '深度学习', '神经网络', '自然语言处理',
            '计算机视觉', '大数据', '云计算', '区块链', '物联网', '5G', '6G',
            'Python', 'Java', 'JavaScript', 'Go', 'Rust', 'TensorFlow', 'PyTorch'
        ]
        
        # 人物关键词模式
        person_patterns = [
            r'(.+先生)',
            r'(.+女士)',
            r'(.+教授)',
            r'(.+博士)',
            r'(.+CEO)',
            r'(.+CTO)',
        ]
        
        # 提取公司
        for keyword in keywords:
            for pattern in company_patterns:
                if re.search(pattern, keyword):
                    if keyword not in entities['companies']:
                        entities['companies'].append(keyword)
                    break
        
        # 提取技术
        for keyword in keywords:
            if keyword in tech_keywords or any(tech in keyword for tech in tech_keywords):
                if keyword not in entities['technologies']:
                    entities['technologies'].append(keyword)
        
        # 提取人物（简化版）
        for keyword in keywords:
            for pattern in person_patterns:
                if re.search(pattern, keyword):
                    if keyword not in entities['persons']:
                        entities['persons'].append(keyword)
                    break
        
        item['entities'] = entities
        item['keywords'] = keywords[:10]  # 保留前10个关键词
        
        return item
    
    def _simple_keyword_extract(self, text: str, topK: int = 20) -> List[str]:
        """
        简单的关键词提取（jieba 不可用时的降级方案）
        
        Args:
            text: 文本内容
            topK: 返回前K个关键词
            
        Returns:
            关键词列表
        """
        if not text:
            return []
        
        # 简单的关键词提取：基于词频和长度
        # 移除标点符号和特殊字符
        text_clean = re.sub(r'[^\w\s]', ' ', text)
        words = text_clean.split()
        
        # 过滤短词和常见停用词
        stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
        words = [w for w in words if len(w) > 1 and w not in stop_words]
        
        # 统计词频
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # 按频率排序，返回前topK个
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        keywords = [word for word, freq in sorted_words[:topK]]
        
        return keywords

"""
提取器智能分析工具
自动分析网页结构，推荐最适合的提取器类型
"""
import re
import logging
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

try:
    from lxml import etree
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False
    logger.warning("lxml 未安装，XPath 分析功能将受限")


class ExtractorAnalyzer:
    """提取器分析器"""
    
    def analyze(self, html_content: str, url: Optional[str] = None) -> Dict[str, Any]:
        """
        分析网页内容，推荐最适合的提取器类型
        
        Args:
            html_content: HTML内容
            url: 网页URL（可选）
            
        Returns:
            分析结果，包含推荐的提取器类型和配置建议
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
        except Exception as e:
            logger.error(f"解析HTML失败: {e}")
            return {
                'recommended_type': 'css',
                'confidence': 0.5,
                'reason': 'HTML解析失败，使用默认CSS选择器',
                'suggestions': {}
            }
        
        # 分析网页特征
        features = self._analyze_features(soup, html_content)
        
        # 计算各提取器的适用性分数
        css_score = self._calculate_css_score(features)
        xpath_score = self._calculate_xpath_score(features)
        regex_score = self._calculate_regex_score(features)
        
        # 选择得分最高的提取器
        scores = {
            'css': css_score,
            'xpath': xpath_score,
            'regex': regex_score
        }
        
        recommended_type = max(scores, key=scores.get)
        max_score = scores[recommended_type]
        
        # 生成配置建议
        suggestions = self._generate_suggestions(soup, recommended_type, features)
        
        return {
            'recommended_type': recommended_type,
            'confidence': min(max_score / 100, 1.0),  # 归一化到0-1
            'scores': scores,
            'reason': self._get_reason(recommended_type, features),
            'suggestions': suggestions,
            'features': features
        }
    
    def _analyze_features(self, soup: BeautifulSoup, html_content: str) -> Dict[str, Any]:
        """分析网页特征"""
        features = {
            'has_structured_html': False,
            'has_semantic_tags': False,
            'has_class_ids': False,
            'has_repetitive_structure': False,
            'text_to_html_ratio': 0.0,
            'has_json_data': False,
            'has_common_patterns': False,
            'complexity': 'medium'
        }
        
        # 检查是否有结构化HTML
        if soup.find_all(['div', 'section', 'article', 'main']):
            features['has_structured_html'] = True
        
        # 检查是否有语义化标签
        semantic_tags = ['article', 'section', 'header', 'footer', 'nav', 'main', 'aside']
        if any(soup.find_all(tag) for tag in semantic_tags):
            features['has_semantic_tags'] = True
        
        # 检查是否有class或id属性
        elements_with_attrs = soup.find_all(attrs={'class': True}) + soup.find_all(attrs={'id': True})
        if len(elements_with_attrs) > 10:
            features['has_class_ids'] = True
        
        # 检查是否有重复结构（列表项）
        list_items = soup.find_all(['li', 'tr', 'dt', 'dd'])
        if len(list_items) > 5:
            features['has_repetitive_structure'] = True
        
        # 计算文本与HTML的比例
        text_length = len(soup.get_text())
        html_length = len(html_content)
        if html_length > 0:
            features['text_to_html_ratio'] = text_length / html_length
        
        # 检查是否有JSON数据
        if '<script' in html_content and ('json' in html_content.lower() or 'application/json' in html_content):
            features['has_json_data'] = True
        
        # 检查是否有常见的数据模式
        common_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # 日期
            r'https?://[^\s]+',     # URL
            r'[\w\.-]+@[\w\.-]+',  # 邮箱
        ]
        text = soup.get_text()
        if any(re.search(pattern, text) for pattern in common_patterns):
            features['has_common_patterns'] = True
        
        # 评估复杂度
        total_elements = len(soup.find_all())
        if total_elements < 50:
            features['complexity'] = 'simple'
        elif total_elements > 500:
            features['complexity'] = 'complex'
        
        return features
    
    def _calculate_css_score(self, features: Dict[str, Any]) -> float:
        """计算CSS选择器的适用性分数"""
        score = 50.0  # 基础分数
        
        if features['has_structured_html']:
            score += 20
        if features['has_class_ids']:
            score += 15
        if features['has_semantic_tags']:
            score += 10
        if features['has_repetitive_structure']:
            score += 10
        if features['text_to_html_ratio'] > 0.3:
            score += 5
        
        return min(score, 100.0)
    
    def _calculate_xpath_score(self, features: Dict[str, Any]) -> float:
        """计算XPath的适用性分数"""
        if not LXML_AVAILABLE:
            return 0.0
        
        score = 30.0  # 基础分数
        
        if features['has_structured_html']:
            score += 20
        if features['complexity'] == 'complex':
            score += 20
        if features['has_repetitive_structure']:
            score += 15
        if not features['has_class_ids']:
            # 如果没有class/id，XPath可能更适合
            score += 10
        if features['has_semantic_tags']:
            score += 5
        
        return min(score, 100.0)
    
    def _calculate_regex_score(self, features: Dict[str, Any]) -> float:
        """计算正则表达式的适用性分数"""
        score = 20.0  # 基础分数
        
        if features['text_to_html_ratio'] > 0.7:
            # 文本比例高，适合正则
            score += 30
        if features['has_common_patterns']:
            score += 25
        if not features['has_structured_html']:
            score += 15
        if features['complexity'] == 'simple':
            score += 10
        
        return min(score, 100.0)
    
    def _get_reason(self, extractor_type: str, features: Dict[str, Any]) -> str:
        """生成推荐理由"""
        reasons = {
            'css': [],
            'xpath': [],
            'regex': []
        }
        
        if features['has_class_ids']:
            reasons['css'].append('页面包含大量class/id属性')
        if features['has_structured_html']:
            reasons['css'].append('页面结构清晰')
        if features['has_repetitive_structure']:
            reasons['css'].append('存在重复的列表结构')
        
        if features['complexity'] == 'complex':
            reasons['xpath'].append('页面结构复杂')
        if not features['has_class_ids']:
            reasons['xpath'].append('缺少class/id属性，XPath更灵活')
        
        if features['text_to_html_ratio'] > 0.7:
            reasons['regex'].append('文本内容比例高')
        if features['has_common_patterns']:
            reasons['regex'].append('存在可识别的数据模式')
        
        reason_list = reasons.get(extractor_type, [])
        if reason_list:
            return '；'.join(reason_list)
        else:
            return f'推荐使用{extractor_type}提取器'
    
    def _generate_suggestions(self, soup: BeautifulSoup, extractor_type: str, features: Dict[str, Any]) -> Dict[str, Any]:
        """生成配置建议"""
        suggestions = {
            'container': None,
            'fields': {}
        }
        
        if extractor_type == 'css':
            # 寻找可能的容器
            containers = soup.find_all(['div', 'section', 'article', 'ul', 'ol', 'table'])
            if containers:
                # 选择最常见的容器类型
                container_types = {}
                for container in containers[:20]:  # 只检查前20个
                    tag = container.name
                    classes = ' '.join(container.get('class', []))
                    key = f"{tag}.{classes}" if classes else tag
                    container_types[key] = container_types.get(key, 0) + 1
                
                if container_types:
                    most_common = max(container_types, key=container_types.get)
                    tag, classes = most_common.split('.', 1) if '.' in most_common else (most_common, '')
                    if classes:
                        suggestions['container'] = f"{tag}.{classes.split()[0]}"
                    else:
                        suggestions['container'] = tag
            
            # 寻找标题
            title_elem = soup.find(['h1', 'h2', 'h3', 'title'])
            if title_elem:
                if title_elem.name == 'title':
                    suggestions['fields']['title'] = {'selector': 'title', 'attr': 'text'}
                else:
                    suggestions['fields']['title'] = {'selector': title_elem.name, 'attr': 'text'}
            
            # 寻找链接
            link_elem = soup.find('a', href=True)
            if link_elem:
                suggestions['fields']['url'] = {'selector': 'a', 'attr': 'href'}
            
            # 寻找内容
            content_elem = soup.find(['article', 'main', 'div'], class_=re.compile(r'content|body|text', re.I))
            if content_elem:
                classes = ' '.join(content_elem.get('class', []))
                if classes:
                    suggestions['fields']['content'] = {'selector': f"div.{classes.split()[0]}", 'attr': 'text'}
        
        elif extractor_type == 'xpath':
            suggestions['container'] = '//body'
            
            # 寻找标题
            title_elem = soup.find(['h1', 'h2', 'h3'])
            if title_elem:
                suggestions['fields']['title'] = {'xpath': f"//{title_elem.name}/text()", 'attr': 'text'}
            
            # 寻找链接
            if soup.find('a', href=True):
                suggestions['fields']['url'] = {'xpath': '//a/@href', 'attr': 'href'}
        
        elif extractor_type == 'regex':
            # 正则表达式建议
            text = soup.get_text()
            if '<title>' in str(soup):
                suggestions['fields']['title'] = {'pattern': '<title>(.+?)</title>'}
            if 'http' in text:
                suggestions['fields']['url'] = {'pattern': 'https?://[\\w\\.-]+/[\\w/]+'}
        
        return suggestions

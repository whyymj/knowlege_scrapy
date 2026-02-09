"""
翻译工具模块
支持自动检测语言并翻译成中文
"""
import re
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# 尝试导入语言检测库
try:
    from langdetect import detect, LangDetectException
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    logger.warning("langdetect 未安装，将使用简单的中文检测方法。安装: pip install langdetect")

# 尝试导入翻译库
try:
    from googletrans import Translator
    GOOGLETRANS_AVAILABLE = True
except ImportError:
    GOOGLETRANS_AVAILABLE = False
    logger.warning("googletrans 未安装，翻译功能将不可用。安装: pip install googletrans==4.0.0rc1")

# 尝试使用DeepSeek API进行翻译（如果可用）
try:
    import os
    from openai import OpenAI
    DEEPSEEK_AVAILABLE = False
    # 检查是否有DeepSeek API配置
    if os.getenv('DEEPSEEK_API_KEY'):
        DEEPSEEK_AVAILABLE = True
except:
    DEEPSEEK_AVAILABLE = False


def is_chinese_text(text: str) -> bool:
    """
    检测文本是否为中文
    
    Args:
        text: 待检测的文本
        
    Returns:
        如果是中文返回True，否则返回False
    """
    if not text or not isinstance(text, str):
        return False
    
    # 移除空白字符和标点符号
    text_clean = re.sub(r'[\s\W]', '', text)
    if not text_clean:
        return False
    
    # 统计中文字符数量
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text_clean))
    total_chars = len(text_clean)
    
    # 如果中文字符占比超过30%，认为是中文
    if total_chars > 0:
        chinese_ratio = chinese_chars / total_chars
        return chinese_ratio > 0.3
    
    return False


def detect_language(text: str) -> Optional[str]:
    """
    检测文本语言
    
    Args:
        text: 待检测的文本
        
    Returns:
        语言代码（如 'zh-cn', 'en', 'ja' 等），如果检测失败返回None
    """
    if not text or not isinstance(text, str):
        return None
    
    # 如果文本太短，使用简单的中文检测
    if len(text.strip()) < 10:
        return 'zh-cn' if is_chinese_text(text) else 'en'
    
    # 使用langdetect库检测
    if LANGDETECT_AVAILABLE:
        try:
            lang = detect(text)
            # langdetect返回的是ISO 639-1代码，需要转换为googletrans格式
            lang_map = {
                'zh': 'zh-cn',
                'zh-cn': 'zh-cn',
                'zh-tw': 'zh-tw',
                'en': 'en',
                'ja': 'ja',
                'ko': 'ko',
                'fr': 'fr',
                'de': 'de',
                'es': 'es',
                'ru': 'ru',
                'ar': 'ar',
                'pt': 'pt',
                'it': 'it',
                'nl': 'nl',
                'pl': 'pl',
                'vi': 'vi',
                'th': 'th',
            }
            return lang_map.get(lang, lang)
        except LangDetectException:
            pass
    
    # 回退到简单的中文检测
    return 'zh-cn' if is_chinese_text(text) else 'en'


def translate_text(text: str, target_lang: str = 'zh-cn', source_lang: Optional[str] = None) -> Optional[str]:
    """
    翻译文本
    
    Args:
        text: 待翻译的文本
        target_lang: 目标语言（默认中文）
        source_lang: 源语言（如果为None则自动检测）
        
    Returns:
        翻译后的文本，如果翻译失败返回None
    """
    if not text or not isinstance(text, str):
        return None
    
    # 如果文本太短，跳过翻译
    if len(text.strip()) < 3:
        return text
    
    # 如果已经是中文，直接返回
    if is_chinese_text(text):
        return text
    
    # 尝试使用googletrans翻译
    if GOOGLETRANS_AVAILABLE:
        try:
            translator = Translator()
            result = translator.translate(text, dest=target_lang, src=source_lang)
            if result and result.text:
                logger.info(f"翻译成功: {text[:50]}... -> {result.text[:50]}...")
                return result.text
        except Exception as e:
            logger.warning(f"googletrans翻译失败: {e}")
    
    # 尝试使用DeepSeek API翻译（如果配置了）
    if DEEPSEEK_AVAILABLE:
        try:
            client = OpenAI(
                api_key=os.getenv('DEEPSEEK_API_KEY'),
                base_url="https://api.deepseek.com"
            )
            
            prompt = f"请将以下文本翻译成中文，只返回翻译结果，不要添加任何解释：\n\n{text}"
            
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            translated = response.choices[0].message.content.strip()
            if translated:
                logger.info(f"DeepSeek翻译成功: {text[:50]}... -> {translated[:50]}...")
                return translated
        except Exception as e:
            logger.warning(f"DeepSeek翻译失败: {e}")
    
    # 如果所有翻译方法都失败，返回原文本
    logger.warning(f"翻译失败，返回原文本: {text[:50]}...")
    return text


def translate_item(item: Dict[str, Any], translate_title: bool = True, translate_content: bool = True) -> Dict[str, Any]:
    """
    翻译数据项
    
    Args:
        item: 数据项字典
        translate_title: 是否翻译标题
        translate_content: 是否翻译内容
        
    Returns:
        翻译后的数据项
    """
    translated_item = item.copy()
    
    # 翻译标题
    if translate_title and item.get('title'):
        title = item['title']
        if not is_chinese_text(title):
            translated_title = translate_text(title, target_lang='zh-cn')
            if translated_title:
                translated_item['title'] = translated_title
                # 保存原始标题到metadata
                if 'metadata' not in translated_item:
                    translated_item['metadata'] = {}
                if not isinstance(translated_item['metadata'], dict):
                    translated_item['metadata'] = {}
                translated_item['metadata']['original_title'] = title
                translated_item['metadata']['title_translated'] = True
    
    # 翻译内容
    if translate_content and item.get('content'):
        content = item['content']
        if not is_chinese_text(content):
            # 如果内容太长，分段翻译
            if len(content) > 5000:
                # 分段翻译
                chunks = [content[i:i+5000] for i in range(0, len(content), 5000)]
                translated_chunks = []
                for chunk in chunks:
                    translated_chunk = translate_text(chunk, target_lang='zh-cn')
                    if translated_chunk:
                        translated_chunks.append(translated_chunk)
                    else:
                        translated_chunks.append(chunk)
                translated_content = '\n\n'.join(translated_chunks)
            else:
                translated_content = translate_text(content, target_lang='zh-cn')
            
            if translated_content and translated_content != content:
                translated_item['content'] = translated_content
                # 保存原始内容到metadata
                if 'metadata' not in translated_item:
                    translated_item['metadata'] = {}
                if not isinstance(translated_item['metadata'], dict):
                    translated_item['metadata'] = {}
                translated_item['metadata']['original_content'] = content[:1000]  # 只保存前1000字符
                translated_item['metadata']['content_translated'] = True
    
    # 翻译description（如果存在）
    if item.get('description'):
        description = item['description']
        if not is_chinese_text(description):
            translated_desc = translate_text(description, target_lang='zh-cn')
            if translated_desc:
                translated_item['description'] = translated_desc
                if 'metadata' not in translated_item:
                    translated_item['metadata'] = {}
                if not isinstance(translated_item['metadata'], dict):
                    translated_item['metadata'] = {}
                translated_item['metadata']['original_description'] = description
                translated_item['metadata']['description_translated'] = True
    
    return translated_item

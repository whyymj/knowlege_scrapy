#!/usr/bin/env python3
"""
测试ArXiv页面提取功能
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
from components.adapters import HttpAdapter
from components.parsers import HtmlParser
from components.extractors import CssExtractor

async def test_arxiv_extraction():
    """测试ArXiv页面提取"""
    url = "https://arxiv.org/list/cs.AI/recent"
    
    print(f"测试URL: {url}")
    print("=" * 60)
    
    # 1. 获取页面
    print("\n1. 获取页面...")
    adapter = HttpAdapter({})
    request = {'url': url, 'method': 'GET'}
    page = await adapter.fetch(request)
    print(f"状态码: {page.get('status')}")
    print(f"内容长度: {len(page.get('content', ''))}")
    
    # 2. 解析HTML
    print("\n2. 解析HTML...")
    parser = HtmlParser({})
    parsed = await parser.parse(page)
    print(f"解析成功，soup对象: {parsed.get('soup') is not None}")
    
    # 3. 提取数据
    print("\n3. 提取数据...")
    extractor = CssExtractor({})
    fields = {
        'container': 'dt',  # 使用dt作为容器，触发ArXiv特殊处理
        'fields': {
            'title': {'selector': 'span.list-title', 'attr': 'text'},
            'content': {'selector': 'span.list-authors, span.list-subjects', 'attr': 'text'},
            'url': {'selector': 'a[href*="arxiv"], a[href*="abs"]', 'attr': 'href'},
        }
    }
    
    items = await extractor.extract(parsed, fields)
    print(f"提取到 {len(items)} 条数据")
    
    # 4. 显示前5条数据
    print("\n4. 前5条数据预览:")
    for i, item in enumerate(items[:5], 1):
        print(f"\n条目 {i}:")
        print(f"  标题: {item.get('title', 'N/A')[:100]}")
        print(f"  URL: {item.get('url', 'N/A')}")
        print(f"  内容: {item.get('content', 'N/A')[:100]}")
    
    return items

if __name__ == '__main__':
    items = asyncio.run(test_arxiv_extraction())
    print(f"\n总共提取到 {len(items)} 条数据")

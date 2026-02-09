"""
DeepSeek 分析器测试示例
"""
import sys
import os
import asyncio

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from analyzer import DeepSeekAnalyzer


def test_technical_trend():
    """测试技术趋势分析"""
    print("=" * 50)
    print("测试技术趋势分析")
    print("=" * 50)
    
    try:
        analyzer = DeepSeekAnalyzer()
        
        content = """
        OpenAI发布了GPT-4 Turbo模型，性能大幅提升。
        该模型支持更长的上下文，推理能力更强。
        预计将对AI应用产生重大影响。
        """
        
        print("\n分析内容:")
        print(content)
        print("\n正在分析...")
        
        result = analyzer.analyze('technical_trend', content)
        
        if result.get('success'):
            data = result['data']
            print(f"\n分析结果:")
            print(f"  技术: {data.get('technologies', [])}")
            print(f"  影响程度: {data.get('impact_level')}")
            print(f"  时间线: {data.get('timeline')}")
            print(f"  关键点: {data.get('key_points', [])[:3]}")
            print(f"  总结: {data.get('summary', '')[:100]}")
        else:
            print(f"\n分析失败: {result.get('error')}")
            
    except ValueError as e:
        print(f"\n配置错误: {e}")
        print("提示: 请设置 DEEPSEEK_API_KEY 环境变量或在 config.json 中配置")


def test_market_sentiment():
    """测试市场情绪分析"""
    print("\n" + "=" * 50)
    print("测试市场情绪分析")
    print("=" * 50)
    
    try:
        analyzer = DeepSeekAnalyzer()
        
        content = """
        苹果公司发布最新财报，营收超预期。
        但iPhone销量下滑，引发市场担忧。
        分析师认为需要关注后续表现。
        """
        
        print("\n分析内容:")
        print(content)
        print("\n正在分析...")
        
        result = analyzer.analyze('market_sentiment', content)
        
        if result.get('success'):
            data = result['data']
            print(f"\n分析结果:")
            print(f"  情绪分数: {data.get('sentiment_score')}")
            print(f"  情绪标签: {data.get('sentiment_label')}")
            print(f"  关键事件: {data.get('key_events', [])}")
            print(f"  风险因素: {data.get('risk_factors', [])}")
            print(f"  机会: {data.get('opportunities', [])}")
        else:
            print(f"\n分析失败: {result.get('error')}")
            
    except ValueError as e:
        print(f"\n配置错误: {e}")


def test_batch_analysis():
    """测试批量分析"""
    print("\n" + "=" * 50)
    print("测试批量分析")
    print("=" * 50)
    
    try:
        analyzer = DeepSeekAnalyzer()
        
        items = [
            {
                'title': 'AI技术突破',
                'content': '深度学习技术在图像识别领域取得重大进展',
                'url': 'https://example.com/1'
            },
            {
                'title': 'AI技术突破',
                'content': '深度学习技术在图像识别领域取得重大进展',  # 相似内容
                'url': 'https://example.com/2'
            },
            {
                'title': '市场分析',
                'content': '科技股整体上涨，AI概念股表现突出',
                'url': 'https://example.com/3'
            }
        ]
        
        print(f"\n批量分析 {len(items)} 条数据...")
        print("（相似内容将合并分析）")
        
        results = analyzer.analyze_batch('technical_trend', items, merge_similar=True)
        
        print(f"\n分析完成，共 {len(results)} 条结果")
        for i, result in enumerate(results[:3], 1):
            if result.get('success'):
                print(f"\n结果 {i}:")
                print(f"  技术: {result['data'].get('technologies', [])[:3]}")
            else:
                print(f"\n结果 {i}: 失败 - {result.get('error')}")
                
    except ValueError as e:
        print(f"\n配置错误: {e}")


async def test_async_analysis():
    """测试异步分析"""
    print("\n" + "=" * 50)
    print("测试异步分析")
    print("=" * 50)
    
    try:
        analyzer = DeepSeekAnalyzer()
        
        contents = [
            'AI技术在自然语言处理领域取得突破',
            '机器学习模型性能大幅提升',
            '计算机视觉应用广泛落地'
        ]
        
        print(f"\n异步分析 {len(contents)} 条内容...")
        
        tasks = [analyzer.analyze_async('technical_trend', content) for content in contents]
        results = await asyncio.gather(*tasks)
        
        print(f"\n分析完成，共 {len(results)} 条结果")
        for i, result in enumerate(results, 1):
            if result.get('success'):
                print(f"  结果 {i}: {len(result['data'].get('technologies', []))} 项技术")
            else:
                print(f"  结果 {i}: 失败")
                
    except ValueError as e:
        print(f"\n配置错误: {e}")


def test_cache():
    """测试缓存功能"""
    print("\n" + "=" * 50)
    print("测试缓存功能")
    print("=" * 50)
    
    try:
        analyzer = DeepSeekAnalyzer()
        
        content = "这是一段测试内容"
        
        print("\n第一次分析（无缓存）...")
        import time
        start = time.time()
        result1 = analyzer.analyze('technical_trend', content)
        time1 = time.time() - start
        
        print(f"耗时: {time1:.2f}秒")
        print(f"缓存: {result1.get('cached', False)}")
        
        print("\n第二次分析（使用缓存）...")
        start = time.time()
        result2 = analyzer.analyze('technical_trend', content)
        time2 = time.time() - start
        
        print(f"耗时: {time2:.2f}秒")
        print(f"缓存: {result2.get('cached', False)}")
        
        # 缓存统计
        stats = analyzer.get_cache_stats()
        print(f"\n缓存统计: {stats}")
        
    except ValueError as e:
        print(f"\n配置错误: {e}")


if __name__ == '__main__':
    # 同步测试
    test_technical_trend()
    test_market_sentiment()
    test_batch_analysis()
    test_cache()
    
    # 异步测试
    print("\n" + "=" * 50)
    print("运行异步测试")
    print("=" * 50)
    asyncio.run(test_async_analysis())

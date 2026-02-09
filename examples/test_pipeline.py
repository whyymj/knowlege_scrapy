"""
数据处理管道测试示例
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pipeline import DataNormalizer, DataQualityMonitor, DataProcessor


def test_normalizer():
    """测试数据标准化"""
    print("=" * 50)
    print("测试数据标准化")
    print("=" * 50)
    
    normalizer = DataNormalizer()
    
    # 测试数据
    test_item = {
        'url': 'https://example.com/article/123',
        'title': '<h1>AI技术突破</h1>',
        'content': '<p>这是一篇关于<strong>人工智能</strong>的文章。内容包含HTML标签。</p>',
        'description': 'AI技术的最新进展',
        'publish_time': '2024-01-15 10:30:00',
        'author': '张三'
    }
    
    print("\n原始数据:")
    print(f"标题: {test_item['title']}")
    print(f"内容: {test_item['content'][:50]}...")
    
    # 标准化
    normalized = normalizer.normalize(test_item)
    
    print("\n标准化后:")
    print(f"标题: {normalized['title']}")
    print(f"内容: {normalized['content'][:50]}...")
    print(f"情感: {normalized.get('sentiment')} (分数: {normalized.get('sentiment_score')})")
    print(f"实体: {normalized.get('entities')}")
    print(f"关键词: {normalized.get('keywords', [])[:5]}")


def test_quality_monitor():
    """测试数据质量监控"""
    print("\n" + "=" * 50)
    print("测试数据质量监控")
    print("=" * 50)
    
    monitor = DataQualityMonitor()
    
    # 测试数据
    test_items = [
        {
            'url': 'https://example.com/1',
            'title': 'AI技术突破',
            'content': '这是一篇关于人工智能技术的文章，内容详细介绍了最新的AI研究成果。',
            'publish_time': '2024-01-15T10:30:00',
            'source': 'example.com'
        },
        {
            'url': 'https://example.com/2',
            'title': 'A',  # 标题过短
            'content': '',  # 内容为空
            'publish_time': '2010-01-01',  # 过期数据
        },
        {
            'url': 'https://example.com/3',
            'title': '正常标题',
            'content': '正常内容' * 20,  # 内容足够
            'publish_time': '2024-12-01T10:30:00',  # 未来时间
        }
    ]
    
    for i, item in enumerate(test_items, 1):
        print(f"\n测试数据 {i}:")
        passed, report = monitor.check(item)
        print(f"  通过: {'是' if passed else '否'}")
        print(f"  总体分数: {report.get('overall_score', 0):.1f}")
        if report.get('issues'):
            print(f"  问题: {report['issues']}")


def test_processor():
    """测试数据处理管道"""
    print("\n" + "=" * 50)
    print("测试数据处理管道")
    print("=" * 50)
    
    processor = DataProcessor()
    
    # 测试数据
    test_item = {
        'url': 'https://example.com/article/123',
        'title': '<h1>AI技术重大突破</h1>',
        'content': '<p>人工智能技术在<strong>深度学习</strong>领域取得了重大进展。这项技术将推动行业发展。</p>',
        'description': 'AI技术的最新突破',
        'publish_time': '2024-01-15 10:30:00',
        'source': 'example.com'
    }
    
    print("\n处理数据...")
    processed_item, quality_report = processor.process(test_item)
    
    print(f"\n处理结果:")
    print(f"标题: {processed_item['title']}")
    print(f"情感: {processed_item.get('sentiment')} (分数: {processed_item.get('sentiment_score')})")
    print(f"质量分数: {processed_item.get('quality_score', 0):.1f}")
    print(f"质量通过: {processed_item.get('quality_passed', False)}")
    
    if quality_report:
        print(f"\n质量报告:")
        print(f"  完整性: {quality_report['checks']['completeness']['score']:.1f}")
        print(f"  时效性: {quality_report['checks']['timeliness']['score']:.1f}")
        print(f"  异常检测: {quality_report['checks']['anomalies']['score']:.1f}")


if __name__ == '__main__':
    test_normalizer()
    test_quality_monitor()
    test_processor()

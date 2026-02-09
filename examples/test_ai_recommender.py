#!/usr/bin/env python3
"""
AI推荐功能测试示例
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ai_recommender.service import AIRecommendationService


def test_topic_recommendation():
    """测试主题推荐"""
    print("=" * 60)
    print("测试主题推荐功能")
    print("=" * 60)
    
    # 模拟文章数据
    articles = [
        {
            'id': '1',
            'title': 'AI技术在医疗领域的应用',
            'content': '人工智能技术在医疗诊断、药物研发等方面展现出巨大潜力...',
            'url': 'https://example.com/article1'
        },
        {
            'id': '2',
            'title': '深度学习算法优化研究',
            'content': '最新的深度学习算法在图像识别和自然语言处理方面取得突破...',
            'url': 'https://example.com/article2'
        },
        {
            'id': '3',
            'title': '区块链技术在金融行业的应用',
            'content': '区块链技术为金融行业带来透明度和安全性...',
            'url': 'https://example.com/article3'
        }
    ]
    
    try:
        service = AIRecommendationService()
        
        print("\n获取主题推荐...")
        result = service.get_topic_recommendations(articles, num_topics=3)
        
        print(f"\n推荐的主题:")
        for i, rec in enumerate(result.get('recommendations', []), 1):
            print(f"\n{i}. {rec['topic']}")
            print(f"   分类: {rec.get('category', 'N/A')}")
            print(f"   理由: {rec.get('reason', 'N/A')}")
            print(f"   相关文章数: {rec.get('article_count', 0)}")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_article_analysis():
    """测试文章分析"""
    print("\n" + "=" * 60)
    print("测试文章分析功能")
    print("=" * 60)
    
    article = {
        'id': '1',
        'title': 'AI技术在医疗领域的应用',
        'content': '''
        人工智能技术在医疗领域的应用正在快速发展。通过机器学习算法，
        医生可以更准确地诊断疾病，特别是在医学影像分析方面。
        此外，AI还可以帮助药物研发，大大缩短新药上市时间。
        然而，我们也需要关注AI医疗的伦理问题和数据隐私保护。
        '''
    }
    
    try:
        service = AIRecommendationService()
        
        print("\n分析文章...")
        result = service.analyze_article(article)
        
        print(f"\n分析结果:")
        print(f"摘要: {result.get('summary', 'N/A')}")
        print(f"\n关键要点:")
        for point in result.get('key_points', []):
            print(f"  - {point}")
        print(f"\n情感倾向: {result.get('sentiment', 'N/A')}")
        print(f"\n关键实体: {', '.join(result.get('entities', []))}")
        print(f"\n标签: {', '.join(result.get('tags', []))}")
        print(f"\n阅读时间: {result.get('analysis', {}).get('read_time', 0)} 分钟")
        print(f"复杂度: {result.get('analysis', {}).get('complexity', 'N/A')}")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_manual_selection():
    """测试手动选择功能"""
    print("\n" + "=" * 60)
    print("测试手动选择功能")
    print("=" * 60)
    
    try:
        service = AIRecommendationService()
        user_id = 'test_user_001'
        
        # 选择主题
        print("\n手动选择主题...")
        topics = ['AI技术', '医疗应用']
        articles = [
            {'id': '1', 'title': 'AI医疗应用', 'content': '...'},
            {'id': '2', 'title': 'AI诊断技术', 'content': '...'}
        ]
        
        selection = service.manual_select_topics(user_id, topics, articles)
        print(f"选择ID: {selection.get('id')}")
        print(f"选择的主题: {selection.get('topics')}")
        
        # 选择文章
        print("\n手动选择文章...")
        article_selection = service.manual_select_articles(
            user_id, 
            ['1', '2'],
            reason='这些文章与我的研究相关'
        )
        print(f"选择ID: {article_selection.get('id')}")
        print(f"选择的文章ID: {article_selection.get('article_ids')}")
        
        # 获取用户选择记录
        print("\n获取用户选择记录...")
        user_selections = service.get_user_selections(user_id)
        print(f"总选择数: {user_selections.get('stats', {}).get('total_selections', 0)}")
        print(f"主题选择: {user_selections.get('stats', {}).get('topic_selections', 0)}")
        print(f"文章选择: {user_selections.get('stats', {}).get('article_selections', 0)}")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_recommendation_pipeline():
    """测试完整推荐流程"""
    print("\n" + "=" * 60)
    print("测试完整推荐流程")
    print("=" * 60)
    
    articles = [
        {
            'id': '1',
            'title': 'AI技术在医疗领域的应用',
            'content': '人工智能技术在医疗诊断、药物研发等方面展现出巨大潜力...'
        },
        {
            'id': '2',
            'title': '深度学习算法优化研究',
            'content': '最新的深度学习算法在图像识别和自然语言处理方面取得突破...'
        }
    ]
    
    try:
        service = AIRecommendationService()
        
        print("\n执行完整推荐流程...")
        result = service.get_recommendation_pipeline(articles, user_id='test_user_001')
        
        print(f"\n主题推荐数: {len(result.get('topic_recommendations', {}).get('topics', []))}")
        print(f"文章分析数: {len(result.get('article_analyses', []))}")
        print(f"总文章数: {result.get('total_articles', 0)}")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    print("AI推荐功能测试")
    print("=" * 60)
    print("\n注意: 需要配置OpenAI API Key才能运行")
    print("设置环境变量: export OPENAI_API_KEY='your-api-key'")
    print("或在config.json中配置: ai_recommender.api_key")
    print("=" * 60)
    
    # 检查API Key
    import os
    api_key = os.getenv('OPENAI_API_KEY', '')
    if not api_key:
        print("\n⚠ 警告: 未检测到OPENAI_API_KEY环境变量")
        print("部分功能可能无法正常工作")
    
    # 运行测试
    test_topic_recommendation()
    test_article_analysis()
    test_manual_selection()
    test_recommendation_pipeline()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

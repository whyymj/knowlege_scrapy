#!/usr/bin/env python3
"""
AI推荐功能自动化测试用例
"""
import sys
import os
import requests
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

BASE_URL = "http://localhost:6000"


def test_topic_recommendation():
    """测试主题推荐接口"""
    print("=" * 60)
    print("测试主题推荐接口")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/ai/recommend/topics"
    
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
    
    data = {
        'articles': articles,
        'num_topics': 3
    }
    
    try:
        response = requests.post(url, json=data, timeout=30)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            if result.get('code') == 200:
                recommendations = result.get('data', {}).get('recommendations', [])
                print(f"\n✓ 推荐了 {len(recommendations)} 个主题")
                return True
            else:
                print(f"✗ 接口返回错误: {result.get('message')}")
                return False
        else:
            print(f"✗ HTTP错误: {response.status_code}")
            print(f"响应: {response.text[:500]}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ 连接失败: 后端服务未运行")
        return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False


def test_article_analysis():
    """测试文章分析接口"""
    print("\n" + "=" * 60)
    print("测试文章分析接口")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/ai/analyze/article"
    
    article = {
        'id': '1',
        'title': 'AI技术在医疗领域的应用',
        'content': '''
        人工智能技术在医疗领域的应用正在快速发展。通过机器学习算法，
        医生可以更准确地诊断疾病，特别是在医学影像分析方面。
        此外，AI还可以帮助药物研发，大大缩短新药上市时间。
        '''
    }
    
    data = {'article': article}
    
    try:
        response = requests.post(url, json=data, timeout=30)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            if result.get('code') == 200:
                analysis = result.get('data', {})
                print(f"\n✓ 文章分析完成")
                print(f"  摘要: {analysis.get('summary', 'N/A')[:100]}...")
                print(f"  关键要点数: {len(analysis.get('key_points', []))}")
                return True
            else:
                print(f"✗ 接口返回错误: {result.get('message')}")
                return False
        else:
            print(f"✗ HTTP错误: {response.status_code}")
            print(f"响应: {response.text[:500]}")
            return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False


def test_manual_selection():
    """测试手动选择接口"""
    print("\n" + "=" * 60)
    print("测试手动选择接口")
    print("=" * 60)
    
    user_id = 'test_user_001'
    
    # 测试选择主题
    url = f"{BASE_URL}/api/ai/select/topics"
    data = {
        'user_id': user_id,
        'topics': ['AI技术', '医疗应用'],
        'articles': [
            {'id': '1', 'title': 'AI医疗', 'content': '...'}
        ]
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"选择主题 - 状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 200:
                print(f"✓ 主题选择成功")
                selection_id = result.get('data', {}).get('id')
                
                # 获取用户选择记录
                url_selections = f"{BASE_URL}/api/ai/selections/{user_id}"
                response2 = requests.get(url_selections, timeout=10)
                
                if response2.status_code == 200:
                    result2 = response2.json()
                    print(f"✓ 获取选择记录成功")
                    print(f"  总选择数: {result2.get('data', {}).get('stats', {}).get('total_selections', 0)}")
                    return True
        
        print(f"✗ 选择失败")
        return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False


def test_recommendation_pipeline():
    """测试完整推荐流程"""
    print("\n" + "=" * 60)
    print("测试完整推荐流程")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/ai/recommend/pipeline"
    
    articles = [
        {
            'id': '1',
            'title': 'AI技术应用',
            'content': '人工智能技术在各个领域都有广泛应用...'
        },
        {
            'id': '2',
            'title': '机器学习算法',
            'content': '机器学习算法不断优化，性能不断提升...'
        }
    ]
    
    data = {
        'articles': articles,
        'user_id': 'test_user_001'
    }
    
    try:
        response = requests.post(url, json=data, timeout=60)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 200:
                data_result = result.get('data', {})
                print(f"✓ 推荐流程完成")
                print(f"  主题推荐数: {len(data_result.get('topic_recommendations', {}).get('topics', []))}")
                print(f"  文章分析数: {len(data_result.get('article_analyses', []))}")
                return True
            else:
                print(f"✗ 接口返回错误: {result.get('message')}")
                return False
        else:
            print(f"✗ HTTP错误: {response.status_code}")
            print(f"响应: {response.text[:500]}")
            return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("AI推荐功能自动化测试")
    print("=" * 60)
    print(f"测试目标: {BASE_URL}")
    print("\n注意: 需要配置OpenAI API Key才能正常运行")
    print("设置环境变量: export OPENAI_API_KEY='your-api-key'")
    print("或在config.json中配置: ai_recommender.api_key")
    print("=" * 60)
    
    # 检查后端服务
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=2)
        if response.status_code != 200:
            print(f"\n⚠ 警告: 后端服务返回非200状态码: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"\n✗ 错误: 无法连接到后端服务 {BASE_URL}")
        print("请先启动后端服务: cd backend && python app.py")
        return 1
    
    results = []
    
    # 执行测试
    print("\n开始执行测试用例...")
    
    results.append(("主题推荐", test_topic_recommendation()))
    results.append(("文章分析", test_article_analysis()))
    results.append(("手动选择", test_manual_selection()))
    results.append(("推荐流程", test_recommendation_pipeline()))
    
    # 打印总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"总测试数: {total}")
    print(f"通过: {passed}")
    print(f"失败: {total - passed}")
    
    if passed < total:
        print("\n失败的测试:")
        for name, result in results:
            if not result:
                print(f"  ✗ {name}")
    
    print("=" * 60)
    
    return 0 if passed == total else 1


if __name__ == '__main__':
    sys.exit(main())

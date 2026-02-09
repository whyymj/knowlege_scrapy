"""
通用抓取引擎测试示例
"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from engine import CrawlerEngine


async def test_simple_crawler():
    """测试简单爬虫任务"""
    print("=" * 60)
    print("测试通用抓取引擎 - 简单爬虫任务")
    print("=" * 60)
    
    # 创建引擎
    engine = CrawlerEngine()
    
    # 任务配置
    task_config = {
        'id': 'test_task_1',
        'source': {
            'type': 'http',
            'urls': ['https://httpbin.org/html']
        },
        'parser': {
            'type': 'html'
        },
        'extractor': {
            'type': 'css',
            'fields': {
                'container': 'body',
                'fields': {
                    'title': {
                        'selector': 'h1',
                        'attr': 'text'
                    }
                }
            }
        },
        'transformer': {
            'pipeline': [
                {'type': 'data'}
            ]
        },
        'validator': {
            'pipeline': [
                {'type': 'data', 'required_fields': ['title']}
            ]
        },
        'output': {
            'type': 'file',
            'file': 'output/test_output.json',
            'format': 'json'
        }
    }
    
    try:
        with engine:
            result = await engine.run_task(task_config)
            print(f"\n任务完成:")
            print(f"  任务ID: {result['task_id']}")
            print(f"  提取数据: {result['items_count']} 条")
            print(f"  错误数: {result['errors_count']}")
            
            if result['items']:
                print(f"\n提取的数据示例:")
                for item in result['items'][:3]:
                    print(f"  {item}")
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


async def test_api_crawler():
    """测试API爬虫任务"""
    print("\n" + "=" * 60)
    print("测试通用抓取引擎 - API爬虫任务")
    print("=" * 60)
    
    engine = CrawlerEngine()
    
    task_config = {
        'id': 'test_api_task',
        'source': {
            'type': 'api',
            'api_url': 'https://httpbin.org/json',
            'method': 'GET'
        },
        'parser': {
            'type': 'json'
        },
        'extractor': {
            'type': 'regex',
            'fields': {
                'fields': {
                    'title': {
                        'pattern': r'"slideshow":\s*\{[^}]*"title":\s*"([^"]+)"'
                    }
                }
            }
        },
        'transformer': {
            'pipeline': [
                {'type': 'data'}
            ]
        },
        'output': {
            'type': 'file',
            'file': 'output/test_api_output.json',
            'format': 'json'
        }
    }
    
    try:
        with engine:
            result = await engine.run_task(task_config)
            print(f"\n任务完成:")
            print(f"  任务ID: {result['task_id']}")
            print(f"  提取数据: {result['items_count']} 条")
    except Exception as e:
        print(f"测试失败: {e}")


async def test_batch_tasks():
    """测试批量任务"""
    print("\n" + "=" * 60)
    print("测试通用抓取引擎 - 批量任务")
    print("=" * 60)
    
    engine = CrawlerEngine()
    
    tasks_config = [
        {
            'id': f'task_{i}',
            'source': {
                'type': 'http',
                'urls': [f'https://httpbin.org/get?page={i}']
            },
            'parser': {'type': 'json'},
            'extractor': {
                'type': 'regex',
                'fields': {
                    'fields': {
                        'page': {'pattern': r'"page":\s*"(\d+)"'}
                    }
                }
            },
            'transformer': {'pipeline': [{'type': 'data'}]},
            'output': {
                'type': 'file',
                'file': 'output/test_batch_output.json',
                'format': 'json'
            }
        }
        for i in range(3)
    ]
    
    try:
        with engine:
            results = await engine.run_tasks(tasks_config)
            print(f"\n批量任务完成:")
            print(f"  总任务数: {len(results)}")
            for result in results:
                if isinstance(result, Exception):
                    print(f"  任务失败: {result}")
                else:
                    print(f"  任务 {result['task_id']}: {result['items_count']} 条数据")
    except Exception as e:
        print(f"测试失败: {e}")


if __name__ == '__main__':
    # 创建输出目录
    os.makedirs('output', exist_ok=True)
    
    # 运行测试
    asyncio.run(test_simple_crawler())
    asyncio.run(test_api_crawler())
    asyncio.run(test_batch_tasks())

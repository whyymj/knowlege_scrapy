#!/usr/bin/env python3
"""
API接口自动化测试用例
"""
import sys
import os
import requests
import json
import time
from typing import Dict, Any, Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

BASE_URL = "http://localhost:6000"
TIMEOUT = 10


class APITester:
    """API测试器"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.results = []
    
    def test(self, name: str, method: str, endpoint: str, 
             params: Optional[Dict] = None, 
             data: Optional[Dict] = None,
             expected_status: int = 200,
             expected_code: Optional[int] = None,
             validator: Optional[callable] = None) -> bool:
        """
        执行测试
        
        Args:
            name: 测试名称
            method: HTTP方法
            endpoint: API端点
            params: URL参数
            data: 请求体数据
            expected_status: 期望的HTTP状态码
            expected_code: 期望的响应code字段
            validator: 自定义验证函数
            
        Returns:
            是否通过
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            print(f"\n{'='*60}")
            print(f"测试: {name}")
            print(f"{'='*60}")
            print(f"请求: {method} {url}")
            if params:
                print(f"参数: {params}")
            if data:
                print(f"数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            # 发送请求
            if method.upper() == 'GET':
                response = requests.get(url, params=params, timeout=TIMEOUT)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, params=params, timeout=TIMEOUT)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, timeout=TIMEOUT)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            print(f"状态码: {response.status_code}")
            
            # 检查HTTP状态码
            if response.status_code != expected_status:
                print(f"✗ HTTP状态码不匹配: 期望 {expected_status}, 实际 {response.status_code}")
                print(f"响应内容: {response.text[:500]}")
                self.results.append({
                    'name': name,
                    'passed': False,
                    'error': f"HTTP状态码不匹配: {response.status_code}"
                })
                return False
            
            # 解析响应
            try:
                response_data = response.json()
                print(f"响应: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
            except:
                print(f"✗ 响应不是有效的JSON")
                print(f"响应内容: {response.text[:500]}")
                self.results.append({
                    'name': name,
                    'passed': False,
                    'error': "响应不是有效的JSON"
                })
                return False
            
            # 检查响应code字段
            if expected_code is not None:
                actual_code = response_data.get('code')
                if actual_code != expected_code:
                    print(f"✗ 响应code不匹配: 期望 {expected_code}, 实际 {actual_code}")
                    print(f"错误消息: {response_data.get('message', '')}")
                    self.results.append({
                        'name': name,
                        'passed': False,
                        'error': f"响应code不匹配: {actual_code}"
                    })
                    return False
            
            # 自定义验证
            if validator:
                try:
                    if not validator(response_data):
                        print(f"✗ 自定义验证失败")
                        self.results.append({
                            'name': name,
                            'passed': False,
                            'error': "自定义验证失败"
                        })
                        return False
                except Exception as e:
                    print(f"✗ 验证函数执行失败: {e}")
                    self.results.append({
                        'name': name,
                        'passed': False,
                        'error': f"验证函数执行失败: {e}"
                    })
                    return False
            
            print(f"✓ 测试通过")
            self.results.append({
                'name': name,
                'passed': True
            })
            return True
            
        except requests.exceptions.ConnectionError:
            print(f"✗ 连接失败: 无法连接到 {self.base_url}")
            print("请确保后端服务正在运行: cd backend && python app.py")
            self.results.append({
                'name': name,
                'passed': False,
                'error': "连接失败"
            })
            return False
        except Exception as e:
            print(f"✗ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            self.results.append({
                'name': name,
                'passed': False,
                'error': str(e)
            })
            return False
    
    def print_summary(self):
        """打印测试总结"""
        print(f"\n{'='*60}")
        print("测试总结")
        print(f"{'='*60}")
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r['passed'])
        failed = total - passed
        
        print(f"总测试数: {total}")
        print(f"通过: {passed}")
        print(f"失败: {failed}")
        
        if failed > 0:
            print(f"\n失败的测试:")
            for result in self.results:
                if not result['passed']:
                    print(f"  ✗ {result['name']}: {result.get('error', '未知错误')}")
        
        print(f"{'='*60}")
        
        return failed == 0


def test_health_check(tester: APITester):
    """测试健康检查接口"""
    def validator(data: Dict) -> bool:
        return data.get('status') == 'ok' or data.get('code') == 200
    
    return tester.test(
        name="健康检查",
        method="GET",
        endpoint="/api/health",
        expected_status=200,
        validator=validator
    )


def test_websites_list(tester: APITester):
    """测试网站列表接口"""
    def validator(data: Dict) -> bool:
        if data.get('code') != 200:
            return False
        result_data = data.get('data', {})
        required_keys = ['list', 'total', 'page', 'page_size', 'total_pages']
        return all(key in result_data for key in required_keys)
    
    return tester.test(
        name="获取网站列表",
        method="GET",
        endpoint="/api/websites",
        params={
            'page': 1,
            'page_size': 10,
            'keyword': '',
            'domain': ''
        },
        expected_status=200,
        expected_code=200,
        validator=validator
    )


def test_websites_with_keyword(tester: APITester):
    """测试带关键词的网站列表接口"""
    return tester.test(
        name="搜索网站（关键词）",
        method="GET",
        endpoint="/api/websites",
        params={
            'page': 1,
            'page_size': 10,
            'keyword': 'test',
            'domain': ''
        },
        expected_status=200,
        expected_code=200
    )


def test_statistics(tester: APITester):
    """测试统计接口"""
    def validator(data: Dict) -> bool:
        if data.get('code') != 200:
            return False
        result_data = data.get('data', {})
        return 'total' in result_data or 'task_stats' in result_data
    
    return tester.test(
        name="获取统计信息",
        method="GET",
        endpoint="/api/statistics",
        expected_status=200,
        expected_code=200,
        validator=validator
    )


def test_tasks_list(tester: APITester):
    """测试任务列表接口"""
    return tester.test(
        name="获取任务列表",
        method="GET",
        endpoint="/api/tasks",
        params={'page': 1, 'per_page': 10},
        expected_status=200,
        expected_code=200
    )


def test_create_task(tester: APITester):
    """测试创建任务接口"""
    task_config = {
        'id': f'test_task_{int(time.time())}',
        'name': '测试任务',
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
                    'title': {'selector': 'h1', 'attr': 'text'}
                }
            }
        },
        'transformer': {
            'pipeline': [{'type': 'data'}]
        },
        'output': {
            'type': 'file',
            'file': 'output/test_output.json',
            'format': 'json'
        }
    }
    
    def validator(data: Dict) -> bool:
        if data.get('code') != 200:
            return False
        return 'task_id' in data.get('data', {})
    
    return tester.test(
        name="创建抓取任务",
        method="POST",
        endpoint="/api/tasks",
        data=task_config,
        expected_status=200,
        expected_code=200,
        validator=validator
    )


def main():
    """主测试函数"""
    print("="*60)
    print("API接口自动化测试")
    print("="*60)
    print(f"测试目标: {BASE_URL}")
    print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查后端服务是否运行
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=2)
        if response.status_code != 200:
            print(f"\n⚠ 警告: 后端服务返回非200状态码: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"\n✗ 错误: 无法连接到后端服务 {BASE_URL}")
        print("请先启动后端服务:")
        print("  cd backend && python app.py")
        return 1
    except Exception as e:
        print(f"\n⚠ 警告: 检查后端服务时出错: {e}")
    
    # 创建测试器
    tester = APITester()
    
    # 执行测试
    print(f"\n开始执行测试用例...")
    
    # 基础接口测试
    test_health_check(tester)
    test_statistics(tester)
    
    # 网站列表接口测试
    test_websites_list(tester)
    test_websites_with_keyword(tester)
    
    # 任务管理接口测试
    test_tasks_list(tester)
    # test_create_task(tester)  # 可选：创建任务测试（可能需要较长时间）
    
    # 打印总结
    all_passed = tester.print_summary()
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())

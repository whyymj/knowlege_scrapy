#!/usr/bin/env python3
"""
测试任务失败情况
"""
import sys
import os
import requests
import json
import time
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

BASE_URL = 'http://localhost:6000/api'

class TestTaskFailure:
    """测试任务失败情况"""
    
    def __init__(self):
        """初始化"""
        self.task_id = "task_1770615448"
        self.base_url = BASE_URL
        self.results = []
    
    def _log_result(self, test_name, passed, message=""):
        """记录测试结果"""
        status = "✓ PASS" if passed else "✗ FAIL"
        self.results.append({
            'name': test_name,
            'passed': passed,
            'message': message
        })
        print(f"{status}: {test_name}")
        if message:
            print(f"      {message}")
    
    def test_get_failed_task_details(self):
        """测试获取失败任务的详情"""
        try:
            # 获取任务详情
            response = requests.get(f"{self.base_url}/tasks/{self.task_id}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data['code'] == 200:
                    task = data['data']
                    print(f"\n任务ID: {task.get('task_id')}")
                    print(f"任务名称: {task.get('task_name')}")
                    print(f"状态: {task.get('status')}")
                    print(f"错误数: {task.get('errors_count', 0)}")
                    print(f"数据条数: {task.get('items_count', 0)}")
                    print(f"开始时间: {task.get('started_at')}")
                    print(f"完成时间: {task.get('completed_at')}")
                    
                    # 验证失败任务的状态
                    passed = True
                    message = ""
                    if task.get('status') == 'failed':
                        if task.get('errors_count', 0) == 0:
                            passed = False
                            message = "失败任务应该有错误数"
                        if task.get('completed_at') is None:
                            passed = False
                            message = "失败任务应该有完成时间"
                    else:
                        message = f"任务状态为: {task.get('status')}，不是失败状态"
                    
                    self._log_result("获取失败任务详情", passed, message)
                    return passed
                else:
                    self._log_result("获取失败任务详情", False, f"API返回错误: {data.get('message')}")
                    return False
            elif response.status_code == 404:
                self._log_result("获取失败任务详情", False, f"任务 {self.task_id} 不存在（404）")
                return False
            else:
                self._log_result("获取失败任务详情", False, f"HTTP状态码: {response.status_code}")
                return False
        except Exception as e:
            self._log_result("获取失败任务详情", False, f"异常: {str(e)}")
            return False
    
    def test_get_failed_task_logs(self):
        """测试获取失败任务的日志"""
        try:
            # 获取任务日志
            response = requests.get(f"{self.base_url}/tasks/{self.task_id}/logs", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data['code'] == 200:
                    logs = data['data'] or []
                    print(f"\n任务日志数量: {len(logs)}")
                    
                    # 显示错误日志
                    error_logs = [log for log in logs if log.get('level') == 'ERROR']
                    print(f"错误日志数量: {len(error_logs)}")
                    
                    if error_logs:
                        print("\n错误日志详情:")
                        for log in error_logs[:5]:  # 只显示前5条
                            print(f"  [{log.get('stage')}] {log.get('message')}")
                            if log.get('error_message'):
                                print(f"    错误: {log.get('error_message')[:200]}")
                    
                    # 验证失败任务应该有错误日志
                    passed = True
                    message = ""
                    if len(logs) > 0 and len(error_logs) == 0:
                        passed = False
                        message = "失败任务应该有错误日志"
                    
                    self._log_result("获取失败任务日志", passed, message)
                    return passed
                else:
                    self._log_result("获取失败任务日志", False, f"API返回错误: {data.get('message')}")
                    return False
            elif response.status_code == 404:
                self._log_result("获取失败任务日志", False, f"任务 {self.task_id} 不存在（404）")
                return False
            else:
                self._log_result("获取失败任务日志", False, f"HTTP状态码: {response.status_code}")
                return False
        except Exception as e:
            self._log_result("获取失败任务日志", False, f"异常: {str(e)}")
            return False
    
    def test_get_failed_task_data(self):
        """测试获取失败任务的数据（可能为空）"""
        try:
            # 获取任务数据
            response = requests.get(f"{self.base_url}/tasks/{self.task_id}/data", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data['code'] == 200:
                    result = data['data']
                    items = result.get('list', [])
                    total = result.get('total', 0)
                    
                    print(f"\n任务数据条数: {total}")
                    
                    # 失败任务可能没有数据或数据很少
                    if items:
                        print(f"前3条数据:")
                        for item in items[:3]:
                            print(f"  - {item.get('title', 'N/A')[:50]}")
                    else:
                        print("  无数据（任务可能失败或未开始）")
                    
                    self._log_result("获取失败任务数据", True, f"数据总数: {total}")
                    return True
                else:
                    self._log_result("获取失败任务数据", False, f"API返回错误: {data.get('message')}")
                    return False
            elif response.status_code == 404:
                self._log_result("获取失败任务数据", False, f"任务 {self.task_id} 不存在（404）")
                return False
            else:
                self._log_result("获取失败任务数据", False, f"HTTP状态码: {response.status_code}")
                return False
        except Exception as e:
            self._log_result("获取失败任务数据", False, f"异常: {str(e)}")
            return False
    
    def test_task_failure_scenarios(self):
        """测试各种任务失败场景"""
        print("\n=== 测试任务失败场景 ===")
        
        # 场景1: 无效的URL
        print("\n1. 测试无效URL任务...")
        try:
            invalid_url_config = {
                "name": "测试无效URL",
                "source": {
                    "type": "http",
                    "urls": ["https://invalid-url-that-does-not-exist-12345.com"]
                },
                "parser": {"type": "html"},
                "extractor": {
                    "type": "css",
                    "fields": {
                        "container": "body",
                        "fields": {
                            "title": {"selector": "title", "attr": "text"}
                        }
                    }
                },
                "transformer": {"pipeline": [{"type": "data"}]},
                "output": {"type": "database", "output_type": "mysql"}
            }
            
            response = requests.post(f"{self.base_url}/tasks", json=invalid_url_config, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data['code'] == 200:
                    test_task_id = data['data']['task_id']
                    print(f"  创建任务: {test_task_id}")
                    
                    # 等待任务执行（最多等待10秒）
                    for i in range(10):
                        time.sleep(1)
                        task_response = requests.get(f"{self.base_url}/tasks/{test_task_id}", timeout=5)
                        if task_response.status_code == 200:
                            task_data = task_response.json()
                            if task_data['code'] == 200:
                                task = task_data['data']
                                status = task.get('status')
                                print(f"  任务状态: {status}")
                                if status in ['completed', 'failed']:
                                    break
                    
                    # 检查任务状态
                    task_response = requests.get(f"{self.base_url}/tasks/{test_task_id}", timeout=5)
                    if task_response.status_code == 200:
                        task_data = task_response.json()
                        if task_data['code'] == 200:
                            task = task_data['data']
                            print(f"  最终状态: {task.get('status')}")
                            print(f"  错误数: {task.get('errors_count', 0)}")
                            
                            # 获取错误日志
                            logs_response = requests.get(f"{self.base_url}/tasks/{test_task_id}/logs", timeout=5)
                            if logs_response.status_code == 200:
                                logs_data = logs_response.json()
                                if logs_data['code'] == 200:
                                    logs = logs_data['data'] or []
                                    error_logs = [log for log in logs if log.get('level') == 'ERROR']
                                    if error_logs:
                                        print(f"  错误日志: {error_logs[0].get('message', '')[:100]}")
                    
                    self._log_result("测试无效URL任务", True, f"任务ID: {test_task_id}")
                    return True
                else:
                    self._log_result("测试无效URL任务", False, f"创建任务失败: {data.get('message')}")
                    return False
            else:
                self._log_result("测试无效URL任务", False, f"HTTP状态码: {response.status_code}")
                return False
        except Exception as e:
            self._log_result("测试无效URL任务", False, f"异常: {str(e)}")
            return False
    
    def test_task_error_handling(self):
        """测试任务错误处理"""
        print("\n=== 测试任务错误处理 ===")
        results = []
        
        # 测试空配置
        print("\n1. 测试空配置...")
        try:
            response = requests.post(f"{self.base_url}/tasks", json={}, timeout=10)
            if response.status_code == 400:
                results.append(("测试空配置", True, "正确返回400错误"))
            else:
                results.append(("测试空配置", False, f"期望400，实际{response.status_code}"))
        except Exception as e:
            results.append(("测试空配置", False, f"异常: {str(e)}"))
        
        # 测试缺少必要字段
        print("\n2. 测试缺少必要字段...")
        try:
            incomplete_config = {
                "name": "测试任务"
                # 缺少source等必要字段
            }
            response = requests.post(f"{self.base_url}/tasks", json=incomplete_config, timeout=10)
            print(f"  响应状态: {response.status_code}")
            results.append(("测试缺少必要字段", True, f"响应状态: {response.status_code}"))
        except Exception as e:
            results.append(("测试缺少必要字段", False, f"异常: {str(e)}"))
        
        # 测试无效的提取器配置
        print("\n3. 测试无效提取器配置...")
        try:
            invalid_extractor_config = {
                "name": "测试无效提取器",
                "source": {
                    "type": "http",
                    "urls": ["https://www.example.com"]
                },
                "parser": {"type": "html"},
                "extractor": {
                    "type": "invalid_extractor_type",  # 无效的提取器类型
                    "fields": {}
                },
                "transformer": {"pipeline": [{"type": "data"}]},
                "output": {"type": "database", "output_type": "mysql"}
            }
            
            response = requests.post(f"{self.base_url}/tasks", json=invalid_extractor_config, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data['code'] == 200:
                    test_task_id = data['data']['task_id']
                    print(f"  创建任务: {test_task_id}")
                    
                    # 等待任务执行
                    time.sleep(5)
                    
                    # 检查任务状态
                    task_response = requests.get(f"{self.base_url}/tasks/{test_task_id}", timeout=5)
                    if task_response.status_code == 200:
                        task_data = task_response.json()
                        if task_data['code'] == 200:
                            task = task_data['data']
                            print(f"  任务状态: {task.get('status')}")
                            if task.get('status') == 'failed':
                                print(f"  任务失败，错误数: {task.get('errors_count', 0)}")
                                results.append(("测试无效提取器配置", True, f"任务失败，错误数: {task.get('errors_count', 0)}"))
                            else:
                                results.append(("测试无效提取器配置", False, f"任务状态: {task.get('status')}"))
            else:
                results.append(("测试无效提取器配置", False, f"HTTP状态码: {response.status_code}"))
        except Exception as e:
            results.append(("测试无效提取器配置", False, f"异常: {str(e)}"))
        
        # 记录所有结果
        for name, passed, msg in results:
            self._log_result(name, passed, msg)
        
        return all(r[1] for r in results)
    
    def test_failed_task_recovery(self):
        """测试失败任务的恢复机制"""
        print("\n=== 测试失败任务恢复 ===")
        
        try:
            # 获取失败任务详情
            response = requests.get(f"{self.base_url}/tasks/{self.task_id}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data['code'] == 200:
                    task = data['data']
                    
                    if task.get('status') == 'failed':
                        print(f"\n失败任务: {task.get('task_id')}")
                        print(f"任务配置: {json.dumps(task.get('task_config', {}), indent=2, ensure_ascii=False)[:500]}")
                        
                        # 验证失败任务的关键信息
                        passed = True
                        message = ""
                        
                        if 'task_config' not in task:
                            passed = False
                            message = "失败任务应该有配置信息"
                        if task.get('errors_count', 0) == 0:
                            passed = False
                            message = "失败任务应该有错误计数"
                        if task.get('completed_at') is None:
                            passed = False
                            message = "失败任务应该有完成时间"
                        
                        if passed:
                            print("\n✓ 失败任务信息完整")
                        
                        self._log_result("测试失败任务恢复", passed, message)
                        return passed
                    else:
                        message = f"任务状态为: {task.get('status')}，不是失败状态"
                        print(f"\n{message}")
                        self._log_result("测试失败任务恢复", False, message)
                        return False
                else:
                    self._log_result("测试失败任务恢复", False, f"API返回错误: {data.get('message')}")
                    return False
            else:
                self._log_result("测试失败任务恢复", False, f"HTTP状态码: {response.status_code}")
                return False
        except Exception as e:
            self._log_result("测试失败任务恢复", False, f"异常: {str(e)}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("="*60)
        print("任务失败情况测试套件")
        print("="*60)
        print(f"测试任务ID: {self.task_id}")
        print(f"API地址: {self.base_url}")
        print("="*60)
        
        # 运行所有测试
        self.test_get_failed_task_details()
        self.test_get_failed_task_logs()
        self.test_get_failed_task_data()
        self.test_failed_task_recovery()
        # test_task_failure_scenarios()  # 可选：创建新任务测试
        
        # 打印总结
        print("\n" + "="*60)
        print("测试总结")
        print("="*60)
        passed = sum(1 for r in self.results if r['passed'])
        total = len(self.results)
        print(f"通过: {passed}/{total}")
        print(f"失败: {total - passed}/{total}")
        
        if total - passed > 0:
            print("\n失败的测试:")
            for r in self.results:
                if not r['passed']:
                    print(f"  - {r['name']}: {r['message']}")
        
        return passed == total


def test_specific_task_failure():
    """测试特定任务ID的失败情况"""
    task_id = "task_1770615448"
    base_url = BASE_URL
    
    print(f"\n{'='*60}")
    print(f"测试任务失败情况: {task_id}")
    print(f"{'='*60}")
    
    # 1. 获取任务详情
    print("\n1. 获取任务详情...")
    response = requests.get(f"{base_url}/tasks/{task_id}")
    
    if response.status_code == 200:
        data = response.json()
        if data['code'] == 200:
            task = data['data']
            print(f"  任务名称: {task.get('task_name')}")
            print(f"  状态: {task.get('status')}")
            print(f"  数据条数: {task.get('items_count', 0)}")
            print(f"  错误数: {task.get('errors_count', 0)}")
            print(f"  开始时间: {task.get('started_at')}")
            print(f"  完成时间: {task.get('completed_at')}")
            
            # 2. 获取任务日志
            print("\n2. 获取任务日志...")
            logs_response = requests.get(f"{base_url}/tasks/{task_id}/logs")
            if logs_response.status_code == 200:
                logs_data = logs_response.json()
                if logs_data['code'] == 200:
                    logs = logs_data['data'] or []
                    print(f"  日志总数: {len(logs)}")
                    
                    # 显示错误日志
                    error_logs = [log for log in logs if log.get('level') == 'ERROR']
                    print(f"  错误日志数: {len(error_logs)}")
                    
                    if error_logs:
                        print("\n  错误日志详情:")
                        for i, log in enumerate(error_logs[:5], 1):
                            print(f"\n  [{i}] {log.get('stage')} - {log.get('level')}")
                            print(f"      消息: {log.get('message', '')[:200]}")
                            if log.get('error_message'):
                                print(f"      错误: {log.get('error_message')[:200]}")
            
            # 3. 获取任务数据
            print("\n3. 获取任务数据...")
            data_response = requests.get(f"{base_url}/tasks/{task_id}/data")
            if data_response.status_code == 200:
                data_data = data_response.json()
                if data_data['code'] == 200:
                    result = data_data['data']
                    print(f"  数据总数: {result.get('total', 0)}")
                    items = result.get('list', [])
                    if items:
                        print(f"  前3条数据:")
                        for item in items[:3]:
                            print(f"    - {item.get('title', 'N/A')[:60]}")
                    else:
                        print("  无数据")
            
            # 4. 分析失败原因
            print("\n4. 失败原因分析...")
            if task.get('status') == 'failed':
                print("  ✓ 任务状态确认为失败")
                if task.get('errors_count', 0) > 0:
                    print(f"  ✓ 错误计数: {task.get('errors_count')}")
                else:
                    print("  ⚠ 错误计数为0，可能任务配置有问题")
                
                # 检查任务配置
                task_config = task.get('task_config', {})
                if task_config:
                    source_config = task_config.get('source', {})
                    urls = source_config.get('urls', [])
                    print(f"  ✓ 配置的URL数量: {len(urls)}")
                    if urls:
                        print(f"  ✓ 第一个URL: {urls[0][:80]}")
                    
                    # 检查提取器配置
                    extractor_config = task_config.get('extractor', {})
                    extractor_type = extractor_config.get('type', 'unknown')
                    print(f"  ✓ 提取器类型: {extractor_type}")
                    
                    # 检查执行时间
                    started_at = task.get('started_at')
                    completed_at = task.get('completed_at')
                    if started_at and completed_at:
                        try:
                            from datetime import datetime
                            # 处理不同的时间格式
                            if isinstance(started_at, str):
                                start = datetime.fromisoformat(started_at.replace('Z', '+00:00').replace('+00:00', ''))
                            else:
                                start = started_at
                            
                            if isinstance(completed_at, str):
                                end = datetime.fromisoformat(completed_at.replace('Z', '+00:00').replace('+00:00', ''))
                            else:
                                end = completed_at
                            
                            duration = (end - start).total_seconds()
                            print(f"  ✓ 执行时长: {duration:.2f}秒")
                            
                            # 如果执行时间很短（<1秒），可能是立即失败
                            if duration < 1:
                                print("  ⚠ 任务执行时间很短，可能是配置错误或立即失败")
                        except Exception as e:
                            print(f"  ⚠ 无法计算执行时长: {e}")
            else:
                print(f"  ⚠ 任务状态为: {task.get('status')}，不是失败状态")
    else:
        print(f"\n✗ 任务 {task_id} 不存在（404）")
        print("  可能原因：")
        print("    1. 任务ID不正确")
        print("    2. 任务已被删除")
        print("    3. 数据库连接问题")


if __name__ == '__main__':
    # 检查后端服务
    try:
        response = requests.get(f"{BASE_URL.replace('/api', '')}/api/health", timeout=2)
        if response.status_code != 200:
            print(f"⚠ 警告: 后端服务返回非200状态码: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"✗ 错误: 无法连接到后端服务 {BASE_URL.replace('/api', '')}")
        print("请先启动后端服务:")
        print("  cd backend && python3 app.py")
        sys.exit(1)
    except Exception as e:
        print(f"⚠ 警告: 检查后端服务时出错: {e}")
    
    # 运行特定任务测试
    test_specific_task_failure()
    
    # 运行测试套件
    print("\n" + "="*60)
    print("运行测试套件...")
    print("="*60)
    
    tester = TestTaskFailure()
    all_passed = tester.run_all_tests()
    
    sys.exit(0 if all_passed else 1)

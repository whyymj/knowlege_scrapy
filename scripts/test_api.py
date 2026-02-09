#!/usr/bin/env python3
"""
测试API接口
"""
import requests
import json

BASE_URL = "http://localhost:6000"

def test_websites_api():
    """测试 /api/websites 接口"""
    print("=" * 60)
    print("测试 /api/websites 接口")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/websites"
    params = {
        'page': 1,
        'page_size': 10,
        'keyword': '',
        'domain': ''
    }
    
    try:
        print(f"\n请求URL: {url}")
        print(f"参数: {params}")
        
        response = requests.get(url, params=params, timeout=10)
        
        print(f"\n状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n响应数据:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            if data.get('code') == 200:
                result_data = data.get('data', {})
                print(f"\n✓ 接口调用成功")
                print(f"  总记录数: {result_data.get('total', 0)}")
                print(f"  当前页: {result_data.get('page', 1)}")
                print(f"  每页数量: {result_data.get('page_size', 10)}")
                print(f"  数据列表长度: {len(result_data.get('list', []))}")
                return True
            else:
                print(f"\n✗ 接口返回错误: {data.get('message')}")
                return False
        else:
            print(f"\n✗ HTTP错误: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"\n✗ 连接失败: 无法连接到 {BASE_URL}")
        print("请确保后端服务正在运行: cd backend && python app.py")
        return False
    except Exception as e:
        print(f"\n✗ 请求失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_health_api():
    """测试健康检查接口"""
    print("\n" + "=" * 60)
    print("测试 /api/health 接口")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/health"
    
    try:
        response = requests.get(url, timeout=5)
        print(f"\n状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
            print("✓ 健康检查通过")
            return True
        else:
            print(f"✗ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 健康检查失败: {e}")
        return False

def test_statistics_api():
    """测试统计接口"""
    print("\n" + "=" * 60)
    print("测试 /api/statistics 接口")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/statistics"
    
    try:
        response = requests.get(url, timeout=5)
        print(f"\n状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
            print("✓ 统计接口正常")
            return True
        else:
            print(f"✗ 统计接口失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 统计接口失败: {e}")
        return False

if __name__ == '__main__':
    import sys
    
    print("API接口测试工具")
    print("=" * 60)
    
    # 测试健康检查
    health_ok = test_health_api()
    
    if not health_ok:
        print("\n⚠ 后端服务可能未启动，请先启动后端:")
        print("  cd backend && python app.py")
        sys.exit(1)
    
    # 测试统计接口
    test_statistics_api()
    
    # 测试网站列表接口
    success = test_websites_api()
    
    if success:
        print("\n" + "=" * 60)
        print("✓ 所有测试通过！")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("✗ 测试失败")
        print("=" * 60)
        sys.exit(1)

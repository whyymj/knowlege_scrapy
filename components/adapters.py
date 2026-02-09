"""
源适配器实现
"""
import aiohttp
import asyncio
import logging
from typing import Dict, List, Any
from .base import BaseAdapter

logger = logging.getLogger(__name__)

# 尝试导入 brotli，如果未安装则会在运行时提示
try:
    import brotli
    BROTLI_AVAILABLE = True
except ImportError:
    BROTLI_AVAILABLE = False


class HttpAdapter(BaseAdapter):
    """HTTP源适配器"""
    
    async def generate_requests(self, task_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成HTTP请求"""
        source_config = task_config.get('source', {})
        urls = source_config.get('urls', [])
        
        requests = []
        for url in urls:
            requests.append({
                'url': url,
                'method': source_config.get('method', 'GET'),
                'headers': source_config.get('headers', {}),
                'params': source_config.get('params', {}),
                'data': source_config.get('data')
            })
        
        return requests
    
    async def fetch(self, request: Dict[str, Any], max_retries: int = 3) -> Dict[str, Any]:
        """
        获取HTTP页面（带重试机制）
        
        Args:
            request: 请求配置字典
            max_retries: 最大重试次数，默认3次
        
        Returns:
            响应数据字典
        """
        # 从请求配置中获取超时时间，默认60秒
        timeout_seconds = request.get('timeout', 60)
        
        # 设置默认请求头，模拟浏览器访问
        # 注意：如果未安装 brotli，Accept-Encoding 中不应包含 'br'
        accept_encoding = 'gzip, deflate'
        if BROTLI_AVAILABLE:
            accept_encoding += ', br'
        
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': accept_encoding,
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # 合并用户自定义请求头
        headers = {**default_headers, **request.get('headers', {})}
        
        url = request['url']
        last_error = None
        
        # 重试循环
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        method=request.get('method', 'GET'),
                        url=url,
                        headers=headers,
                        params=request.get('params'),
                        data=request.get('data'),
                        timeout=aiohttp.ClientTimeout(
                            total=timeout_seconds,
                            connect=10,  # 连接超时10秒
                            sock_read=timeout_seconds  # 读取超时
                        ),
                        allow_redirects=True  # 允许重定向
                    ) as response:
                        # 检查HTTP状态码
                        if response.status >= 400:
                            error_text = await response.text()
                            raise Exception(f"HTTP {response.status} 错误: {error_text[:200]}")
                        
                        content = await response.text()
                        
                        if attempt > 0:
                            logger.info(f"请求成功（第{attempt + 1}次尝试）: {url}")
                        
                        return {
                            'url': url,
                            'status': response.status,
                            'headers': dict(response.headers),
                            'content': content,
                            'content_type': response.content_type
                        }
            except asyncio.TimeoutError as e:
                last_error = f"请求超时（{timeout_seconds}秒）"
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # 递增等待时间：2秒、4秒、6秒
                    logger.warning(f"请求超时（第{attempt + 1}次尝试）: {url}, {wait_time}秒后重试...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"请求超时（已重试{max_retries}次）: {url}")
            except aiohttp.ClientError as e:
                error_msg = str(e)
                last_error = f"网络错误: {error_msg}"
                # 检查是否是 Brotli 解码错误
                if 'brotli' in error_msg.lower() or 'br' in error_msg.lower():
                    raise Exception(
                        f"HTTP请求失败: {url}, 需要安装 Brotli 库来解码压缩内容。"
                        f"请运行: pip install brotli"
                    )
                # 对于某些客户端错误，不重试（如404、403等）
                if hasattr(e, 'status') and e.status in [400, 401, 403, 404]:
                    raise Exception(f"HTTP请求失败: {url}, {last_error}")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    logger.warning(f"网络错误（第{attempt + 1}次尝试）: {url}, {wait_time}秒后重试...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"网络错误（已重试{max_retries}次）: {url}")
            except Exception as e:
                error_msg = str(e)
                last_error = f"错误: {error_msg}"
                # 检查是否是 Brotli 解码错误
                if 'brotli' in error_msg.lower() or 'br' in error_msg.lower():
                    raise Exception(
                        f"HTTP请求失败: {url}, 需要安装 Brotli 库来解码压缩内容。"
                        f"请运行: pip install brotli"
                    )
                # HTTP状态码错误不重试
                if 'HTTP' in error_msg and any(code in error_msg for code in ['400', '401', '403', '404']):
                    raise Exception(f"HTTP请求失败: {url}, {last_error}")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    logger.warning(f"请求失败（第{attempt + 1}次尝试）: {url}, {wait_time}秒后重试...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"请求失败（已重试{max_retries}次）: {url}")
        
        # 所有重试都失败
        raise Exception(f"HTTP请求失败: {url}, {last_error}（已重试{max_retries}次）")


class ApiAdapter(BaseAdapter):
    """API源适配器"""
    
    async def generate_requests(self, task_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成API请求"""
        source_config = task_config.get('source', {})
        api_url = source_config.get('api_url')
        
        if not api_url:
            raise ValueError("API URL未配置")
        
        # 支持分页
        requests = []
        page = source_config.get('start_page', 1)
        max_pages = source_config.get('max_pages', 1)
        
        while page <= max_pages:
            requests.append({
                'url': api_url,
                'method': source_config.get('method', 'GET'),
                'headers': source_config.get('headers', {}),
                'params': {**source_config.get('params', {}), 'page': page}
            })
            page += 1
        
        return requests
    
    async def fetch(self, request: Dict[str, Any], max_retries: int = 3) -> Dict[str, Any]:
        """
        获取API数据（带重试机制）
        
        Args:
            request: 请求配置字典
            max_retries: 最大重试次数，默认3次
        
        Returns:
            响应数据字典
        """
        # 从请求配置中获取超时时间，默认60秒
        timeout_seconds = request.get('timeout', 60)
        url = request['url']
        last_error = None
        
        # 重试循环
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        method=request.get('method', 'GET'),
                        url=url,
                        headers=request.get('headers', {}),
                        params=request.get('params'),
                        timeout=aiohttp.ClientTimeout(
                            total=timeout_seconds,
                            connect=10,
                            sock_read=timeout_seconds
                        )
                    ) as response:
                        if response.content_type == 'application/json':
                            data = await response.json()
                        else:
                            data = await response.text()
                        
                        if attempt > 0:
                            logger.info(f"API请求成功（第{attempt + 1}次尝试）: {url}")
                        
                        return {
                            'url': url,
                            'status': response.status,
                            'data': data,
                            'content_type': response.content_type
                        }
            except asyncio.TimeoutError as e:
                last_error = f"请求超时（{timeout_seconds}秒）"
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    logger.warning(f"API请求超时（第{attempt + 1}次尝试）: {url}, {wait_time}秒后重试...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"API请求超时（已重试{max_retries}次）: {url}")
            except Exception as e:
                error_msg = str(e)
                last_error = f"错误: {error_msg}"
                # HTTP状态码错误不重试
                if 'HTTP' in error_msg and any(code in error_msg for code in ['400', '401', '403', '404']):
                    raise Exception(f"API请求失败: {url}, {last_error}")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    logger.warning(f"API请求失败（第{attempt + 1}次尝试）: {url}, {wait_time}秒后重试...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"API请求失败（已重试{max_retries}次）: {url}")
        
        # 所有重试都失败
        raise Exception(f"API请求失败: {url}, {last_error}（已重试{max_retries}次）")

"""
中国专利查新模块
==============
优先查询国家知识产权局·中国专利公布公告系统。
当国知局接口异常或无结果时，自动降级到 Web 搜索。

核心类：
- CNPatentSearch：中国专利检索类

数据源：
1. 主：国知局专利公布公告（http://epub.cnipa.gov.cn）
2. 备：SerpAPI / Google CSE 网页搜索

注意：
- 国知局官网接口可能随政策调整，需定期检查更新
- 所有返回数据必须真实，不可虚构
"""

import os
import logging
import requests
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode, quote

logger = logging.getLogger(__name__)

class CNPatentSearch:
    """
    中国专利检索类
    
    优先使用国知局官方接口，失败时降级到网页搜索。
    """
    
    def __init__(self, config, serpapi_key: Optional[str] = None, 
                 google_cse_key: Optional[str] = None, google_cse_id: Optional[str] = None):
        """
        初始化中国专利检索器
        
        参数：
            config: RetrievalConfig 配置对象
            serpapi_key: SerpAPI 密钥（可选）
            google_cse_key: Google CSE 密钥（可选）
            google_cse_id: Google CSE ID（可选）
        """
        self.config = config
        self.cn_patent_base = config.cn_patent_base
        self.timeout = config.timeout
        self.serpapi_key = serpapi_key or os.getenv(config.serpapi_key_env, "")
        self.google_cse_key = google_cse_key or os.getenv(config.google_cse_key_env, "")
        self.google_cse_id = google_cse_id or os.getenv(config.google_cse_id_env, "")

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        执行中国专利检索（含降级逻辑）
        
        策略：
        1. 首先调用国知局专利公布公告接口
        2. 若异常或无结果，降级到 Web 搜索
        3. 所有结果标注来源，确保可追溯
        
        参数：
            query: 检索关键词
            limit: 最大返回条数
        
        返回：
            List[Dict]: 专利信息列表，每条包含 title/abstract/patent_number/source
        """
        # 第一步：尝试国知局官方接口
        logger.info(f"正在查询国知局专利公布公告：{query}")
        cn_results = self._search_cnipa(query, limit)
        
        if cn_results:
            logger.info(f"国知局查询成功，返回 {len(cn_results)} 条")
            return cn_results
        
        # 第二步：降级到 Web 搜索
        logger.warning("国知局查询无结果或异常，降级到 Web 搜索...")
        web_results = self._search_web_fallback(query, limit)
        return web_results

    def _search_cnipa(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        查询国知局专利公布公告系统
        
        参数：
            query: 检索关键词
            limit: 最大返回条数
        
        返回：
            List[Dict]: 专利信息列表，为空则说明无结果或异常
        """
        try:
            # 国知局专利检索 API 端点（实际接口可能需要根据官网调整）
            # 这里使用常见的检索接口格式，实际部署时可能需要更新
            search_url = f"{self.cn_patent_base}/Advanced/Search"
            
            # 构造请求参数
            params = {
                "searchStr": query,
                "pageSize": limit,
                "pageNum": 1,
            }
            
            # 发送请求
            resp = requests.get(search_url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            
            # 解析响应（国知局返回 HTML 或 JSON，需要根据实际格式解析）
            # 这里以 JSON 格式为例，实际需根据接口文档调整
            try:
                data = resp.json()
                records = data.get("records", [])
            except ValueError:
                # 非 JSON 响应，尝试解析 HTML
                records = self._parse_html_records(resp.text)
            
            # 格式化结果
            results = []
            for rec in records[:limit]:
                results.append({
                    "title": rec.get("patent_name", rec.get("title", "")),
                    "abstract": rec.get("abstract", ""),
                    "patent_number": rec.get("patent_number", ""),
                    "date": rec.get("publication_date", ""),
                    "applicant": rec.get("applicant", ""),
                    "source": "国知局·专利公布公告"
                })
            return results
            
        except Exception as e:
            logger.error(f"国知局查询异常: {e}")
            return []

    def _parse_html_records(self, html: str) -> List[Dict[str, Any]]:
        """
        解析国知局返回的 HTML 页面（备用解析方式）
        
        参数：
            html: HTML 页面内容
        
        返回：
            List[Dict]: 提取的专利记录
        """
        # 使用正则或 BeautifulSoup 提取专利信息
        # 这里提供简化版本，实际使用时需根据国知局页面结构调整
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            records = []
            # 查找专利列表项（选择器需根据实际页面调整）
            for item in soup.select('.patent-item'):
                title = item.select_one('.title').get_text(strip=True)
                num = item.select_one('.number').get_text(strip=True)
                records.append({"title": title, "patent_number": num})
            return records
        except ImportError:
            # 未安装 BeautifulSoup，返回空
            logger.warning("未安装 BeautifulSoup，无法解析 HTML")
            return []
        except Exception as e:
            logger.error(f"HTML 解析失败: {e}")
            return []

    def _search_web_fallback(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        降级 Web 搜索：优先 SerpAPI，其次 Google CSE
        
        参数：
            query: 检索关键词
            limit: 最大返回条数
        
        返回：
            List[Dict]: 搜索结果列表
        """
        # 增加"专利"关键词以提高搜索精度
        enhanced_query = f"{query} 专利 中国专利"
        
        # 尝试 SerpAPI
        if self.serpapi_key:
            results = self._serpapi_search(enhanced_query, limit)
            if results:
                return results
        
        # 尝试 Google CSE
        if self.google_cse_key and self.google_cse_id:
            results = self._google_cse_search(enhanced_query, limit)
            if results:
                return results
        
        logger.warning("未配置任何 Web 搜索 API Key，降级搜索无结果")
        return []

    def _serpapi_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """SerpAPI 网页搜索"""
        url = "https://serpapi.com/search.json"
        params = {"q": query, "api_key": self.serpapi_key, "num": limit}
        try:
            resp = requests.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            results = []
            for item in data.get("organic_results", [])[:limit]:
                results.append({
                    "title": item.get("title", ""),
                    "abstract": item.get("snippet", ""),
                    "link": item.get("link", ""),
                    "source": "Web搜索(SerpAPI)"
                })
            return results
        except Exception as e:
            logger.error(f"SerpAPI 搜索失败: {e}")
            return []

    def _google_cse_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Google 自定义搜索"""
        url = "https://www.googleapis.com/customsearch/v1"
        params = {"q": query, "key": self.google_cse_key, "cx": self.google_cse_id, "num": limit}
        try:
            resp = requests.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            results = []
            for item in data.get("items", [])[:limit]:
                results.append({
                    "title": item.get("title", ""),
                    "abstract": item.get("snippet", ""),
                    "link": item.get("link", ""),
                    "source": "Web搜索(GoogleCSE)"
                })
            return results
        except Exception as e:
            logger.error(f"Google CSE 搜索失败: {e}")
            return []

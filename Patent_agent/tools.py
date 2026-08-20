"""
检索工具集
==========
集成多种真实网络检索工具，确保数据来源可追溯。

包含：
- 中国专利查新（国知局优先，Web 降级）
- 美国专利检索（PatentsView）
- 学术论文检索（Crossref）
- 网页搜索（SerpAPI / Google CSE）

核心类：
- RetrievalTools：统一检索入口
"""

import os
import logging
import requests
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode
from patent_agent.cn_patent_search import CNPatentSearch

logger = logging.getLogger(__name__)

class RetrievalTools:
    """
    统一检索工具集
    
    提供 patent_cn（中国专利）、patent_us（美国专利）、
    crossref（论文）、web（网页）四类检索能力。
    """
    
    def __init__(self, config):
        """
        初始化检索工具
        
        参数：
            config: RetrievalConfig 配置对象
        """
        self.config = config
        self.patentsview_base = config.patentsview_base
        self.crossref_base = config.crossref_base
        self.timeout = config.timeout
        # 初始化中国专利检索器
        self.cn_patent = CNPatentSearch(config)

    def patent_cn_search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        中国专利查新（含降级逻辑）
        
        参数：
            query: 检索关键词
            limit: 最大返回条数
        
        返回：
            List[Dict]: 专利信息列表
        """
        return self.cn_patent.search(query, limit)

    def patent_us_search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        美国专利检索（PatentsView API，免费）
        
        参数：
            query: 检索关键词
            limit: 最大返回条数
        
        返回：
            List[Dict]: 专利信息列表
        """
        # 构造 PatentsView API 查询 URL
        # 使用 JSON 格式查询参数
        url = (f"{self.patentsview_base}?q={{\"_text_any\":"
               f"{{\"patent_title\":\"{query}\"}}}}"
               f"&f=[\"patent_number\",\"patent_title\",\"patent_abstract\","
               f"\"patent_date\",\"inventors\"]"
               f"&o={{\"per_page\":{limit}}}")
        try:
            resp = requests.get(url, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            results = []
            for p in data.get("patents", []):
                # 提取发明人列表
                inventors = ", ".join([
                    i.get("inventor_first_name", "") + " " + i.get("inventor_last_name", "")
                    for i in p.get("inventors", [])
                ])
                results.append({
                    "title": p.get("patent_title", ""),
                    "abstract": p.get("patent_abstract", ""),
                    "patent_number": p.get("patent_number", ""),
                    "date": p.get("patent_date", ""),
                    "inventors": inventors,
                    "source": "PatentsView(美国专利)"
                })
            return results
        except Exception as e:
            logger.error(f"PatentsView 检索失败: {e}")
            return []

    def crossref_search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        学术论文检索（Crossref API，免费）
        
        参数：
            query: 检索关键词
            limit: 最大返回条数
        
        返回：
            List[Dict]: 论文信息列表
        """
        # 构造查询参数
        params = {
            "query.title": query,
            "rows": limit,
            "format": "json"
        }
        url = f"{self.crossref_base}?{urlencode(params)}"
        try:
            resp = requests.get(url, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("message", {}).get("items", [])
            results = []
            for it in items:
                # 提取标题和作者
                title = it.get("title", [""])[0] if it.get("title") else ""
                authors = ", ".join([
                    f"{a.get('given', '')} {a.get('family', '')}"
                    for a in it.get("author", [])
                ])
                results.append({
                    "title": title,
                    "abstract": it.get("abstract", ""),
                    "doi": it.get("DOI", ""),
                    "date": it.get("issued", {}).get("date-parts", [[""]])[0][0],
                    "authors": authors,
                    "source": "Crossref(学术论文)"
                })
            return results
        except Exception as e:
            logger.error(f"Crossref 检索失败: {e}")
            return []

    def web_search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        通用网页搜索（SerpAPI 优先，Google CSE 备选）
        
        参数：
            query: 检索关键词
            limit: 最大返回条数
        
        返回：
            List[Dict]: 搜索结果列表
        """
        # 先尝试 SerpAPI
        results = self._serpapi_search(query, limit)
        if results:
            return results
        # 降级到 Google CSE
        return self._google_cse_search(query, limit)

    def _serpapi_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """SerpAPI 搜索实现"""
        api_key = os.getenv(self.config.serpapi_key_env, "")
        if not api_key:
            return []
        url = "https://serpapi.com/search.json"
        params = {"q": query, "api_key": api_key, "num": limit}
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
        """Google CSE 搜索实现"""
        api_key = os.getenv(self.config.google_cse_key_env, "")
        cse_id = os.getenv(self.config.google_cse_id_env, "")
        if not api_key or not cse_id:
            return []
        url = "https://www.googleapis.com/customsearch/v1"
        params = {"q": query, "key": api_key, "cx": cse_id, "num": limit}
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

    def retrieve(self, tool_name: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        统一检索入口
        
        参数：
            tool_name: 工具名称，可选值：
                - "patent_cn"：中国专利查新
                - "patent_us"：美国专利
                - "crossref"：学术论文
                - "web"：网页搜索
            query: 检索关键词
            limit: 最大返回条数
        
        返回：
            List[Dict]: 检索结果列表
        """
        tool_map = {
            "patent_cn": self.patent_cn_search,
            "patent_us": self.patent_us_search,
            "patent": self.patent_cn_search,  # 兼容旧名称，默认中国专利
            "crossref": self.crossref_search,
            "web": self.web_search,
        }
        if tool_name not in tool_map:
            raise ValueError(f"未知检索工具: {tool_name}")
        return tool_map[tool_name](query, limit)
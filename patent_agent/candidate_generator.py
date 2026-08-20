"""
候选发明方向生成器
=================
基于用户输入（标题、领域、问题），通过真实网络检索现有技术，
调用 LLM 生成至少 3 个候选发明方向供用户选择。

核心类：
- CandidateGenerator：候选方向生成器
"""

import json
import logging
from typing import List, Dict, Any
from patent_agent.llm import LLMClient
from patent_agent.tools import RetrievalTools

logger = logging.getLogger(__name__)

class CandidateGenerator:
    """
    候选方向生成器
    
    工作流程：
    1. 根据用户输入构造检索关键词
    2. 执行中国专利查新 + 美国专利 + 论文检索
    3. 汇总检索结果
    4. 调用 LLM 基于真实资料生成候选方向
    """
    
    def __init__(self, llm: LLMClient, tools: RetrievalTools):
        """
        初始化
        
        参数：
            llm: 大模型客户端
            tools: 检索工具集
        """
        self.llm = llm
        self.tools = tools

    def generate(self, user_input: Dict[str, str]) -> List[Dict[str, str]]:
        """
        生成候选发明方向
        
        参数：
            user_input: 包含 title（标题）、field（领域）、problem（问题）的字典
        
        返回：
            List[Dict]: 至少 3 个候选方向，每个含 title/innovation/solution/advantages
        """
        # 1. 构造检索关键词
        queries = self._build_queries(user_input)
        
        # 2. 执行多路检索
        retrieval_results = {}
        for q in queries:
            # 中国专利查新（优先）
            cn_patents = self.tools.retrieve("patent_cn", q, limit=3)
            # 美国专利补充
            us_patents = self.tools.retrieve("patent_us", q, limit=2)
            # 学术论文补充
            papers = self.tools.retrieve("crossref", q, limit=2)
            
            retrieval_results[q] = {
                "cn_patents": cn_patents,
                "us_patents": us_patents,
                "papers": papers
            }
            logger.info(f"检索关键词 '{q}'：中国专利 {len(cn_patents)} 条，美国专利 {len(us_patents)} 条，论文 {len(papers)} 条")

        # 3. 汇总检索摘要
        retrieval_summary = self._summarize_retrieval(retrieval_results)

        # 4. 调用 LLM 生成候选方向
        system_prompt = """你是一名资深的发明专利申请策略专家。根据用户提供的最初想法和检索到的真实现有技术，提出至少 3 个具有可专利性的发明方向。每个方向必须：
- 有明确的技术创新点，且未被现有技术公开
- 能够解决用户提出的技术问题
- 具有实际可行性
- 不编造数据，所有判断基于检索结果

输出 JSON 数组，每个元素包含：
{
  "title": "发明方向标题（简洁明确）",
  "innovation": "核心创新点描述",
  "solution": "技术方案概述（具体实现方式）",
  "advantages": "相对于现有技术的优势"
}

注意：请只输出 JSON 数组本身，不要包含任何解释性文字或 markdown 代码块标记（如 ```json）。
"""
        user_prompt = f"""
用户想法：
标题：{user_input.get('title', '')}
技术领域/方向：{user_input.get('field', '')}
要解决的技术问题：{user_input.get('problem', '')}

检索到的现有技术摘要（只使用这些真实资料）：
{retrieval_summary}

请基于以上信息，提出至少 3 个候选发明方向。
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # 获取 LLM 响应
        response = self.llm.get_json_response(messages)
        
        # 解析响应
        if isinstance(response, list) and len(response) >= 3:
            return response[:5]  # 最多返回 5 个
        elif isinstance(response, dict) and "candidates" in response:
            cands = response["candidates"]
            if isinstance(cands, list) and len(cands) >= 3:
                return cands[:5]
        
        # 响应格式异常
        raise ValueError("候选方向生成失败，LLM 未返回至少 3 个方向")

    def _build_queries(self, user_input: Dict[str, str]) -> List[str]:
        """
        根据用户输入构造检索关键词列表
        
        参数：
            user_input: 用户输入字典
        
        返回：
            List[str]: 关键词列表
        """
        queries = []
        # 技术领域
        if user_input.get("field"):
            queries.append(user_input["field"])
        # 发明标题
        if user_input.get("title"):
            queries.append(user_input["title"])
        # 技术问题
        if user_input.get("problem"):
            queries.append(user_input["problem"])
        # 组合查询：领域 + 问题
        if user_input.get("field") and user_input.get("problem"):
            queries.append(f"{user_input['field']} {user_input['problem']}")
        # 去重并限制数量
        unique_queries = list(dict.fromkeys(queries))
        return unique_queries[:5]

    def _summarize_retrieval(self, retrieval_results: Dict[str, Any]) -> str:
        """
        将检索结果整理成文本摘要
        
        参数：
            retrieval_results: 检索结果字典
        
        返回：
            str: 检索摘要文本
        """
        lines = []
        for query, data in retrieval_results.items():
            lines.append(f"【关键词：{query}】")
            # 中国专利
            for item in data.get("cn_patents", [])[:3]:
                lines.append(f"[中国专利] {item.get('title', '')} - {item.get('abstract', '')[:200]}")
            # 美国专利
            for item in data.get("us_patents", [])[:2]:
                lines.append(f"[美国专利] {item.get('title', '')} - {item.get('abstract', '')[:200]}")
            # 学术论文
            for item in data.get("papers", [])[:2]:
                lines.append(f"[学术论文] {item.get('title', '')} - {item.get('abstract', '')[:200]}")
        
        if not lines:
            return "（未检索到相关资料）"
        return "\n".join(lines)

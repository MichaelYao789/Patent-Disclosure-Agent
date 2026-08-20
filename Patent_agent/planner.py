"""
计划生成器
==========
Plan-and-Execute 框架中的 Planner，负责将用户需求分解为可执行步骤。

核心类：
- Planner：基于 LLM 生成包含检索和写作步骤的详细计划
"""

import json
import logging
from typing import List, Dict, Any
from patent_agent.llm import LLMClient

logger = logging.getLogger(__name__)

class Planner:
    """
    计划生成器
    
    根据用户选定的发明方向，生成包含以下类型步骤的计划：
    - retrieve：检索步骤（指定工具和关键词）
    - write：写作步骤（指定交底书章节）
    - analyze：分析步骤（对比现有技术）
    """
    
    def __init__(self, llm_client: LLMClient):
        """
        初始化
        
        参数：
            llm_client: 大模型客户端
        """
        self.llm = llm_client

    def build_plan(self, user_input: str, selected_direction: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        生成执行计划
        
        参数：
            user_input: 用户原始输入（完整文本）
            selected_direction: 用户选定的发明方向
        
        返回：
            List[Dict]: 步骤列表
        """
        system_prompt = """你是专利申请交底书撰写规划器。需要根据用户提供的技术要点（包括最终选定的发明方向），生成一个可执行的详细计划。
计划必须覆盖以下工作：
1. 真实网络检索：优先中国专利查新（patent_cn），补充美国专利（patent_us）、论文（crossref）、网页（web）等，收集与发明最接近的现有技术。
2. 撰写交底书各章节内容（章节编号 1-15，包括 7.1-7.4、15.1-15.2）。
3. 生成可编辑图表（流程图、数据表等）。
4. 输出 Word 文档。

你只能使用真实检索数据，不得虚构。每个检索步骤必须指定工具：patent_cn / patent_us / crossref / web，并给出检索关键词。
每个写作步骤必须指定交底书章节号。输出 JSON 数组，格式：
[
  {"step_id": 1, "type": "retrieve", "tool": "patent_cn", "query": "关键词", "notes": "说明"},
  {"step_id": 2, "type": "write", "section": "1", "title": "标题", "depends_on": [1], "notes": "写作要求"}
]
"""
        user_prompt = f"""
用户原始输入：
{user_input}

最终选定的发明方向：
标题：{selected_direction.get('title', '')}
创新点：{selected_direction.get('innovation', '')}
技术方案概述：{selected_direction.get('solution', '')}
优势：{selected_direction.get('advantages', '')}

请生成执行计划。
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        plan = self.llm.get_json_response(messages)
        if not isinstance(plan, list):
            raise ValueError("计划格式错误，应为 JSON 数组")
        return plan
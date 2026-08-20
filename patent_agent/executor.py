"""
计划执行器
==========
Plan-and-Execute 框架中的 Executor，负责逐步执行计划并管理状态。

核心类：
- Executor：执行检索、写作、分析步骤，自动补全缺失章节
"""

import json
import logging
from typing import Dict, Any, List
from patent_agent.tools import RetrievalTools
from patent_agent.llm import LLMClient

logger = logging.getLogger(__name__)

class Executor:
    """
    计划执行器
    
    维护执行状态（state），包含：
    - user_input: 用户原始输入
    - selected_direction: 选定发明方向
    - sections: 已完成的交底书章节
    - retrieval_results: 检索结果汇总
    - figures: 图表列表
    - tables: 数据表列表
    """
    
    def __init__(self, llm_client: LLMClient, retrieval_tools: RetrievalTools):
        """
        初始化
        
        参数：
            llm_client: 大模型客户端
            retrieval_tools: 检索工具集
        """
        self.llm = llm_client
        self.tools = retrieval_tools
        # 初始化状态
        self.state = {
            "user_input": "",
            "selected_direction": {},
            "sections": {},
            "retrieval_results": {},
            "figures": [],
            "tables": [],
        }

    def execute_plan(self, plan: List[Dict[str, Any]], user_input: str, 
                     selected_direction: Dict[str, str]) -> Dict[str, Any]:
        """
        执行完整计划
        
        参数：
            plan: 步骤列表
            user_input: 用户原始输入
            selected_direction: 选定发明方向
        
        返回：
            Dict: 执行后的状态字典
        """
        # 保存输入信息到状态
        self.state["user_input"] = user_input
        self.state["selected_direction"] = selected_direction
        
        # 逐步执行计划
        for step in plan:
            step_id = step.get("step_id", len(self.state["sections"]) + 1)
            step_type = step.get("type")
            logger.info(f"执行步骤 {step_id}: {step_type}")
            
            if step_type == "retrieve":
                self._execute_retrieve(step)
            elif step_type == "write":
                self._execute_write(step)
            elif step_type == "analyze":
                self._execute_analyze(step)
            else:
                logger.warning(f"未知步骤类型: {step_type}")
        
        # 校验并补全缺失章节
        self._validate_sections()
        return self.state

    def _execute_retrieve(self, step: Dict[str, Any]):
        """
        执行检索步骤
        
        参数：
            step: 检索步骤定义，包含 tool、query、limit 等
        """
        tool = step.get("tool", "patent_cn")  # 默认中国专利
        query = step.get("query", "")
        limit = step.get("limit", 5)
        
        # 调用检索工具
        results = self.tools.retrieve(tool, query, limit)
        
        # 保存结果到状态
        step_id = str(step.get("step_id"))
        self.state["retrieval_results"][step_id] = {
            "tool": tool,
            "query": query,
            "results": results,
            "notes": step.get("notes", "")
        }
        logger.info(f"检索完成: {tool} 查询 '{query}' 返回 {len(results)} 条")

    def _execute_write(self, step: Dict[str, Any]):
        """
        执行写作步骤
        
        参数：
            step: 写作步骤定义，包含 section、title、depends_on、notes 等
        """
        section = step.get("section", "")
        title = step.get("title", "")
        deps = step.get("depends_on", [])
        
        # 构建检索上下文
        retrieval_context = self._build_context(deps)
        
        # 构建写作提示
        system_prompt = self._writing_system_prompt()
        user_prompt = f"""
用户原始输入：
{self.state.get('user_input', '')}

最终选定发明方向：
标题：{self.state['selected_direction'].get('title', '')}
创新点：{self.state['selected_direction'].get('innovation', '')}
技术方案概述：{self.state['selected_direction'].get('solution', '')}
优势：{self.state['selected_direction'].get('advantages', '')}

已收集的真实资料（只允许使用这些资料，未检索到请明确说明）：
{retrieval_context}

请撰写交底书第 {section} 部分：{title}
要求：
{step.get('notes', '')}

输出格式：直接输出该章节的正式内容，使用 Markdown 格式。
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # 调用 LLM 生成章节内容
        content = self.llm.chat(messages, temperature=0.3)
        self.state["sections"][section] = content
        logger.info(f"章节 {section} 写入完成，长度 {len(content)}")

    def _execute_analyze(self, step: Dict[str, Any]):
        """
        执行分析步骤（生成技术对比表）
        
        参数：
            step: 分析步骤定义
        """
        section = step.get("section", "analysis")
        deps = step.get("depends_on", [])
        context = self._build_context(deps)
        
        prompt = f"""
请根据用户技术要点和以下检索结果，生成现有技术与本发明技术方案的对比分析。
只使用真实检索数据，不要虚构效果数据。
{context}

输出 Markdown 表格，列为：对比项 | 现有技术 | 本发明方案 | 优势说明
"""
        messages = [
            {"role": "system", "content": "你是专利技术分析专家，保证数据真实。"},
            {"role": "user", "content": prompt}
        ]
        content = self.llm.chat(messages)
        self.state["sections"][section] = content
        logger.info(f"分析章节 {section} 完成")

    def _build_context(self, dep_ids: List) -> str:
        """
        根据依赖步骤 ID 组装检索结果上下文
        
        参数：
            dep_ids: 依赖的步骤 ID 列表
        
        返回：
            str: 检索结果上下文文本
        """
        ctx = []
        for dep in dep_ids:
            key = str(dep)
            if key in self.state["retrieval_results"]:
                r = self.state["retrieval_results"][key]
                ctx.append(f"【检索工具 {r['tool']}，关键词：{r['query']}】")
                for i, item in enumerate(r["results"], 1):
                    ctx.append(f"{i}. {item.get('title', '')} - {item.get('abstract', '')[:500]}")
        return "\n\n".join(ctx) if ctx else "（无检索资料）"

    def _writing_system_prompt(self) -> str:
        """返回写作系统提示词"""
        return """你是中国发明专利交底书撰写专家。必须严格遵守：
1. 所有技术方案、数据、效果必须基于用户提供的技术要点和检索到的真实资料，不得编造。
2. 对于未检索到或无法确认的内容，明确标注"未检索到"或"需进一步确认"。
3. 内容需符合专利交底书规范，避免使用英文单词，英文缩写需给出中文全称。
4. 专利必须是一个完整技术方案，充分公开以本领域技术人员可实现为准。
5. 权利要求部分列出关键保护点，但仅作为交底书内容，最终由专利代理人撰写。"""

    def _validate_sections(self):
        """
        校验必需章节是否齐全，缺失则自动补写
        """
        required = ["1", "2", "3", "4", "5", "6", "7.1", "7.2", "7.3", "7.4",
                    "8", "9", "10", "11", "12", "13", "14", "15.1", "15.2"]
        missing = [s for s in required if s not in self.state["sections"]]
        if missing:
            logger.warning(f"缺失章节: {missing}，自动补写...")
            for sec in missing:
                self._execute_write({
                    "step_id": f"auto_{sec}",
                    "type": "write",
                    "section": sec,
                    "title": f"章节 {sec}",
                    "depends_on": [],
                    "notes": "请按照交底书规范撰写该章节，如无足够信息则注明需补充。"
                })

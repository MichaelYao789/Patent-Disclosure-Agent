"""
AI辅助编写发明专利交底书 Agent
================================
基于 Plan-and-Execute 框架，集成中国专利查新、真实网络检索、
多模型 API、可编辑图表和 Word 输出。

版本：3.0.0
功能：
- 交互式候选发明方向生成（至少3个）
- 国家知识产权局专利查新（优先）+ Web 降级搜索
- 完整 15 章交底书自动撰写
- 可编辑流程图（DOT 源码）、Excel 数据表
- Word 格式最终文档输出

作者：开源社区
许可证：MIT
"""

__version__ = "3.0.0"
__author__ = "Open Source Community"
__license__ = "MIT"

# 定义导出的公共接口
__all__ = [
    "config",
    "llm",
    "tools",
    "cn_patent_search",
    "candidate_generator",
    "planner",
    "executor",
    "writer",
    "visualizer",
    "docx_generator",
    "excel_generator",
]

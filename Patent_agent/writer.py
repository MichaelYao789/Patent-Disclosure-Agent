"""
交底书内容聚合与 Markdown 输出
==============================
将各章节内容按标准顺序聚合为完整 Markdown 文档。

核心类：
- PatentWriter：交底书写入器
"""

import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PatentWriter:
    """
    交底书写入器
    
    负责将 Executor 生成的各章节内容按标准顺序排列，
    聚合为完整的 Markdown 文档，并保存到输出目录。
    """
    
    def __init__(self, config):
        """
        初始化
        
        参数：
            config: OutputConfig 配置对象
        """
        self.output_dir = config.output.dir
        os.makedirs(self.output_dir, exist_ok=True)

    def build_markdown(self, state: Dict[str, Any]) -> str:
        """
        构建完整 Markdown 文档
        
        参数：
            state: 执行状态，包含 sections 和 retrieval_results
        
        返回：
            str: 完整 Markdown 文本
        """
        sections = state.get("sections", {})
        md_lines = ["# 发明专利交底书\n"]
        
        # 按标准顺序排列章节
        section_order = [
            ("1", "标题"),
            ("2", "技术领域"),
            ("3", "摘要"),
            ("4", "本发明要解决的技术问题"),
            ("5", "技术背景与现有技术方案"),
            ("6", "现有技术的缺点与本发明的目的"),
            ("7.1", "发明内容"),
            ("7.2", "实施方式"),
            ("7.3", "附图"),
            ("7.4", "详细描述"),
            ("8", "本发明的关键点和保护点"),
            ("9", "与现有技术相比的优点"),
            ("10", "替代方案"),
            ("11", "附图及说明"),
            ("12", "权利要求"),
            ("13", "引用文献"),
            ("14", "说明书附录"),
            ("15.1", "避免英文单词注意事项"),
            ("15.2", "专利法规定"),
        ]
        
        # 逐章节添加
        for sec, title in section_order:
            content = sections.get(sec, "")
            md_lines.append(f"\n## {sec} {title}\n")
            md_lines.append(content)
        
        # 添加检索资料汇总
        retrieval_results = state.get("retrieval_results", {})
        if retrieval_results:
            md_lines.append("\n## 附：检索资料汇总（真实来源）\n")
            for step_id, data in retrieval_results.items():
                md_lines.append(f"\n### 检索步骤 {step_id}：{data['tool']} / {data['query']}\n")
                for i, item in enumerate(data["results"], 1):
                    md_lines.append(f"{i}. **{item.get('title', '')}**  \n   {item.get('abstract', '')[:300]}  \n   来源：{item.get('source', '')}")
        
        return "\n".join(md_lines)

    def save_markdown(self, markdown_text: str, filename: str = "patent_disclosure.md") -> str:
        """
        保存 Markdown 文档
        
        参数：
            markdown_text: Markdown 文本
            filename: 文件名
        
        返回：
            str: 保存路径
        """
        path = os.path.join(self.output_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(markdown_text)
        logger.info(f"Markdown 文档已保存: {path}")
        return path
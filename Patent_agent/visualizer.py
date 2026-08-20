"""
图表生成器
==========
生成可编辑的流程图（DOT 源码 + PNG 图片）。

核心类：
- Visualizer：图表生成器
"""

import os
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class Visualizer:
    """
    图表生成器
    
    使用 Graphviz 生成流程图，同时保留 DOT 源码便于编辑。
    """
    
    def __init__(self, output_dir: str):
        """
        初始化
        
        参数：
            output_dir: 输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_flowchart(self, title: str, nodes: List[str], edges: List[tuple],
                           filename: str = "flowchart") -> Dict[str, str]:
        """
        生成流程图
        
        参数：
            title: 流程图标题
            nodes: 节点列表
            edges: 边列表，格式 [(from, to), ...]
            filename: 文件名（不含扩展名）
        
        返回：
            Dict: 包含 dot_source、dot_path、png_path
        """
        # 构建 DOT 源码
        dot_lines = [
            f'digraph "{title}" {{',
            '  rankdir=LR;',
            '  node [shape=box, style="rounded,filled", fillcolor=lightblue];'
        ]
        for n in nodes:
            dot_lines.append(f'  "{n}";')
        for e in edges:
            dot_lines.append(f'  "{e[0]}" -> "{e[1]}";')
        dot_lines.append("}")
        dot_source = "\n".join(dot_lines)
        
        # 保存 DOT 源码
        dot_path = os.path.join(self.output_dir, f"{filename}.dot")
        png_path = os.path.join(self.output_dir, f"{filename}.png")
        with open(dot_path, "w", encoding="utf-8") as f:
            f.write(dot_source)
        
        # 尝试生成 PNG（需要安装 Graphviz）
        png_generated = False
        try:
            from graphviz import Source
            src = Source(dot_source, format="png")
            src.render(filename=filename, directory=self.output_dir, cleanup=True)
            png_generated = os.path.exists(png_path)
        except Exception as e:
            logger.warning(f"Graphviz 未安装或渲染失败: {e}，仅保留 DOT 源码")
        
        return {
            "dot_source": dot_source,
            "dot_path": dot_path,
            "png_path": png_path if png_generated else None
        }
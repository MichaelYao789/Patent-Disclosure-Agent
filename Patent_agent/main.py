"""
主入口程序
==========
交互式运行：输入技术要点 → 生成候选方向 → 用户选择 → 自动撰写交底书。

使用示例：
    # 使用 JSON 文件输入
    python -m patent_agent.main --input examples/input_brief.json
    
    # 交互式输入
    python -m patent_agent.main
"""

import argparse
import logging
import json
import sys
from patent_agent.config import load_config
from patent_agent.llm import LLMClient
from patent_agent.tools import RetrievalTools
from patent_agent.candidate_generator import CandidateGenerator
from patent_agent.planner import Planner
from patent_agent.executor import Executor
from patent_agent.writer import PatentWriter
from patent_agent.visualizer import Visualizer
from patent_agent.docx_generator import DocxGenerator
from patent_agent.excel_generator import ExcelGenerator

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_user_input(args):
    """
    获取用户初始输入
    
    参数：
        args: 命令行参数
    
    返回：
        Dict: 包含 title、field、problem 的字典
    """
    user_input = {}
    
    if args.input:
        # 从文件读取
        with open(args.input, "r", encoding="utf-8") as f:
            content = f.read()
            try:
                data = json.loads(content)
                if "title" in data and "field" in data and "problem" in data:
                    user_input = {
                        "title": data.get("title", ""),
                        "field": data.get("field", ""),
                        "problem": data.get("problem", "")
                    }
                elif "brief" in data:
                    # 兼容旧格式
                    brief = data.get("brief", "")
                    tp = data.get("technical_points", {})
                    user_input = {
                        "title": data.get("title", ""),
                        "field": tp.get("领域", data.get("field", "")),
                        "problem": tp.get("现有技术问题", data.get("problem", ""))
                    }
                else:
                    user_input = data
            except json.JSONDecodeError:
                # 纯文本文件
                lines = content.strip().split('\n')
                user_input = {
                    "title": lines[0] if len(lines) > 0 else "",
                    "field": lines[1] if len(lines) > 1 else "",
                    "problem": lines[2] if len(lines) > 2 else ""
                }
    else:
        # 交互式输入
        print("\n" + "="*60)
        print("   AI 辅助发明专利交底书生成系统")
        print("="*60)
        print("\n请输入初始发明想法：")
        title = input("  1. 发明名称/标题（简洁描述）：").strip()
        field = input("  2. 技术领域/创新方向：").strip()
        problem = input("  3. 要解决的技术问题：").strip()
        user_input = {"title": title, "field": field, "problem": problem}
    
    # 校验必填字段
    for key in ["title", "field", "problem"]:
        if not user_input.get(key):
            print(f"错误：缺少必要字段 '{key}'")
            sys.exit(1)
    
    return user_input


def select_candidate(candidates):
    """
    让用户从候选方向中选择
    
    参数：
        candidates: 候选方向列表
    
    返回：
        Dict: 选定的方向
    """
    print("\n" + "="*60)
    print("   基于检索结果，为您推荐以下发明方向")
    print("="*60)
    
    for i, cand in enumerate(candidates, 1):
        print(f"\n【方向 {i}】")
        print(f"  标题：{cand.get('title', '')}")
        print(f"  创新点：{cand.get('innovation', '')}")
        print(f"  方案概述：{cand.get('solution', '')}")
        print(f"  优势：{cand.get('advantages', '')}")
    
    print(f"\n请选择发明方向（输入 1-{len(candidates)}），或输入 0 自定义：")
    while True:
        choice = input("> ").strip()
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(candidates):
                return candidates[idx-1]
            elif idx == 0:
                print("请输入自定义发明方向：")
                custom = {}
                custom["title"] = input("  标题：").strip()
                custom["innovation"] = input("  创新点：").strip()
                custom["solution"] = input("  方案概述：").strip()
                custom["advantages"] = input("  优势：").strip()
                return custom
        print("输入无效，请重新输入编号。")


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="AI 辅助编写发明专利交底书")
    parser.add_argument("--input", "-i", type=str, help="输入 JSON 文件路径")
    parser.add_argument("--config", "-c", type=str, default="config.yaml", help="配置文件路径")
    parser.add_argument("--output", "-o", type=str, default="output", help="输出目录")
    args = parser.parse_args()
    
    # 加载配置
    config = load_config(args.config)
    if args.output:
        config.output.dir = args.output
    
    # 获取用户输入
    user_input = get_user_input(args)
    logger.info(f"用户输入：{user_input}")
    
    # 初始化组件
    llm = LLMClient(config.llm)
    tools = RetrievalTools(config.retrieval)
    
    # 生成候选方向
    print("\n正在检索现有技术并生成候选发明方向...")
    candidate_gen = CandidateGenerator(llm, tools)
    candidates = candidate_gen.generate(user_input)
    if not candidates:
        print("候选方向生成失败，请重试。")
        sys.exit(1)
    
    # 用户选择方向
    selected = select_candidate(candidates)
    logger.info(f"用户选定方向：{selected['title']}")
    
    # 构建完整输入
    full_input = f"""
用户原始想法：
标题：{user_input['title']}
领域：{user_input['field']}
问题：{user_input['problem']}

最终选定发明方向：
标题：{selected.get('title', '')}
创新点：{selected.get('innovation', '')}
方案概述：{selected.get('solution', '')}
优势：{selected.get('advantages', '')}
"""
    
    # 生成计划
    print("\n正在生成执行计划...")
    planner = Planner(llm)
    plan = planner.build_plan(full_input, selected)
    logger.info(f"计划包含 {len(plan)} 个步骤")
    
    # 执行计划
    print("正在执行计划，撰写交底书...")
    executor = Executor(llm, tools)
    state = executor.execute_plan(plan, full_input, selected)
    logger.info(f"执行完成，共生成 {len(state['sections'])} 个章节")
    
    # 输出文件
    writer = PatentWriter(config.output)
    md_text = writer.build_markdown(state)
    md_path = writer.save_markdown(md_text)
    
    # 生成流程图
    visualizer = Visualizer(config.output.dir)
    flow = visualizer.generate_flowchart(
        title="本发明技术方案流程",
        nodes=["输入技术要点", "检索现有技术", "生成候选方向", "用户选择", "撰写交底书", "输出Word"],
        edges=[("输入技术要点", "检索现有技术"), ("检索现有技术", "生成候选方向"),
               ("生成候选方向", "用户选择"), ("用户选择", "撰写交底书"), 
               ("撰写交底书", "输出Word")],
        filename="技术方案流程"
    )
    
    # 生成 Excel
    excel_gen = ExcelGenerator(config.output.dir)
    excel_path = excel_gen.generate(state)
    
    # 生成 Word
    docx_gen = DocxGenerator(config.output.dir)
    docx_path = docx_gen.generate(state, md_text)
    
    # 输出结果汇总
    print("\n" + "="*60)
    print("   生成完成！")
    print("="*60)
    print(f"  Word 文档：{docx_path}")
    print(f"  Markdown 文档：{md_path}")
    print(f"  Excel 数据表：{excel_path}")
    print(f"  流程图源码：{flow['dot_path']}")
    print("="*60)


if __name__ == "__main__":
    main()
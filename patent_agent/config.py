"""
配置管理模块
============
负责从 YAML 文件和系统环境变量中加载配置，提供统一的配置数据类。

主要类：
- LLMConfig：大模型配置(provider、model、API Key 等)
- RetrievalConfig：检索工具配置
- OutputConfig：输出配置
- AppConfig：聚合配置类
- load_config()：加载配置文件

使用示例：
    config = load_config("config.yaml")
    print(config.llm.provider)  # 输出: deepseek
"""

import os
import yaml
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class LLMConfig:
    """
    大模型配置类
    
    属性：
        provider: 模型提供方，支持 openai/deepseek/anthropic/ollama/moonshot/qwen
        model: 具体模型名称
        api_key_env: API Key 所在环境变量的名称
        base_url: 自定义 API 地址（可选）
        temperature: 采样温度，越低越确定
        max_tokens: 单次生成的最大 token 数
    """
    provider: str = "deepseek"                # 默认使用 DeepSeek
    model: str = "deepseek-chat"              # 默认模型
    api_key_env: str = "DEEPSEEK_API_KEY"     # 环境变量名
    base_url: Optional[str] = None            # 可自定义
    temperature: float = 0.2                  # 低温度保证稳定性
    max_tokens: int = 4096                    # 足够长以生成完整章节


@dataclass
class RetrievalConfig:
    """
    检索工具配置类
    
    属性：
        cn_patent_base: 国知局专利公布公告查询 API 基础地址
        patentsview_base: 美国专利 PatentsView API
        crossref_base: 学术论文 Crossref API
        serpapi_key_env: SerpAPI 网页搜索 Key 的环境变量名
        google_cse_key_env: Google 自定义搜索 Key 的环境变量名
        google_cse_id_env: Google 自定义搜索引擎 ID 的环境变量名
        timeout: 网络请求超时时间（秒）
    """
    cn_patent_base: str = "http://epub.cnipa.gov.cn"  # 国家知识产权局
    patentsview_base: str = "https://api.patentsview.org/patents/query"
    crossref_base: str = "https://api.crossref.org/works"
    serpapi_key_env: str = "SERPAPI_KEY"
    google_cse_key_env: str = "GOOGLE_CSE_KEY"
    google_cse_id_env: str = "GOOGLE_CSE_ID"
    timeout: int = 20


@dataclass
class OutputConfig:
    """
    输出配置类
    
    属性：
        dir: 输出文件目录
        generate_markdown: 是否生成 Markdown
        generate_word: 是否生成 Word
        generate_excel: 是否生成 Excel
        generate_images: 是否生成图片
        template_path: 交底书模板路径
    """
    dir: str = "output"
    generate_markdown: bool = True
    generate_word: bool = True
    generate_excel: bool = True
    generate_images: bool = True
    template_path: str = "templates/disclosure_template.md"


@dataclass
class AppConfig:
    """聚合配置类"""
    llm: LLMConfig
    retrieval: RetrievalConfig
    output: OutputConfig


def load_config(path: str = "config.yaml") -> AppConfig:
    """
    加载配置文件
    
    参数：
        path: YAML 配置文件路径
    
    返回：
        AppConfig: 包含所有子配置的聚合对象
    
    异常：
        FileNotFoundError: 配置文件不存在时抛出
    """
    # 检查配置文件是否存在
    if not os.path.exists(path):
        raise FileNotFoundError(f"配置文件不存在: {path}")
    
    # 读取 YAML 文件
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    
    # 提取各子配置（使用默认值兜底）
    llm_raw = raw.get("llm", {})
    ret_raw = raw.get("retrieval", {})
    out_raw = raw.get("output", {})
    
    # 实例化配置对象
    llm = LLMConfig(**llm_raw)
    retrieval = RetrievalConfig(**ret_raw)
    output = OutputConfig(**out_raw)
    
    return AppConfig(llm=llm, retrieval=retrieval, output=output)

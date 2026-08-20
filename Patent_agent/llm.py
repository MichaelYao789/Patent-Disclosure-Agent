"""
大模型统一客户端
===============
适配多种主流大模型 API，提供统一的 chat 和 JSON 输出接口。

支持的 Provider：
- deepseek：DeepSeek API（https://api.deepseek.com）
- openai：OpenAI API
- anthropic：Anthropic Claude API
- ollama：本地 Ollama（http://localhost:11434/v1）
- moonshot：Moonshot/Kimi API
- qwen：阿里通义千问 API

核心类：
- LLMClient：统一客户端，封装 API 调用差异
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List

# 配置日志
logger = logging.getLogger(__name__)

class LLMClient:
    """
    大模型统一客户端类
    
    通过 provider 参数自动适配不同 API 的调用方式，
    对上层提供一致的 chat() 和 get_json_response() 接口。
    """
    
    def __init__(self, config):
        """
        初始化客户端
        
        参数：
            config: LLMConfig 配置对象
        """
        self.config = config
        # 从环境变量读取 API Key
        self.api_key = os.getenv(config.api_key_env, "")
        self.client = None
        self._init_client()  # 初始化底层客户端

    def _init_client(self):
        """
        初始化底层 API 客户端
        根据 provider 选择对应的 SDK 或客户端
        """
        if self.config.provider in ("openai", "deepseek", "ollama", "moonshot", "qwen"):
            # 这些 provider 都兼容 OpenAI SDK 格式
            try:
                from openai import OpenAI
                base_url = self.config.base_url
                # 自动推断常用 base_url
                if self.config.provider == "deepseek" and not base_url:
                    base_url = "https://api.deepseek.com"
                if self.config.provider == "moonshot" and not base_url:
                    base_url = "https://api.moonshot.cn/v1"
                if self.config.provider == "qwen" and not base_url:
                    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
                if self.config.provider == "ollama" and not base_url:
                    base_url = "http://localhost:11434/v1"
                # 创建 OpenAI 兼容客户端
                self.client = OpenAI(api_key=self.api_key, base_url=base_url)
            except ImportError:
                raise ImportError("请先安装 openai 库：pip install openai")
        elif self.config.provider == "anthropic":
            # Anthropic 使用独立 SDK
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError("请先安装 anthropic 库：pip install anthropic")
        else:
            raise ValueError(f"不支持的 provider: {self.config.provider}")

    def chat(self, messages: List[Dict], temperature: Optional[float] = None,
             max_tokens: Optional[int] = None, 
             response_format: Optional[Dict] = None) -> str:
        """
        发送对话请求并返回文本回复
        
        参数：
            messages: 消息列表，格式 [{"role": "system"/"user"/"assistant", "content": "..."}]
            temperature: 采样温度，None 则使用配置默认值
            max_tokens: 最大生成 token 数
            response_format: 响应格式约束（如 {"type": "json_object"}）
        
        返回：
            str: 模型生成的文本内容
        """
        # 使用配置默认值
        temp = temperature if temperature is not None else self.config.temperature
        max_tok = max_tokens if max_tokens is not None else self.config.max_tokens
        
        if self.config.provider == "anthropic":
            # Anthropic API 调用方式不同，需要拆分 system 和其他消息
            system = ""
            msgs = []
            for m in messages:
                if m["role"] == "system":
                    system = m["content"]
                else:
                    msgs.append(m)
            resp = self.client.messages.create(
                model=self.config.model,
                max_tokens=max_tok,
                temperature=temp,
                system=system,
                messages=msgs
            )
            return resp.content[0].text
        else:
            # OpenAI 兼容 API 调用
            kwargs = dict(
                model=self.config.model,
                messages=messages,
                temperature=temp,
                max_tokens=max_tok,
            )
            if response_format:
                kwargs["response_format"] = response_format
            resp = self.client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content

    def get_json_response(self, messages: List[Dict], 
                          expected_keys: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        强制获取 JSON 格式响应
        
        参数：
            messages: 消息列表
            expected_keys: 期望存在的键列表，用于校验
        
        返回：
            Dict: 解析后的 JSON 数据
        
        异常：
            RuntimeError: 多次尝试后仍无法获取有效 JSON 时抛出
        """
        # 最多重试 3 次
        for attempt in range(3):
            try:
                # 请求 JSON 格式响应
                content = self.chat(messages, response_format={"type": "json_object"})
                data = json.loads(content)
                # 校验必要键
                if expected_keys:
                    missing = [k for k in expected_keys if k not in data]
                    if not missing:
                        return data
                else:
                    return data
            except Exception as e:
                logger.warning(f"JSON 解析失败，重试 {attempt+1}: {e}")
        raise RuntimeError("无法从 LLM 获取有效 JSON")
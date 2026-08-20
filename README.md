# AI 辅助编写发明专利交底书 Agent（含中国专利查新）

基于 **Plan-and-Execute** 框架的智能体，支持**中国专利现场查新**（国知局优先，Web 降级），从简要技术要点自动生成符合中国专利交底书规范的完整文档。

## 核心功能

- **中国专利查新**：优先查询国家知识产权局·专利公布公告，异常时降级 Web 搜索
- **交互式候选方向**：输入标题/领域/问题，自动检索并推荐 3-5 个可专利化方向
- **完整交底书**：自动撰写 1-15 章全部内容（含 7.1-7.4、15.1-15.2）
- **真实数据**：所有检索来自真实 API，不编造
- **多模型支持**：OpenAI / DeepSeek / Anthropic / Ollama / Moonshot / Qwen
- **可编辑输出**：DOT 流程图源码、Excel 数据表、Word 文档

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 配置 API Key
cp .env.example .env
# 编辑 .env 填入 DEEPSEEK_API_KEY

# 运行
python -m patent_agent.main --input examples/input_brief.json
```

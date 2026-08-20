## 一、工程结构

patent-agent/
├── README.md              # 主文档
├── DEPLOYMENT.md          # 部署详细说明
├── config.yaml            # 配置文件
├── templates/             # 模板文件
├── examples/              # 示例输入
├── patent_agent/          # 核心代码
└── output/                # 输出目录

## 二、开源协议
MIT License

### 2.22 `DEPLOYMENT.md`

```markdown
# 部署安装详细说明

## 一、本地运行

### 1. 环境准备
- Python 3.9+
- pip
- （可选）Graphviz 系统包（用于流程图 PNG 渲染）

### 2. 安装步骤

```bash
# 克隆或下载工程
cd patent-agent

# 安装 Python 依赖
pip install -r requirements.txt

# 可选：安装 Graphviz（用于流程图渲染）
# Windows: 从 graphviz.org 下载安装包
# macOS: brew install graphviz
# Linux: sudo apt-get install graphviz


### 3. 配置 API Key

cp .env.example .env
# 编辑 .env 文件，填入至少一个大模型 API Key

### 4. 运行

# 使用示例输入
python -m patent_agent.main --input examples/input_brief.json

# 交互式输入
python -m patent_agent.main

# 自定义配置
python -m patent_agent.main --config config.yaml --output output


### 5. 生成 README Word

python generate_readme_docx.py
# 输出：output/README.docx


## 二、MonkeyCode 平台部署
步骤 1：创建项目
登录 MonkeyCode 平台

点击"新建项目"

选择"Python"环境

项目名称：patent-agent

步骤 2：上传代码
将工程所有文件上传至项目目录

确保目录结构完整

步骤 3：配置环境变量
在平台"环境变量"设置中添加：

DEEPSEEK_API_KEY=sk-xxx
SERPAPI_KEY=xxx（可选）

步骤 4：安装依赖
在终端执行

pip install -r requirements.txt

步骤 5：运行

python -m patent_agent.main --input examples/input_brief.json

步骤 6：查看输出
输出文件在 output/ 目录，可下载 Word 文档。

## 三、WorkBuddy 平台部署
步骤 1：创建工作空间
登录 WorkBuddy

创建新工作空间

步骤 2：导入工程
1. 上传整个 patent-agent 文件夹
2. 或连接 GitHub 仓库

步骤 3：环境配置
在 WorkBuddy 的"环境变量"中添加：

DEEPSEEK_API_KEY=sk-xxx

步骤 4：安装依赖
在 WorkBuddy 终端执行：

pip install -r requirements.txt

步骤 5：启动

python -m patent_agent.main --input examples/input_brief.json


## 四、GitHub 开源发布

步骤 1：初始化仓库
bash
cd patent-agent
git init
git add .
git commit -m "初始提交"

步骤 2：创建 GitHub 仓库
1. 登录 GitHub → New repository
2. 仓库名：patent-agent
3. 设为 Public（开源）

步骤 3：推送代码

git remote add origin https://github.com/用户名/patent-agent.git
git push -u origin main

步骤 4：配置 GitHub Secrets
在仓库 Settings → Secrets → Actions 中添加：

DEEPSEEK_API_KEY
SERPAPI_KEY（可选）

步骤 5：README 徽章
在 README 中添加许可证徽章：

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


## 五、常见问题
Q1: 国知局查询无结果？
A: 系统会自动降级到 Web 搜索，请配置 SERPAPI_KEY 或 GOOGLE_CSE_KEY。

Q2: Graphviz 未安装？
A: 不影响运行，仍会保存 DOT 源码，可在线渲染。

Q3: 如何切换大模型？
A: 修改 config.yaml 中 llm.provider 和 llm.model，在 .env 设置对应 Key。



## 三、打包为 ZIP

将以上所有文件保存到 `patent-agent` 文件夹后，在上级目录执行：

```bash
# Linux/macOS
zip -r patent-agent.zip patent-agent/

# Windows PowerShell
Compress-Archive -Path patent-agent -DestinationPath patent-agent.zip


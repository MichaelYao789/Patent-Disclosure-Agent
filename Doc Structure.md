patent-agent/
├── README.md                          # 主说明文档
├── DEPLOYMENT.md                      # 平台部署详细说明
├── requirements.txt
├── Dockerfile
├── .env.example
├── config.yaml
├── generate_readme_docx.py
├── templates/
│   └── disclosure_template.md         # 交底书模板（含全部章节）
├── examples/
│   └── input_brief.json
├── patent_agent/
│   ├── __init__.py
│   ├── config.py
│   ├── llm.py
│   ├── tools.py                       # 含中国专利查新 + 降级搜索
│   ├── cn_patent_search.py            # 国知局专利检索模块
│   ├── candidate_generator.py
│   ├── planner.py
│   ├── executor.py
│   ├── writer.py
│   ├── visualizer.py
│   ├── docx_generator.py
│   ├── excel_generator.py
│   └── main.py
└── output/                            # 运行后自动创建
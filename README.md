# XiaoTao Travel - 智能旅行规划助手

基于 **LangChain ReAct Agent + MCP 工具 + RAG 知识库** 的智能旅行规划系统。

> CS599 大作业 | 方向一：Agentic AI 原生开发

## 项目简介

用户输入旅行需求后，Agent 自动调用 12306 火车票查询、高德地图路线规划、天气预报、酒店搜索、黄历吉日、航班查询等 MCP 工具，并结合 RAG 文档检索与 DeepSeek R1 深度推理，生成完整的个性化旅行方案。

## 技术栈

| 层次 | 技术 |
|------|------|
| LLM | DeepSeek R1（深度推理）+ Qwen3/DashScope（通用对话与 Embedding） |
| Agent 框架 | LangChain ReAct Agent |
| 工具协议 | MCP（Model Context Protocol） |
| RAG | ChromaDB 向量数据库 + LangChain Retriever |
| 后端 | FastAPI + Uvicorn |
| 前端 | Vue 3 + Vite + TypeScript + Pinia |

## 目录结构

```
cs599-project/
├── docs/                         # 项目文档
│   └── architecture.md            # 系统架构说明
├── src/                          # 项目源代码
│   ├── backend/                  # FastAPI 后端
│   │   ├── api/                  # 路由（chat、documents、tools）
│   │   ├── schemas/              # Pydantic 请求/响应模型
│   │   └── services/             # Agent 编排、SSE 状态流、工具调度
│   ├── frontend/                 # Vue 3 前端
│   │   ├── src/api/              # API 客户端与 SSE 连接
│   │   ├── src/components/       # UI 组件
│   │   ├── src/stores/           # Pinia 状态管理
│   │   └── src/views/            # 主页面
│   └── aggentic_RAG/             # RAG 知识库 + Agent 工具
│       ├── travel_agent/
│       │   ├── config/           # 模型配置、Prompt 模板、MCP 配置
│       │   └── tools/            # MCP 工具管理、RAG 检索、R1 推理
│       └── data/                 # ChromaDB 持久化目录
├── README.md
├── .gitignore
└── LICENSE
```

## 快速开始

### 1. 安装依赖

```bash
# 后端
pip install -r src/aggentic_RAG/requirements.txt

# 前端
cd src/frontend && npm install
```

### 2. 配置环境变量

```bash
cp src/aggentic_RAG/.env.example src/aggentic_RAG/.env
```

编辑 `src/aggentic_RAG/.env`，填入 API Key：

```bash
DEEPSEEK_API_KEY=sk-your-deepseek-key
DASHSCOPE_API_KEY=sk-your-dashscope-key
```

MCP 服务端配置：

```bash
cp src/aggentic_RAG/travel_agent/config/servers_config.json.example \
   src/aggentic_RAG/travel_agent/config/servers_config.json
```

### 3. 启动

```bash
# 后端（从 src/ 目录执行）
cd src && uvicorn backend.main:app --reload --port 8000

# 前端（新终端）
cd src/frontend && npm run dev
```

访问 `http://localhost:5173`

### 4. 健康检查

```bash
curl http://127.0.0.1:8000/api/health
```

## 系统架构

详见 [docs/architecture.md](docs/architecture.md)

```
用户输入 → Vue 3 前端 → FastAPI API → LangChain ReAct Agent
                                              │
                        ┌─────────────────────┼─────────────────────┐
                        ▼                     ▼                     ▼
                   RAG 检索              MCP 工具调用           R1 深度分析
                  (ChromaDB)      (12306/高德/航班/黄历)      (DeepSeek)
                        │                     │                     │
                        └─────────────────────┼─────────────────────┘
                                              ▼
                                        结果合成 → SSE 流式返回 → 前端展示
```

## 项目状态

- [x] Proposal
- [x] MVP
- [ ] Final

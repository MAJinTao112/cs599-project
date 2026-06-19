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

## 运行前准备

本项目依赖外部大模型 API 和 MCP 服务。首次运行前需要准备以下配置：

| 配置项 | 来源/平台 | 用途 | 是否必填 |
|--------|-----------|------|----------|
| `DEEPSEEK_API_KEY` | DeepSeek 开放平台 | 调用 DeepSeek R1，用于复杂路线推理与优化 | 必填 |
| `DASHSCOPE_API_KEY` | 阿里云 DashScope / 百炼 | 调用 Qwen 对话模型和 `text-embedding-v4` 嵌入模型 | 必填 |
| `LANGCHAIN_API_KEY` | LangSmith | 调试链路追踪，仅在启用 `LANGCHAIN_TRACING_V2=true` 时使用 | 可选 |
| `servers_config.json` | MCP 服务配置 | 配置火车票、高德地图、黄历、航班等工具服务 | 必填 |

API Key 获取入口：

- DeepSeek: `https://platform.deepseek.com/`
- DashScope / 阿里云百炼: `https://dashscope.aliyun.com/`
- LangSmith: `https://smith.langchain.com/`

### 环境变量

复制环境变量模板：

```bash
cp src/aggentic_RAG/.env.example src/aggentic_RAG/.env
```

编辑 `src/aggentic_RAG/.env`：

```bash
DEEPSEEK_API_KEY=sk-your-deepseek-api-key
DASHSCOPE_API_KEY=sk-your-dashscope-api-key
LANGCHAIN_TRACING_V2=false
MCP_CONFIG_PATH=travel_agent/config/servers_config.json
CHROMA_PERSIST_DIR=./data/travel_vectordb
```

`.env` 包含敏感密钥，已经被 `.gitignore` 和 `.dockerignore` 忽略，不要提交到 GitHub，也不要打进 Docker 镜像。

### MCP 服务器配置

复制 MCP 配置模板：

```bash
cp src/aggentic_RAG/travel_agent/config/servers_config.json.example \
   src/aggentic_RAG/travel_agent/config/servers_config.json
```

然后把里面的占位 URL 替换为真实的 MCP SSE 地址。项目当前会使用这些服务器名称，名称需要保持一致：

| MCP 服务器名称 | 用途 | 主要工具 | 是否建议配置 |
|----------------|------|----------|--------------|
| `12306 Server` | 火车票、车站码、车次路线查询 | `get-tickets`, `get-stations-code-in-city` | 必需 |
| `Gaode Server` | 高德地图 POI、酒店、天气、地理编码、驾车路线 | `maps_text_search`, `maps_weather`, `maps_geo`, `maps_direction_driving` | 必需 |
| `bazi Server` | 黄历、农历、宜忌信息 | `getChineseCalendar` | 建议配置 |
| `flight Server` | 国内航班价格与时刻表 | `search_flight` | 建议配置 |
| `biying Server` | 搜索最新旅游资讯 | `bing_search`, `crawl_webpage` | 可选 |

示例结构：

```json
{
  "mcp_servers": [
    {
      "name": "12306 Server",
      "url": "https://your-12306-mcp-server-url/sse"
    },
    {
      "name": "Gaode Server",
      "url": "https://your-gaode-mcp-server-url/sse"
    }
  ]
}
```

`servers_config.json` 可能包含真实服务地址，默认也不会提交到 GitHub。仓库只保留 `servers_config.json.example` 模板。

## 快速开始

### 1. 安装依赖

```bash
# 后端
pip install -r src/aggentic_RAG/requirements.txt

# 前端
cd src/frontend && npm install
```

### 2. 配置环境变量和 MCP

```bash
cp src/aggentic_RAG/.env.example src/aggentic_RAG/.env
cp src/aggentic_RAG/travel_agent/config/servers_config.json.example \
   src/aggentic_RAG/travel_agent/config/servers_config.json
```

然后按照“运行前准备”填写 API Key 和 MCP SSE 地址。

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

## Docker 部署

### 本地 Docker 运行

```bash
docker compose up -d --build
```

访问：

- 前端：`http://localhost:8080`
- 后端健康检查：`http://localhost:8000/api/health`

### 云服务器部署

本地构建并打包 amd64 镜像：

```bash
chmod +x build-images.sh deploy.sh
./build-images.sh
```

上传到服务器：

```bash
SERVER_IP=你的服务器IP
ssh root@$SERVER_IP "mkdir -p /opt/cs599"
scp cs599-backend.tar cs599-frontend.tar docker-compose.prod.yml deploy.sh root@$SERVER_IP:/opt/cs599/
scp src/aggentic_RAG/travel_agent/config/servers_config.json root@$SERVER_IP:/opt/cs599/
```

服务器启动：

```bash
cd /opt/cs599
chmod +x deploy.sh
./deploy.sh
```

生产环境只需要开放 `80/tcp`；后端 `8000` 默认只绑定服务器本机，由 nginx 反向代理 `/api`。

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

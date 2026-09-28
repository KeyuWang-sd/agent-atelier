<div align="center">

# Caker

**跑在本机的 Agent Skills 助手 —— LangGraph 驱动的对话式 Agent 运行时**

Python 3.11+ · FastAPI · LangGraph · PostgreSQL/pgvector · Chroma

[功能](#功能) · [架构](#架构) · [快速开始](#快速开始) · [文档](#文档) · [测试](#测试)

</div>

---

## 项目介绍

Caker 是一个跑在本机的 **Agent Skills 助手**：浏览器里对话，Agent 在**当前会话工作区**里读文件、写结果、按技能执行任务。每个对话有独立工作区（`user` + `session` 双层隔离），上传进 `data/uploads/`，工具只在该目录内读写，不碰你电脑上的其它路径。

LangGraph 负责流程调度，FastAPI 提供服务，自带 Web 聊天界面，数据落在本机 `var/` 与 PostgreSQL——不绑任何云厂商，一条 `uvicorn` 即可起。

## 功能

- **对话**：多轮续聊，SSE 流式输出；长对话上下文自动压缩
- **带文件问答**：网页上传 → Agent 用 `read` 等工具阅读、总结、改写
- **工作区工具**：会话内读写、搜索、编辑，产出写到 `outputs/`
- **技能系统**：`skills/` 下 11 个内置技能按需加载（`call_skill`），如联网搜索、SQLite 查询、深度调研、HTML 报告生成、记忆存取
- **执行环境工作台（CEER V2）**：沙箱页 + Web 终端（`docker exec`），Agent 可在隔离容器里跑代码
- **记忆（可选）**：配置 Embedding 后跨会话语义召回，用户级隔离
- **工作区面板**：查看已上传文件、复制路径、本机打开文件夹（Win+WSL / Mac / Linux）

## 架构

```
                        ┌──────────────────────────────────────────┐
                        │              Web UI (原生 JS)             │
                        │   聊天 / 工作区面板 / 沙箱终端 / 会话管理    │
                        └───────────────────┬──────────────────────┘
                                            │ SSE / REST
                        ┌───────────────────▼──────────────────────┐
                        │            FastAPI (app/api)             │
                        └───────────────────┬──────────────────────┘
                                            │
┌───────────────┐   ┌─────────────────────▼───────────────────────┐
│  skills/      │   │           LangGraph StateGraph (runtime)     │
│  11个技能      ├───►  start → inject(system/user/memory) → llm     │
│  按需加载      │   │    → tools → apply_result_set → (compact) →  │
└───────────────┘   │    end，条件路由循环                          │
                    └──────┬──────────────┬──────────────┬─────────┘
                           │              │              │
                 ┌─────────▼───┐  ┌───────▼──────┐  ┌────▼─────────┐
                 │ tools/      │  │ mempalace/   │  │ execution/   │
                 │ 12个原子工具 │  │ Chroma向     │  │ Docker沙箱   │
                 │ 注册中心+适配│  │ 量记忆(可选)  │  │ Web终端      │
                 └─────────┬───┘  └───────┬──────┘  └────┬─────────┘
                           │              │              │
                    ┌──────▼──────────────▼──────────────▼─────────┐
                    │   workspace/ 会话沙箱 (var/workspace)         │
                    │   PostgreSQL: LangGraph checkpoint + pgvector │
                    └───────────────────────────────────────────────┘
```

**分层设计**：流程在 LangGraph 图里，原子能力在工具（统一注册中心 + LangChain 适配器），业务说明在技能（Markdown + 脚本，按需注入）——三层各自独立演进。

## 快速开始

```bash
git clone https://github.com/KeyuWang-sd/cakertest.git
cd cakertest
cp .env.example .env          # 填写 LLM_* 与 PG_DSN
docker compose up -d postgres
pip install -e .
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

打开 **http://127.0.0.1:8000/** · 详细说明见 [docs/user-guide.md](docs/user-guide.md)

## 测试

```bash
pytest            # 31 个测试文件 / 109 条单元测试
```

## 文档

| 文档 | 说明 |
|------|------|
| [docs/user-guide.md](docs/user-guide.md) | 界面与工作区使用 |
| [docs/execution-runtime-v2.md](docs/execution-runtime-v2.md) | CEER 沙箱工作台 + 终端 |
| [docs/milestones.md](docs/milestones.md) | 里程碑实现与验收记录 |
| [docs/agent_skills_build_guide.md](docs/agent_skills_build_guide.md) | 从零跟写引擎实现 |
| [AGENTS.md](AGENTS.md) | AI 协作开发约定 |
| [system_prompt.md](system_prompt.md) | Agent 系统提示词 |

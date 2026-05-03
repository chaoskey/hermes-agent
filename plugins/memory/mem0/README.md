# Mem0 Memory Provider

Server-side LLM fact extraction with semantic search, reranking, and automatic deduplication.

## Requirements

- `pip install mem0ai`
- Mem0 API key（当前实现中必填，官方/本地模式都需要）
- 若使用本地服务，需提供可访问的 REST API 地址（例如 `http://localhost:8888`）

## Setup

```bash
hermes memory setup    # select "mem0"
```

说明：
- 当提示 `Mem0 API key (current: ...xxxx):` 时，若当前已存在 key，可直接回车保留原值。
- 仅当当前没有 key 且输入为空时，才会提示 `API key is required.`。

或手动配置：
```bash
hermes config set memory.provider mem0
echo "MEM0_API_KEY=your-key" >> "$HERMES_HOME/.env"
# 如需本地服务，添加：
echo "MEM0_ENDPOINT=http://localhost:8888" >> "$HERMES_HOME/.env"
echo "MEM0_LOCAL=true" >> "$HERMES_HOME/.env"
echo "MEM0_SERVICE=local" >> "$HERMES_HOME/.env"
```

## Config

Config file: `$HERMES_HOME/mem0.json`

支持以下配置（环境变量或 mem0.json）：

| Key / Env Var | Default | Description |
|---------------|---------|-------------|
| `api_key` / `MEM0_API_KEY` | (none) | Mem0 API key（当前实现要求提供） |
| `service` / `MEM0_SERVICE` | `official`（若 `MEM0_LOCAL=true` 则推导为 `local`） | 服务模式：`official` 或 `local` |
| `endpoint` / `MEM0_ENDPOINT` | (none) | 本地模式下的 Mem0 REST API 地址（setup 默认提示为 `http://localhost:8888`） |
| `local_client` / `MEM0_LOCAL` | `false` | 是否启用本地 REST 客户端（`true`=本地，`false`=官方） |
| `user_id` / `MEM0_USER_ID` | `hermes-user` | User identifier on Mem0 |
| `agent_id` / `MEM0_AGENT_ID` | `hermes` | Agent identifier |
| `rerank` | `true` | Enable reranking for recall |

> 插件不再根据 endpoint 自动切换客户端。
> 仅当 `MEM0_LOCAL=true`（或 `mem0.json` 中 `local_client=true`）时才使用 `LocalMemoryClient`。
> 本地模式下若未配置 endpoint，将无法初始化客户端。

## Tools

| Tool | Description |
|------|-------------|
| `mem0_profile` | All stored memories about the user |
| `mem0_search` | Semantic search with optional reranking |
| `mem0_conclude` | Store a fact verbatim (no LLM extraction) |

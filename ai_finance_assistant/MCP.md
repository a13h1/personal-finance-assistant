# Model Context Protocol (MCP) Integration

This document describes the MCP-compatible HTTP tool endpoints exposed by the AI Finance Assistant for Claude Desktop integration.

## Overview

The MCP server exposes one endpoint per finance agent tool. Each endpoint accepts a JSON request with `query`, optional `user_id` and `session_id`, and returns a structured JSON response.

## Available endpoints

- `GET /mcp/tools`
- `POST /mcp/finance_qa`
- `POST /mcp/portfolio`
- `POST /mcp/market`
- `POST /mcp/goal_planning`
- `POST /mcp/news`
- `POST /mcp/tax`

## Request format

```json
{
  "query": "Tell me how to reduce taxes on capital gains.",
  "user_id": "user-123",
  "session_id": "session-abc",
  "context": {
    "history": [],
    "portfolio": null,
    "profile": {
      "risk_tolerance": "moderate",
      "investment_horizon": "medium",
      "experience_level": "beginner"
    }
  }
}
```

- `query`: the user question or prompt.
- `user_id`: optional account identifier for future login/account flow.
- `session_id`: optional session identifier used to persist conversation state.
- `context`: optional extra context; the server derives history and profile from persisted state when available.

## Response format

```json
{
  "response": "Here is a high-level explanation...",
  "agent": "tax",
  "status": "ok",
  "error": null,
  "session_id": "session-abc"
}
```

- `response`: the agent answer.
- `agent`: the tool/agent that handled the request.
- `status`: `ok` or `error`.
- `error`: optional error message.
- `session_id`: the canonical session identifier used for persistence.

## Tool descriptions

- `finance_qa`: general financial education, concept explanations, and broad guidance.
- `portfolio`: portfolio analysis, diversification recommendations, and holdings review.
- `market`: market data, stock quotes, and price inquiries.
- `goal_planning`: financial goal planning and savings guidance.
- `news`: financial news summarization and context.
- `tax`: tax education and high-level tax-related guidance.

## Running the MCP server

From `ai_finance_assistant` run:

```bash
uvicorn src.mcp_server:app --reload --port 8000
```

The server loads the same `config.yaml` and agent definitions as the main application.

## Notes

- Risk profile persistence is supported via `session_id` and `user_id` mapping.
- The server stores conversation history and portfolio data in the same session backend used by the Streamlit app.
- Each tool endpoint is intentionally separate to support Claude Desktop tool-based routing.

# AI Finance Assistant — Architecture

## Overview

A multi-agent financial education chatbot built with LangGraph, OpenAI, FAISS, and Streamlit.
Six specialized agents handle distinct financial domains. A keyword-based LangGraph router
dispatches each query to the right agent, which combines LLM reasoning with either RAG
retrieval (knowledge base) or live market data (yFinance).

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User's Browser                              │
└─────────────────────────────┬───────────────────────────────────────┘
                              │ HTTP (Streamlit)
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   Streamlit Web App  (src/web_app/app.py)           │
│                                                                     │
│   ┌─────────────────┬───────────────────┬───────────────────────┐  │
│   │   💬 Chat Tab   │  📊 Portfolio Tab │    📈 Market Tab      │  │
│   │                 │                   │                       │  │
│   │ • Chat history  │ • Add/remove      │ • Live index quotes   │  │
│   │ • Chat input    │   holdings form   │   (S&P, Dow, NASDAQ,  │  │
│   │ • Agent label   │ • Metrics: value, │   VIX)                │  │
│   │   on responses  │   cost, gain/loss │ • Stock symbol lookup │  │
│   │                 │ • Holdings table  │ • Candlestick chart   │  │
│   │                 │ • Sector pie chart│   (3-month history)   │  │
│   │                 │ • AI analysis btn │                       │  │
│   └─────────────────┴───────────────────┴───────────────────────┘  │
│                                                                     │
│   Session State (st.session_state)                                  │
│   • session_id: UUID (per browser tab)                              │
│   • messages[]: chat history for display                            │
│   • portfolio_holdings[]: {symbol, shares, avg_cost}                │
│                                                                     │
│   @st.cache_resource → single FinanceOrchestrator instance          │
└─────────────────────────────┬───────────────────────────────────────┘
                              │ orchestrator.process_query(query, session_id)
                              │ orchestrator.market_data.analyze_portfolio(holdings)
                              │ orchestrator.market_data.get_market_indices()
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│              FinanceOrchestrator  (src/workflow/orchestrator.py)    │
│                                                                     │
│  Startup (once):                                                    │
│  1. load_dotenv(.env) → OPENAI_API_KEY                              │
│  2. Parse config.yaml                                               │
│  3. Instantiate LLMInterface, SessionManager, MarketDataService     │
│  4. Build or load FAISS index from knowledge_base/                  │
│  5. Construct RAGRetriever                                          │
│  6. Instantiate all 6 agents                                        │
│  7. Compile LangGraph workflow                                      │
│                                                                     │
│  Per query:                                                         │
│  • Add user message to SessionManager                               │
│  • Fetch last 10 history turns + portfolio + profile from Session   │
│  • Build AgentState, invoke LangGraph workflow                      │
│  • Add assistant response to SessionManager                         │
│  • Return {response, agent}                                         │
└─────────────────────────────┬───────────────────────────────────────┘
                              │ workflow.invoke(AgentState)
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│               LangGraph Workflow  (src/workflow/router.py)          │
│                                                                     │
│  AgentState (TypedDict):                                            │
│  { query, intent, response, history[], portfolio, profile, error }  │
│                                                                     │
│                     ┌─────────────────┐                            │
│                     │ classify_intent │                            │
│                     │  (keyword match)│                            │
│                     └────────┬────────┘                            │
│                              │                                     │
│         ┌────────┬───────────┼───────────┬────────┬────────┐      │
│         ▼        ▼           ▼           ▼        ▼        ▼      │
│    finance_qa portfolio   market   goal_planning  news     tax     │
│      node     node        node       node        node     node     │
│         │        │           │           │        │        │      │
│         └────────┴───────────┴───────────┴────────┴────────┘      │
│                              │ END                                 │
│                                                                     │
│  Intent routing (keyword-based):                                    │
│  "tax","ira","roth","401k","capital gains"  → tax                  │
│  "portfolio","holding","diversif","my investment" → portfolio       │
│  "price","market","quote","trading"         → market               │
│  "news","headline","earnings","merger"      → news                 │
│  "goal","retire","save for","afford"        → goal_planning        │
│  (default)                                  → finance_qa           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Agent Layer

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Six Specialized Agents                         │
│                    (src/agents/*.py — all extend BaseAgent)         │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  FinanceQAAgent          │  TaxAgent                         │  │
│  │  • RAG retrieval (k=3)   │  • RAG retrieval (k=3)            │  │
│  │  • Appends source list   │  • Appends source list            │  │
│  │  • Supports multi-turn   │  • Supports multi-turn            │  │
│  │    (generate_with_history│    (generate_with_history)        │  │
│  ├──────────────────────────┼───────────────────────────────────┤  │
│  │  PortfolioAgent          │  MarketAgent                      │  │
│  │  • Reads portfolio from  │  • Regex-extracts ticker symbols  │  │
│  │    context (set via UI)  │    from query (e.g. AAPL, MSFT)   │  │
│  │  • Calls analyze_        │  • Fetches market indices         │  │
│  │    portfolio() for live  │  • Fetches per-symbol quotes      │  │
│  │    prices, gain/loss,    │  • Passes data to LLM for         │  │
│  │    sector breakdown      │    narrative analysis             │  │
│  ├──────────────────────────┼───────────────────────────────────┤  │
│  │  GoalPlanningAgent       │  NewsAgent                        │  │
│  │  • Pure LLM reasoning    │  • Calls yfinance .news for up    │  │
│  │  • Injects user profile  │    to 2 symbols or SPY/QQQ        │  │
│  │    (risk tolerance,      │  • Formats headlines + publisher  │  │
│  │    horizon, experience)  │  • Passes to LLM for synthesis    │  │
│  └──────────────────────────┴───────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Shared Services

```
┌──────────────────────────┐   ┌──────────────────────────────────────┐
│     LLMInterface         │   │         RAGRetriever                 │
│  (src/core/llm_interface)│   │         (src/rag/retriever.py)       │
│                          │   │                                      │
│  Model: gpt-4o-mini      │   │  retrieve(query, k=3) → str          │
│  Temp:  0.3              │   │  retrieve_with_sources() → str, list │
│  Max tokens: 2048        │   │         │                            │
│                          │   │         ▼                            │
│  generate(msg, sys)      │   │  FinancialVectorStore                │
│  generate_with_history() │   │  (src/rag/vector_store.py)           │
│         │                │   │                                      │
│         ▼                │   │  Embeddings: all-MiniLM-L6-v2        │
│  ChatOpenAI (LangChain)  │   │  (HuggingFaceEmbeddings)             │
│         │                │   │  Chunk: 500 chars / 50 overlap       │
│         ▼                │   │  Index:  FAISS (saved to disk)       │
│  OpenAI API              │   │         │                            │
│  api.openai.com          │   │         ▼                            │
└──────────────────────────┘   │  18 Markdown articles                │
                               │  (src/data/knowledge_base/)          │
                               └──────────────────────────────────────┘

┌──────────────────────────┐   ┌──────────────────────────────────────┐
│    SessionManager        │   │        MarketDataService             │
│  (src/core/session_mgr)  │   │        (src/utils/market_data.py)    │
│                          │   │                                      │
│  SQLAlchemy ORM          │   │  TTL cache (300s)                    │
│  Write-through cache     │   │                                      │
│                          │   │  get_quote(symbol)                   │
│  Per session:            │   │  get_historical(symbol, period)      │
│  • UserProfile           │   │  get_multiple_quotes(symbols[])      │
│    - risk_tolerance      │   │  get_market_indices()                │
│    - investment_horizon  │   │    → S&P 500, Dow Jones,             │
│    - experience_level    │   │       NASDAQ, VIX                    │
│  • ConversationTurn[]    │   │  get_news(symbol)                    │
│    - role, content,      │   │  analyze_portfolio(holdings[])       │
│      agent, timestamp    │   │    → value, cost, gain/loss,         │
│  • portfolio dict        │   │       sector allocation              │
│                          │   │         │                            │
│  get_history(n=10)       │   │         ▼                            │
│  update_portfolio()      │   │  yfinance  (yf.Ticker)               │
│  update_profile()        │   │  Free, no API key required           │
│  list_users()            │   │                                      │
│  delete_user()           │   │                                      │
└──────────┬───────────────┘   └──────────────────────────────────────┘
           │ DATABASE_URL env var
           │ (PostgreSQL in prod/QA, SQLite locally)
           ▼
  ┌─────────────────────────────────────────────────────┐
  │         Persistence Layer  (SQLAlchemy 2.0)         │
  │                                                     │
  │  Production / QA → AWS RDS PostgreSQL t3.micro      │
  │  Local dev       → SQLite  data/sessions.db         │
  │                                                     │
  │  pool_pre_ping=True  — auto-recovers stale RDS      │
  │  connections after idle timeout                     │
  └─────────────────────────────────────────────────────┘
```

---

## Persistence Layer

```
                    DATABASE_URL env var
                           │
           ┌───────────────┴────────────────┐
           │ PostgreSQL (RDS)               │ SQLite
           │ DATABASE_URL=postgresql://...  │ (default, no env var needed)
           ▼                               ▼
  AWS RDS t3.micro                  data/sessions.db
  Single instance (QA)              Local development
  Multi-AZ (production)
```

### RDS Schema

```
┌────────────────────────────────────────────────────────────────────┐
│                         users                                      │
├──────────────────┬──────────────┬───────────────────────────────── ┤
│ user_id (PK)     │ VARCHAR(36)  │ UUID assigned per browser session │
│ risk_tolerance   │ VARCHAR(20)  │ conservative | moderate | aggressive│
│ investment_horizon│ VARCHAR(20) │ short | medium | long             │
│ experience_level │ VARCHAR(20)  │ beginner | intermediate | advanced │
│ created_at       │ FLOAT        │ Unix timestamp                    │
│ updated_at       │ FLOAT        │ Unix timestamp                    │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│                    conversation_history                            │
├──────────────────┬──────────────┬──────────────────────────────────┤
│ id (PK)          │ INTEGER      │ Auto-increment                   │
│ user_id          │ VARCHAR(36)  │ FK → users.user_id  (indexed)    │
│ role             │ VARCHAR(10)  │ "user" | "assistant"             │
│ content          │ TEXT         │ Full message text                │
│ agent            │ VARCHAR(50)  │ Which agent produced the response │
│ timestamp        │ FLOAT        │ Unix timestamp                   │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│                    portfolio_holdings                              │
├──────────────────┬──────────────┬──────────────────────────────────┤
│ user_id (PK)     │ VARCHAR(36)  │ FK → users.user_id               │
│ portfolio_json   │ TEXT         │ JSON: [{symbol, shares, avg_cost}]│
│ updated_at       │ FLOAT        │ Unix timestamp                   │
└────────────────────────────────────────────────────────────────────┘
```

### How the SessionManager Works

```
Request comes in with session_id
          │
          ▼
  _cache hit?  ──yes──▶  return cached session (no DB round-trip)
          │
         no
          │
          ▼
  DB query: SELECT user, last 100 history rows, portfolio
          │
     user exists? ──no──▶  INSERT new user row (defaults applied)
          │
         yes
          │
          ▼
  Hydrate UserProfile + ConversationTurn[] + portfolio dict
  Store in _cache[session_id]
          │
          ▼
  Return session dict

On add_message() / update_portfolio() / update_profile():
  • Update _cache immediately (fast path)
  • Write-through to DB in same call (durable)
```

### User Management API

```python
sm = SessionManager(database_url=os.getenv("DATABASE_URL"))

sm.list_users()                     # → List[UserProfile]
sm.get_profile(session_id)          # → UserProfile
sm.update_profile(session_id,       # update any field
    risk_tolerance="aggressive",
    experience_level="intermediate")
sm.delete_user(session_id)          # removes user + history + portfolio
```

### Connecting to RDS

```bash
# Set in .env (never commit this file)
DATABASE_URL=postgresql://username:password@your-rds-endpoint.amazonaws.com:5432/finance_db

# Tables are created automatically on first startup (SQLAlchemy create_all)
# No migration tool required for the current schema
```

---

## Data Flow — Single Query

```
User types: "What is the P/E ratio of AAPL?"
                    │
                    ▼
         app.py: process_query()
                    │
                    ▼
         SessionManager.add_message("user", ...)
         SessionManager.get_history(last_n=10)
                    │
                    ▼
         LangGraph: classify_intent()
         → matches "price" keyword → intent = "market"
                    │
                    ▼
         MarketAgent.process(query, context)
         │
         ├── _extract_symbols("AAPL") → ["AAPL"]
         ├── market_data.get_market_indices() → {S&P, Dow, NASDAQ, VIX}
         ├── market_data.get_quote("AAPL")  → {price, change_pct, pe_ratio, ...}
         │
         └── llm.generate(prompt_with_market_data, system_prompt)
                    │
                    ▼
             OpenAI gpt-4o-mini
                    │
                    ▼
         SessionManager.add_message("assistant", response, agent="market")
                    │
                    ▼
         app.py: render response + "Agent: Market" caption
```

---

## File Structure

```
ai_finance_assistant/
├── config.yaml                    # LLM model, RAG settings, agent prompts, cache TTL
├── requirements.txt
├── run.sh                         # ./run.sh — launches app from any directory
├── .env                           # OPENAI_API_KEY (not committed)
├── .env.example                   # Template
│
├── src/
│   ├── web_app/
│   │   └── app.py                 # Streamlit UI — 3 tabs, session init, rendering
│   │
│   ├── workflow/
│   │   ├── orchestrator.py        # FinanceOrchestrator — wires all components
│   │   └── router.py              # LangGraph StateGraph — intent classify + 6 nodes
│   │
│   ├── agents/
│   │   ├── base_agent.py          # ABC: __init__(llm, system_prompt, name), process()
│   │   ├── finance_qa_agent.py    # RAG + multi-turn LLM
│   │   ├── portfolio_agent.py     # Live portfolio analysis + LLM
│   │   ├── market_agent.py        # Symbol extraction + live quotes + LLM
│   │   ├── goal_planning_agent.py # Profile-aware LLM reasoning
│   │   ├── news_agent.py          # yFinance news headlines + LLM synthesis
│   │   └── tax_agent.py           # RAG + multi-turn LLM
│   │
│   ├── core/
│   │   ├── llm_interface.py       # ChatOpenAI wrapper (generate / generate_with_history)
│   │   └── session_manager.py     # In-memory sessions (profile, history, portfolio)
│   │
│   ├── rag/
│   │   ├── vector_store.py        # FAISS build/save/load, HuggingFace embeddings
│   │   └── retriever.py           # retrieve() / retrieve_with_sources()
│   │
│   ├── utils/
│   │   ├── market_data.py         # yFinance wrapper with TTL cache
│   │   └── error_handler.py       # @with_fallback decorator
│   │
│   └── data/
│       └── knowledge_base/        # 18 .md articles (investing, tax, retirement, etc.)
│
├── data/
│   └── faiss_index/               # Built on first run, loaded on subsequent runs
│
└── tests/
    ├── test_agents.py             # Intent routing + agent unit tests (16 tests)
    └── test_rag.py                # Vector store build/search tests (6 tests)
```

---

## Configuration (config.yaml)

```
llm:
  provider: openai
  model:    gpt-4o-mini          ← cheapest capable OpenAI model
  temp:     0.3
  tokens:   2048

vector_db:
  embedding: all-MiniLM-L6-v2   ← local HuggingFace model, no API needed
  chunk:     500 chars / 50 overlap
  index:     data/faiss_index/

cache:
  ttl:  300s                     ← market data cached for 5 minutes
  size: 100 entries

agents:                          ← per-agent system prompts defined here
  finance_qa, portfolio, market, goal_planning, news, tax
```

---

## External Dependencies

```
┌─────────────────────────────────────────────────────────────┐
│                  External Services                          │
├───────────────────────┬─────────────────────────────────────┤
│ OpenAI API            │ All LLM inference                   │
│ api.openai.com        │ Model: gpt-4o-mini                  │
│ Requires API key      │ Used by: all 6 agents               │
├───────────────────────┼─────────────────────────────────────┤
│ yFinance              │ Stock quotes, historical prices,    │
│ (Python library)      │ market indices, company news        │
│ Free, no key needed   │ Used by: market, portfolio, news    │
├───────────────────────┼─────────────────────────────────────┤
│ HuggingFace Hub       │ Download all-MiniLM-L6-v2 model     │
│ (first run only)      │ ~90MB, cached locally after         │
│ Free                  │ Used by: RAG embedding              │
├───────────────────────┼─────────────────────────────────────┤
│ AWS RDS PostgreSQL    │ Persistent user profiles,           │
│ t3.micro (QA)         │ conversation history, portfolios    │
│ Requires DATABASE_URL │ SQLite used locally if unset        │
└───────────────────────┴─────────────────────────────────────┘
```

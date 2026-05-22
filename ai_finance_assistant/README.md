# AI Finance Assistant

A production-ready multi-agent AI application for personal finance education, built with LangGraph, LangChain, and Claude. The system routes user queries to specialized agents covering portfolio analysis, market data, tax education, financial goal planning, and general finance Q&A.

## Architecture

```
User Query
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│                   Streamlit Web App                      │
│         (Chat Tab | Portfolio Tab | Market Tab)          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              FinanceOrchestrator                         │
│  (LangGraph workflow + session management)               │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                Intent Classifier                         │
│         (Keyword-based LangGraph router)                 │
└──────┬──────┬──────┬──────┬──────┬───────────────────--─┘
       │      │      │      │      │
       ▼      ▼      ▼      ▼      ▼
   Finance  Portfolio Market Goal  News    Tax
   Q&A      Agent    Agent  Agent  Agent  Agent
   Agent
       │                    │
       ▼                    ▼
   RAG System          yFinance API
  (FAISS + HF          (Market Data)
  Embeddings)
       │
       ▼
  Knowledge Base
  (18 MD Articles)
       │
       ▼
  Claude Haiku
  (LLM Responses)
```

## Agent Descriptions

| Agent | Trigger Keywords | Capabilities |
|-------|-----------------|--------------|
| Finance Q&A | (default) | General finance education with RAG retrieval |
| Portfolio | portfolio, holdings, diversif | Portfolio analysis with live market data |
| Market | price, market, quote, stock price | Real-time market data and analysis |
| Goal Planning | goal, retire, save for, plan | Financial goal planning and math |
| News | news, headline, earnings, merger | Financial news synthesis |
| Tax | tax, capital gains, IRA, 401k | Tax education with RAG retrieval |

## Tech Stack

- **Orchestration:** LangGraph (state machine workflow)
- **LLM:** Claude Haiku (`claude-haiku-4-5-20251001`) via LangChain-Anthropic
- **RAG:** FAISS + HuggingFace `all-MiniLM-L6-v2` sentence transformer (runs locally, no server)
- **Market Data:** yFinance (free, no API key required)
- **UI:** Streamlit with Plotly charts
- **Session:** In-memory session manager with user profile tracking

## Project Structure

```
ai_finance_assistant/
├── src/
│   ├── agents/            # 6 specialized agents
│   ├── core/              # LLM interface and session manager
│   ├── data/knowledge_base/  # 18 financial education articles
│   ├── rag/               # FAISS vector store and retriever
│   ├── utils/             # Market data service and error handling
│   ├── web_app/           # Streamlit application
│   └── workflow/          # LangGraph router and orchestrator
├── tests/                 # pytest test suite
├── config.yaml            # Configuration for all components
├── requirements.txt
└── .env.example
```

## Setup

### Prerequisites

- Python 3.10+
- An Anthropic API key

### Installation

```bash
# Navigate to the project directory
cd ai_finance_assistant

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your Anthropic API key:
# ANTHROPIC_API_KEY=your_actual_key_here
```

### First Run (FAISS Index Building)

On the first run, the application automatically builds the FAISS vector index from the knowledge base articles. This takes 30-60 seconds and downloads the sentence transformer model (~90MB). Subsequent runs load the pre-built index instantly.

## Running the Application

From the project root (`personal-finance-agent/`):

```bash
streamlit run ai_finance_assistant/src/web_app/app.py
```

The app will open at `http://localhost:8501`.

Alternatively, from inside `ai_finance_assistant/`:

```bash
cd ai_finance_assistant
streamlit run src/web_app/app.py
```

## Running Tests

```bash
cd ai_finance_assistant
python -m pytest tests/ -v
```

**Note:** The RAG tests (`test_rag.py`) download the sentence transformer model on first run. They require an internet connection initially but run offline thereafter.

## Usage Examples

### Chat Tab

Ask any financial question:
- "What is the difference between a Roth IRA and a Traditional IRA?"
- "How does dollar cost averaging work?"
- "Explain capital gains tax to me"
- "What is the current price of AAPL?"
- "How much do I need to save to retire at 60?"

### Portfolio Tab

1. Enter stock holdings using the form (symbol, shares, average cost)
2. View live portfolio value, gain/loss, and sector allocation pie chart
3. Click "Get AI Portfolio Analysis" for personalized recommendations

### Market Tab

1. View real-time S&P 500, Dow Jones, NASDAQ, and VIX levels
2. Enter any stock ticker for a detailed quote and 3-month candlestick chart

## Configuration

Edit `config.yaml` to adjust:
- LLM model, temperature, and token limits
- FAISS chunk size and overlap for RAG
- Per-agent system prompts
- Cache TTL for market data

## Troubleshooting

**"ANTHROPIC_API_KEY not set"**
Make sure your `.env` file exists in `ai_finance_assistant/` and contains a valid API key.

**"No module named 'src'"**
Run the app from the `personal-finance-agent/` root directory using the full path:
`streamlit run ai_finance_assistant/src/web_app/app.py`

**"Could not fetch data for [SYMBOL]"**
yFinance may have temporary rate limits. Try again in a few minutes.

**First run is slow**
The sentence transformer model downloads on first use (~90MB). Subsequent runs are fast because the FAISS index is cached.

**Import errors with langchain-community**
Ensure you have the latest versions: `pip install --upgrade langchain-community langchain-anthropic`

## Disclaimer

This application is for educational purposes only. Nothing in this application constitutes financial advice. Always consult a qualified financial advisor before making investment decisions.

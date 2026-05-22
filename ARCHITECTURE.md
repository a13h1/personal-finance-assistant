# AI Finance Assistant - System Architecture

## 1. Overall System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          USER INTERFACE LAYER                               │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    Streamlit Web Application                         │   │
│  │  ┌─────────────────┬──────────────────┬────────────────────────────┐ │   │
│  │  │ Chat Interface  │ Portfolio Dash   │ Market Overview Dashboard  │ │   │
│  │  │ (Multi-turn)    │ (Visualizations) │ (Real-time Data)          │ │   │
│  │  └─────────────────┴──────────────────┴────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└────────────┬─────────────────────────────────────────────────────────────────┘
             │ User Query + Context
             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      REQUEST ORCHESTRATION LAYER                            │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │              Workflow Router (LangGraph)                            │   │
│  │  • Intent Classification                                           │   │
│  │  • Agent Selection & Routing                                       │   │
│  │  • Multi-Agent Coordination                                        │   │
│  │  • State Management & Context Tracking                             │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└────────────┬─────────────────────────────────────────────────────────────────┘
             │
    ┌────────┴────────┬────────────────┬──────────────────┬──────────────┬──────────────┐
    │                 │                │                  │              │              │
    ▼                 ▼                ▼                  ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐
│   Finance    │ │  Portfolio   │ │    Market    │ │    Goal    │ │    News    │ │     Tax    │
│   Q&A        │ │   Analysis   │ │   Analysis   │ │  Planning  │ │ Synthesizer│ │ Education  │
│   Agent      │ │   Agent      │ │   Agent      │ │   Agent    │ │   Agent    │ │   Agent    │
│              │ │              │ │              │ │            │ │            │ │            │
│  Domain:     │ │  Domain:     │ │  Domain:     │ │ Domain:    │ │ Domain:    │ │ Domain:    │
│  • Concepts  │ │  • Holdings  │ │  • Trends    │ │ • Planning │ │ • News     │ │ • Taxes    │
│  • Basics    │ │  • Metrics   │ │  • Analysis  │ │ • Risk     │ │ • Context  │ │ • Accounts │
│  • Education │ │  • Strategies│ │  • Quotes    │ │ • Returns  │ │ • Synthesis│ │ • Strategy │
└──────────────┘ └──────────────┘ └──────────────┘ └────────────┘ └────────────┘ └────────────┘
    │                 │                │                  │              │              │
    └────────────────┬┴────────────────┬──────────────────┴──────────────┴──────────────┘
                     │ Agent Responses
                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     SHARED SERVICES LAYER                                   │
│                                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │ LLM Interface    │  │   Vector DB      │  │  API Manager             │  │
│  │ (Claude/Gemini)  │  │  (FAISS/Chroma)  │  │  (Rate Limiting/Cache)   │  │
│  │ • Prompt Mgmt    │  │  • Indexing      │  │  • Alpha Vantage         │  │
│  │ • Response Gen   │  │  • Search        │  │  • yFinance              │  │
│  │ • Token Counting │  │  • Retrieval     │  │  • Sentiment Analysis    │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────────────┘  │
│                                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │ Session Manager  │  │  Logging/Monitor │  │  Error Handler           │  │
│  │ • User Profiles  │  │  • Metrics       │  │  • Fallback Logic        │  │
│  │ • History        │  │  • Tracing       │  │  • Graceful Degradation  │  │
│  │ • Preferences    │  │  • Analytics     │  │  • Retry Logic           │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────────────┘  │
└────────────┬─────────────────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DATA & EXTERNAL SERVICES LAYER                           │
│                                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │ Knowledge Base   │  │  Market Data     │  │  External APIs           │  │
│  │ • 50-100 Articles│  │  • Cached Quotes │  │  • News Sources          │  │
│  │ • Embeddings     │  │  • Historical    │  │  • Data Providers        │  │
│  │ • Categories     │  │  • Trends        │  │  • Tax Resources         │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ External Data Sources: Alpha Vantage | yFinance | Financial News    │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Data Flow Diagram

```
                         USER INPUT
                            │
                            ▼
                  ┌──────────────────────┐
                  │  Input Validation    │
                  │  & Preprocessing     │
                  └──────────┬───────────┘
                             │
                             ▼
              ┌──────────────────────────────────┐
              │  Intent Classification           │
              │  (What is the user asking?)      │
              │  • Financial Education?          │
              │  • Portfolio Analysis?           │
              │  • Market Info?                  │
              │  • Goal Planning?                │
              │  • News/Context?                 │
              │  • Tax Question?                 │
              └────────────┬─────────────────────┘
                           │
                           ▼
              ┌──────────────────────────────────┐
              │  Route to Agent(s)               │
              │  (Single or Multi-Agent)         │
              └────────────┬─────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
      ┌────────────┐  ┌────────────┐  ┌────────────┐
      │  Agent 1   │  │  Agent 2   │  │  Agent N   │
      │  Process   │  │  Process   │  │  Process   │
      └─┬──────────┘  └─┬──────────┘  └─┬──────────┘
        │               │               │
        ├───────────────┼───────────────┤
        │               │               │
        └───┬───────────┴───────────────┘
            │
            ▼
    ┌───────────────────────────────┐
    │  RAG Retrieval (if needed)    │
    │  • Query Vector DB            │
    │  • Get Context Documents      │
    │  • Rank by Relevance          │
    └──────────┬────────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
    ▼                     ▼
┌────────────┐      ┌─────────────────┐
│ Knowledge  │      │  Market Data    │
│ Base (RAG) │      │  APIs           │
│            │      │  (Real-time)    │
└────────────┘      └─────────────────┘
    │                     │
    └──────────┬──────────┘
               │
               ▼
    ┌───────────────────────────────┐
    │  LLM Processing               │
    │  • Combine context            │
    │  • Generate response          │
    │  • Format output              │
    └──────────┬────────────────────┘
               │
               ▼
    ┌───────────────────────────────┐
    │  Response Assembly            │
    │  • Add citations              │
    │  • Include disclaimers        │
    │  • Format for UI              │
    └──────────┬────────────────────┘
               │
               ▼
    ┌───────────────────────────────┐
    │  State Update                 │
    │  • Save conversation          │
    │  • Update user profile        │
    │  • Log analytics              │
    └──────────┬────────────────────┘
               │
               ▼
              USER RESPONSE
```

---

## 3. Agent Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AGENT INTERFACE                             │
│  (Common pattern for all 6 agents)                                  │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
    ┌──────────────────────┐  ┌──────────────────────┐
    │  Input Processing    │  │  Context Retrieval   │
    │  • Parse query       │  │  • History lookup    │
    │  • Extract entities  │  │  • User profile      │
    │  • Determine scope   │  │  • Previous context  │
    └──────────┬───────────┘  └──────────┬───────────┘
               │                         │
               └────────────┬────────────┘
                            ▼
                  ┌────────────────────┐
                  │  Domain Logic      │
                  │  (Agent-specific)  │
                  │                    │
                  │  • Calculations    │
                  │  • Analysis        │
                  │  • Data Processing │
                  └────────────┬───────┘
                               │
                  ┌────────────┴────────────┐
                  ▼                         ▼
         ┌─────────────────┐      ┌─────────────────┐
         │  RAG Retrieval  │      │  API Calls      │
         │  (if needed)    │      │  (if needed)    │
         └────────┬────────┘      └────────┬────────┘
                  │                        │
                  └────────────┬───────────┘
                               ▼
                  ┌────────────────────────┐
                  │  Response Generation   │
                  │  • Prompt Assembly     │
                  │  • LLM Call            │
                  │  • Output Formatting   │
                  └────────────┬───────────┘
                               ▼
                  ┌────────────────────────┐
                  │  Response Enhancement  │
                  │  • Add citations       │
                  │  • Include disclaimers │
                  │  • Add sources         │
                  └────────────┬───────────┘
                               ▼
                          AGENT OUTPUT
```

---

## 4. Component Responsibilities

### **Orchestration Layer (LangGraph)**
- **Request Routing**: Classify intent and route to appropriate agent(s)
- **State Management**: Maintain conversation history and context
- **Agent Coordination**: Handle multi-agent flows when needed
- **Error Handling**: Fallback mechanisms for API failures

### **Specialized Agents** (6 total)

| Agent | Primary Responsibility | Data Sources |
|-------|----------------------|--------------|
| **Finance Q&A** | Educational content on financial concepts | Knowledge Base (RAG) |
| **Portfolio Analysis** | Analyze holdings, diversification, performance | User input + Market data |
| **Market Analysis** | Real-time trends, stock quotes, analysis | Market APIs (Alpha Vantage, yFinance) |
| **Goal Planning** | Financial goal setting and projections | User profile + LLM reasoning |
| **News Synthesizer** | Contextual financial news summaries | Financial News APIs + Market data |
| **Tax Education** | Tax concepts, account types, strategies | Knowledge Base (RAG) |

### **Shared Services**

| Service | Purpose |
|---------|---------|
| **LLM Interface** | Unified access to Claude/Gemini with prompt management |
| **Vector DB** | Store and retrieve financial knowledge efficiently |
| **Session Manager** | Maintain user profiles, conversation history |
| **API Manager** | Rate limiting, caching, error handling for external APIs |
| **Error Handler** | Graceful degradation and user-friendly error messages |

### **Data Layer**

| Resource | Content |
|----------|---------|
| **Knowledge Base** | 50-100 curated financial education articles with embeddings |
| **Market Data Cache** | Real-time quotes with intelligent caching strategy |
| **User Profiles** | Preferences, risk tolerance, portfolio data |
| **Session Store** | Conversation history and context |

---

## 5. Key Design Patterns

### **Pattern 1: Intent-Driven Routing**
```
Query → Classify Intent → Select Agent(s) → Execute → Aggregate Response
```

### **Pattern 2: RAG Enhancement**
```
Query → Retrieve Knowledge Base Docs → Enrich Prompt → LLM Processing → Response
```

### **Pattern 3: Multi-Turn Context Preservation**
```
User Message → Add to History → Update State → Route → Use Full Context → Respond
```

### **Pattern 4: Error Boundary Pattern**
```
Try API Call → Catch Error → Log Issue → Use Cached Data / Fallback → Respond
```

---

## 6. Deployment Architecture

```
┌──────────────────────────────────────────────────────┐
│                 PRODUCTION ENVIRONMENT               │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │         Streamlit Web Application              │  │
│  │         (Containerized - Optional)             │  │
│  └──────┬─────────────────────────────────────────┘  │
│         │                                            │
│         ▼                                            │
│  ┌────────────────────────────────────────────────┐  │
│  │      Python Runtime (LangChain/LangGraph)     │  │
│  │      • Agents                                 │  │
│  │      • Orchestration                          │  │
│  │      • State Management                       │  │
│  └──────┬─────────────────────────────────────────┘  │
│         │                                            │
│  ┌──────┴─────────────────┬──────────────────────┐   │
│  │                        │                      │   │
│  ▼                        ▼                      ▼   │
│ ┌─────────────┐  ┌─────────────────┐  ┌───────────┐ │
│ │ Local Vector│  │   Config File   │  │  Logging/ │ │
│ │  DB (FAISS/ │  │   (YAML)         │  │ Monitoring│ │
│ │  Chroma)    │  │                 │  │           │ │
│ └─────────────┘  └─────────────────┘  └───────────┘ │
│                                                      │
│  External Dependencies:                             │
│  • Alpha Vantage API                                │
│  • yFinance API                                     │
│  • Claude/Gemini API                                │
│  • News APIs                                        │
└──────────────────────────────────────────────────────┘
```

---

## 7. Configuration Management

```
config.yaml
├── llm
│   ├── provider: "claude" | "gemini"
│   ├── model: "claude-3-5-sonnet" | "gemini-pro"
│   └── temperature: 0.3-0.7
├── vector_db
│   ├── type: "faiss" | "chroma"
│   └── embedding_model: "sentence-transformers"
├── agents
│   └── [agent-specific configs]
├── apis
│   ├── alpha_vantage:
│   │   ├── key: "${ALPHA_VANTAGE_KEY}"
│   │   └── rate_limit: 5/min
│   ├── yfinance:
│   │   └── cache_ttl: 300s
│   └── news:
│       └── sources: [...]
└── cache
    ├── ttl: 300s (market data)
    └── size: 1000 entries
```

---

## 8. Error Handling Strategy

```
┌──────────────────────────────────────┐
│        Error Occurs                  │
└────────────┬─────────────────────────┘
             │
             ▼
    ┌─────────────────────┐
    │ Error Type?         │
    └────┬────────┬───────┘
         │        │
         │        └─────────────────────┐
         ▼                              ▼
    ┌─────────────────┐         ┌──────────────────┐
    │  API Error      │         │  Data Error      │
    │  (Rate limit/   │         │  (Parsing/       │
    │   timeout)      │         │   validation)    │
    └────┬────────────┘         └────┬─────────────┘
         │                           │
         ▼                           ▼
    ┌─────────────────┐         ┌──────────────────┐
    │  • Retry logic  │         │  • Log error     │
    │  • Use cache    │         │  • Return default│
    │  • Fallback msg │         │  • Suggest retry │
    └────┬────────────┘         └────┬─────────────┘
         │                           │
         └───────────┬───────────────┘
                     ▼
          ┌──────────────────────┐
          │  User-Friendly       │
          │  Response with       │
          │  Alternative Info    │
          └──────────────────────┘
```

---

## 9. Scalability Considerations

- **Horizontal Scaling**: Stateless agent design allows deployment across multiple instances
- **Rate Limiting**: Built-in API throttling prevents upstream service overload
- **Caching Strategy**: Market data cached locally to reduce API calls
- **Async Processing**: Long-running analyses can be made asynchronous if needed
- **Queue Management**: For batch operations, integrate message queue (optional)

---

## 10. Security & Compliance

- **API Key Management**: Environment variables, no hardcoding
- **Input Validation**: Sanitize all user inputs
- **Output Disclaimers**: Clear education vs. advice distinction
- **Rate Limiting**: Prevent abuse and control costs
- **Audit Logging**: Track all transactions for compliance
- **Data Privacy**: Minimal PII retention, user consent tracking

---

## 11. AWS Deployment Plan

### **11.1 AWS Services Mapping**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AWS DEPLOYMENT ARCHITECTURE                         │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                    FRONTEND LAYER                                      │ │
│  │  AWS Amplify + CloudFront (Streamlit App Distribution)                │ │
│  │  Route 53 (DNS Management)                                            │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                 │                                           │
│                                 ▼                                           │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                    APPLICATION LAYER                                   │ │
│  │  ECS on Fargate (Containerized LangChain/LangGraph Services)          │ │
│  │  • Agent Services (Task Definitions)                                  │ │
│  │  • Orchestration Service                                              │ │
│  │  • Auto-scaling Groups                                                │ │
│  │                                                                        │ │
│  │  Application Load Balancer (ALB)                                       │ │
│  │  • Route traffic to services                                          │ │
│  │  • Health checks                                                      │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                 │                                           │
│     ┌───────────────────────────┼───────────────────────────┐              │
│     ▼                           ▼                           ▼              │
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐  │
│  │   DATA LAYER    │    │ CACHE & MESSAGING│    │   STORAGE LAYER     │  │
│  │                 │    │                  │    │                     │  │
│  │ • RDS (PostgreSQL
│  │   Session Store)│    │ • ElastiCache    │    │ • S3 (Knowledge Base│  │
│  │                 │    │   (Redis)        │    │   Articles)         │  │
│  │ • DynamoDB      │    │   (Hot Cache)    │    │                     │  │
│  │   (User Profiles)    │                  │    │ • OpenSearch        │  │
│  │                 │    │ • SQS (Queues)   │    │   (Vector Store)    │  │
│  │                 │    │   (Async Tasks)  │    │                     │  │
│  │ • DocumentDB    │    │                  │    │ • CloudWatch Logs   │  │
│  │   (Conversation │    │ • SNS (Events)   │    │   (Centralized)     │  │
│  │    History)     │    │   (Notifications)│    │                     │  │
│  └─────────────────┘    └──────────────────┘    └─────────────────────┘  │
│                                 │                                           │
│     ┌───────────────────────────┼───────────────────────────┐              │
│     ▼                           ▼                           ▼              │
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐  │
│  │   SECURITY      │    │ MONITORING       │    │ EXTERNAL APIS       │  │
│  │                 │    │                  │    │                     │  │
│  │ • AWS Secrets   │    │ • CloudWatch     │    │ • Bedrock (LLM)     │  │
│  │   Manager       │    │   (Metrics/Logs) │    │   Alternative: Sage │  │
│  │   (API Keys)    │    │                  │    │   Maker JumpStart    │  │
│  │                 │    │ • X-Ray (Tracing)│    │                     │  │
│  │ • VPC & Security│    │   (Distributed)  │    │ • EventBridge       │  │
│  │   Groups (SG)   │    │                  │    │   (Orchestration)   │  │
│  │                 │    │ • SNS Alerts     │    │                     │  │
│  │ • IAM Roles     │    │   (Notifications)│    │ • External APIs:    │  │
│  │   & Policies    │    │                  │    │   - Alpha Vantage   │  │
│  │                 │    │ • Cost Explorer  │    │   - yFinance        │  │
│  │ • KMS Encryption│    │   (Optimization) │    │   - News APIs       │  │
│  └─────────────────┘    └──────────────────┘    └─────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### **11.2 Component-to-AWS Service Mapping**

| Architecture Component | AWS Service | Purpose |
|----------------------|-------------|---------|
| **UI Layer** | Amplify + CloudFront + Route 53 | Host Streamlit app with CDN distribution |
| **Container Runtime** | ECS Fargate | Run agents and orchestration services |
| **Load Balancing** | Application Load Balancer | Distribute traffic across services |
| **Session Store** | RDS PostgreSQL | Persistent session and conversation history |
| **User Profiles** | DynamoDB | Fast key-value access for profiles |
| **Conversation History** | DocumentDB | Document storage for rich context |
| **Vector DB** | OpenSearch (managed) | Semantic search for knowledge base |
| **Knowledge Base** | S3 + CloudFront | Store and serve articles |
| **Hot Cache** | ElastiCache Redis | Fast access to frequent queries |
| **Message Queue** | SQS | Async task processing |
| **Event Notifications** | SNS + EventBridge | Trigger workflows and alerts |
| **LLM** | Bedrock (or external API) | Claude/Gemini via AWS managed service |
| **Secrets Management** | Secrets Manager | Store API keys securely |
| **Logging** | CloudWatch Logs | Centralized logging |
| **Metrics/Monitoring** | CloudWatch + X-Ray | Performance tracking & distributed tracing |
| **Alerts** | CloudWatch Alarms + SNS | Operational alerts |
| **VPC/Networking** | VPC + Security Groups + NAT | Network isolation and security |
| **Domain/DNS** | Route 53 | Domain management |

---

### **11.3 Deployment Architecture on AWS**

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              AWS ACCOUNT                                     │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                          VPC (Virtual Private Cloud)                   │ │
│  │  CIDR: 10.0.0.0/16                                                    │ │
│  │                                                                        │ │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │ │
│  │  │                    PUBLIC SUBNET (AZ-1)                         │ │ │
│  │  │  • NAT Gateway                                                  │ │ │
│  │  │  • CloudFront Origin                                            │ │ │
│  │  └──────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                        │ │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │ │
│  │  │                 PRIVATE SUBNET (AZ-1) - APP TIER               │ │ │
│  │  │  ┌────────────────────────────────────────────────────────────┐ │ │ │
│  │  │  │  ALB (Application Load Balancer)                          │ │ │ │
│  │  │  │  • Port 443 (HTTPS)                                       │ │ │ │
│  │  │  │  • Health Checks                                          │ │ │ │
│  │  │  └──────────────┬─────────────────────────────────────────────┘ │ │ │
│  │  │                 │                                              │ │ │
│  │  │  ┌──────────────┴──────────────────────────────────────────┐  │ │ │
│  │  │  │  ECS Fargate Cluster (Agent Services)                  │  │ │ │
│  │  │  │  ┌────────────┬────────────┬────────────┬────────────┐ │  │ │ │
│  │  │  │  │ Finance Q&A│ Portfolio  │ Market     │ Task X     │ │  │ │ │
│  │  │  │  │ (Task)     │ Analysis   │ Analysis   │ (...)      │ │  │ │ │
│  │  │  │  │            │ (Task)     │ (Task)     │            │ │  │ │ │
│  │  │  │  └────────────┴────────────┴────────────┴────────────┘ │  │ │ │
│  │  │  │  Auto Scaling Group (Min: 2, Max: 10 tasks)            │  │ │ │
│  │  │  └────────────────────────────────────────────────────────┘  │ │ │
│  │  │                                                              │ │ │
│  │  └──────────────────────────────────────────────────────────────┘ │ │
│  │                                                                        │ │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │ │
│  │  │              PRIVATE SUBNET (AZ-1) - DATA TIER                 │ │ │
│  │  │  ┌──────────────┬────────────────┬──────────────────────────┐  │ │ │
│  │  │  │ RDS Aurora   │ DocumentDB     │ DynamoDB               │  │ │ │
│  │  │  │ PostgreSQL   │ (Replicated)   │ (On-Demand)            │  │ │ │
│  │  │  │ Multi-AZ     │                │                        │  │ │ │
│  │  │  └──────────────┴────────────────┴──────────────────────────┘  │ │ │
│  │  │                                                                │ │ │
│  │  │  ┌──────────────┬────────────────┬──────────────────────────┐  │ │ │
│  │  │  │ ElastiCache  │ OpenSearch     │ S3 Bucket             │  │ │ │
│  │  │  │ Redis Cluster│ (Vector DB)    │ (Knowledge Base)      │  │ │ │
│  │  │  │              │ Multi-AZ       │ (Versioned)           │  │ │ │
│  │  │  └──────────────┴────────────────┴──────────────────────────┘  │ │ │
│  │  │                                                                │ │ │
│  │  └──────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                        │ │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │ │
│  │  │            PRIVATE SUBNET (AZ-2) - REPLICA                      │ │ │
│  │  │  RDS Read Replica | DocumentDB Replica | ElastiCache Replica   │ │ │
│  │  └──────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                        │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

### **11.4 Step-by-Step AWS Deployment Workflow**

#### **Phase 1: Infrastructure Setup (Week 1)**

```
1. AWS Account & IAM Setup
   ├─ Create AWS account
   ├─ Set up IAM roles/policies
   │  ├─ ECS Task Execution Role
   │  ├─ ECS Task Role (for accessing services)
   │  └─ Lambda Functions Role (for automation)
   └─ Enable CloudTrail for audit logs

2. VPC & Networking
   ├─ Create VPC (10.0.0.0/16)
   ├─ Create public subnets (2 AZs)
   ├─ Create private subnets (2 AZs)
   ├─ Set up NAT Gateways
   ├─ Configure Route Tables
   ├─ Create Security Groups
   │  ├─ ALB Security Group (allow 443)
   │  ├─ ECS Security Group (allow from ALB)
   │  └─ Database Security Group (allow from ECS)
   └─ Configure NACLs

3. Secrets Management
   ├─ Store API Keys in Secrets Manager
   │  ├─ Alpha Vantage Key
   │  ├─ Claude/Gemini API Key
   │  ├─ yFinance credentials (if needed)
   │  └─ Other external API keys
   └─ Set up Secrets rotation policies

4. Route 53 & DNS
   ├─ Register domain (or use existing)
   ├─ Create hosted zone
   └─ Set up CNAME for ALB
```

#### **Phase 2: Data Layer Setup (Week 1-2)**

```
5. RDS PostgreSQL (Session Store)
   ├─ Create RDS Aurora PostgreSQL cluster
   │  ├─ Multi-AZ deployment
   │  ├─ 2 instances (primary + read replica)
   │  ├─ Daily automated backups (7-day retention)
   │  └─ Point-in-time recovery enabled
   ├─ Create database schema
   └─ Configure connection pooling (PgBouncer)

6. DynamoDB (User Profiles)
   ├─ Create table with partition key (user_id)
   ├─ Set sort key (profile_version)
   ├─ Configure billing mode (on-demand for MVP)
   ├─ Enable point-in-time recovery
   └─ Set up global secondary indexes

7. DocumentDB (Conversation History)
   ├─ Create DocumentDB cluster
   ├─ Multi-AZ setup
   ├─ Enable automated backups
   └─ Create conversation collection indexes

8. ElastiCache Redis (Hot Cache)
   ├─ Create Redis cluster
   ├─ Multi-AZ with automatic failover
   ├─ Configure cache eviction policy (LRU)
   └─ Set up parameter groups

9. OpenSearch (Vector Store)
   ├─ Create OpenSearch domain
   ├─ Multi-AZ deployment (3 nodes)
   ├─ Enable encryption at rest
   ├─ Configure indexing for embeddings
   └─ Set up snapshot backups to S3

10. S3 (Knowledge Base)
    ├─ Create S3 bucket (versioning enabled)
    ├─ Upload knowledge base articles
    ├─ Enable CloudFront distribution
    ├─ Configure lifecycle policies
    └─ Set up bucket encryption (KMS)
```

#### **Phase 3: Application Layer Setup (Week 2-3)**

```
11. ECR (Elastic Container Registry)
    ├─ Create ECR repositories
    │  ├─ finance-assistant-orchestrator
    │  ├─ finance-qa-agent
    │  ├─ portfolio-analysis-agent
    │  ├─ market-analysis-agent
    │  ├─ goal-planning-agent
    │  ├─ news-synthesizer-agent
    │  └─ tax-education-agent
    └─ Configure image scanning & lifecycle policies

12. ECS Cluster Setup
    ├─ Create Fargate cluster
    ├─ Set up CloudWatch container insights
    ├─ Configure task definitions for each agent
    │  ├─ CPU: 256-512 (based on agent)
    │  ├─ Memory: 512-1024 MB
    │  ├─ Environment variables
    │  └─ Logging to CloudWatch
    └─ Create ECS services for each agent

13. Application Load Balancer (ALB)
    ├─ Create ALB in public subnets
    ├─ Configure target groups
    │  ├─ Health check path: /health
    │  ├─ Port: 8000 (ECS tasks)
    │  └─ Protocol: HTTP (ALB → ECS), HTTPS (Client → ALB)
    ├─ Add listeners
    │  ├─ 443 (HTTPS) → Target Group
    │  └─ 80 → Redirect to 443
    ├─ Attach SSL/TLS certificates (ACM)
    └─ Configure WAF rules (optional but recommended)

14. Auto Scaling Groups
    ├─ Set target scaling policies
    │  ├─ Min: 2 tasks
    │  ├─ Desired: 3 tasks
    │  ├─ Max: 10 tasks
    │  └─ Scale based on CPU (70%) & Memory (80%)
    └─ Configure scale-in cooldown (300s)
```

#### **Phase 4: Integration & Deployment (Week 3-4)**

```
15. Deployment Automation (CodePipeline + CodeBuild)
    ├─ Set up CodeRepository (GitHub/CodeCommit)
    ├─ Create CodeBuild project
    │  ├─ Build Docker images
    │  ├─ Push to ECR
    │  └─ Run integration tests
    ├─ Create CodePipeline
    │  ├─ Source: GitHub/CodeCommit
    │  ├─ Build: CodeBuild
    │  ├─ Deploy: ECS (Canary or Blue/Green)
    │  └─ Manual approval before production
    └─ Configure notifications (SNS)

16. Messaging & Queuing
    ├─ Create SQS queues
    │  ├─ AsyncTaskQueue (for long-running tasks)
    │  ├─ NotificationQueue (for alerts)
    │  └─ DeadLetterQueue (for failed tasks)
    ├─ Create SNS topics
    │  ├─ AlertTopic
    │  └─ NotificationTopic
    └─ Configure Lambda for queue processing (optional)

17. EventBridge (Orchestration)
    ├─ Create rules for multi-agent workflows
    ├─ Route events to appropriate services
    └─ Enable DLQ for failed events

18. Monitoring & Logging
    ├─ Configure CloudWatch Logs
    │  ├─ Log groups for each service
    │  ├─ Log retention: 30 days
    │  └─ Log filters for errors/warnings
    ├─ Set up CloudWatch Dashboards
    │  ├─ Service health
    │  ├─ Request latency
    │  ├─ Error rates
    │  └─ Resource utilization
    ├─ Enable X-Ray tracing
    └─ Create CloudWatch Alarms
       ├─ High error rate (>5%)
       ├─ High latency (>2s p99)
       ├─ Database connection issues
       └─ Out of memory errors
```

#### **Phase 5: Testing & Go-Live (Week 4)**

```
19. Testing
    ├─ Integration testing in staging
    ├─ Load testing (1000 concurrent users)
    ├─ Security scanning (OWASP)
    ├─ Penetration testing (recommended)
    └─ Data validation

20. Deployment
    ├─ Deploy to staging environment
    ├─ Smoke tests
    ├─ Blue/Green deployment to production
    ├─ Gradual traffic shift (10% → 50% → 100%)
    └─ Monitor metrics post-deployment

21. Post-Launch
    ├─ Daily monitoring for 1 week
    ├─ Performance baseline establishment
    ├─ Cost optimization review
    └─ User feedback collection
```

---

### **11.5 Infrastructure as Code (IaC)**

**Using AWS CDK (Python)**

```python
# Example structure
project/
├── cdk/
│   ├── cdk.json
│   ├── app.py                    # Entry point
│   ├── stacks/
│   │   ├── vpc_stack.py          # VPC + Networking
│   │   ├── database_stack.py     # RDS, DocumentDB, DynamoDB
│   │   ├── cache_stack.py        # ElastiCache, OpenSearch
│   │   ├── ecs_stack.py          # ECS Cluster & Services
│   │   ├── alb_stack.py          # Load Balancer
│   │   ├── secrets_stack.py      # Secrets Manager
│   │   └── monitoring_stack.py   # CloudWatch, X-Ray
│   └── requirements.txt
```

**Alternative: Terraform**

```hcl
# Example structure
project/
├── terraform/
│   ├── main.tf                   # Provider & main config
│   ├── variables.tf              # Input variables
│   ├── outputs.tf                # Outputs
│   ├── modules/
│   │   ├── vpc/
│   │   ├── database/
│   │   ├── ecs/
│   │   ├── monitoring/
│   │   └── security/
│   ├── environments/
│   │   ├── dev.tfvars
│   │   ├── staging.tfvars
│   │   └── prod.tfvars
│   └── .gitignore
```

---

### **11.6 Cost Estimation (Monthly)**

| Service | Usage | Cost |
|---------|-------|------|
| **ECS Fargate** | 3 tasks × 0.5 GB × 24h | $45 |
| **ALB** | 1 ALB + 1M requests | $25 |
| **RDS Aurora** | 2 instances (db.t3.medium) | $150 |
| **DocumentDB** | 2 instances (db.t3.medium) | $200 |
| **DynamoDB** | On-demand (small usage) | $25 |
| **ElastiCache** | 1 Redis node (cache.t3.micro) | $20 |
| **OpenSearch** | 3 nodes (t3.small) | $100 |
| **S3** | 10 GB storage + transfer | $10 |
| **CloudWatch** | Logs + Monitoring | $30 |
| **Data Transfer** | 10 GB/month | $1 |
| **NAT Gateway** | 2 NATs + data processing | $60 |
| **Route 53** | Domain + queries | $2 |
| **Secrets Manager** | Secret storage & rotation | $1 |
| **Total Estimated** | | **~$670/month** |

**Cost Optimization Tips:**
- Use Reserved Instances for stable workloads (30-40% savings)
- Implement tiered caching (hot/warm/cold data)
- Use Spot instances for non-critical workloads
- Implement S3 lifecycle policies
- Monitor unused resources with Cost Explorer

---

### **11.7 High Availability & Disaster Recovery**

```
┌─────────────────────────────────────────────────────────┐
│         High Availability Strategy                      │
├─────────────────────────────────────────────────────────┤
│ • Multi-AZ deployment for all critical services        │
│ • Load balancing across availability zones             │
│ • Auto Scaling with minimum 2 running instances        │
│ • RTO: 1 hour | RPO: 15 minutes                        │
│ • Health checks with automatic recovery               │
│ • Circuit breaker pattern for external APIs           │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│      Disaster Recovery Strategy                        │
├─────────────────────────────────────────────────────────┤
│ Backup Strategy:                                       │
│ • RDS: Automated daily backups (7-day retention)      │
│ • DocumentDB: Continuous backups                      │
│ • S3: Versioning + Cross-region replication          │
│ • OpenSearch: Daily snapshots to S3                   │
│                                                       │
│ Recovery:                                              │
│ • Database recovery from snapshots (15 min)           │
│ • Code rollback via CodePipeline                      │
│ • DNS failover via Route 53                           │
│ • Cross-region failover (optional, 30 min setup)      │
└─────────────────────────────────────────────────────────┘
```

---

### **11.8 Security Best Practices**

```
┌──────────────────────────────────────────────────────┐
│  Security Checklist                                 │
├──────────────────────────────────────────────────────┤
│ Network Security:                                   │
│ ✓ VPC with private subnets for sensitive services   │
│ ✓ Security groups with minimal permissions          │
│ ✓ NACLs for additional network layer                │
│ ✓ VPC Flow Logs for monitoring                      │
│ ✓ AWS WAF on ALB                                    │
│                                                     │
│ Data Security:                                      │
│ ✓ Encryption at rest (RDS, S3, DocumentDB)          │
│ ✓ Encryption in transit (TLS 1.3)                   │
│ ✓ KMS keys for sensitive data                       │
│ ✓ Secrets Manager for API keys                      │
│ ✓ Database backups encrypted                        │
│                                                     │
│ Access Control:                                     │
│ ✓ IAM roles with least privilege                    │
│ ✓ Service-to-service authentication                │
│ ✓ MFA for human access                             │
│ ✓ Regular access reviews                           │
│                                                     │
│ Monitoring & Compliance:                            │
│ ✓ CloudTrail for audit logs                         │
│ ✓ Config for compliance tracking                    │
│ ✓ GuardDuty for threat detection                    │
│ ✓ Security Hub for centralized view                │
│ ✓ VPC Flow Logs enabled                            │
└──────────────────────────────────────────────────────┘
```

---

### **11.9 Monitoring & Operations**

```
Dashboard Metrics (CloudWatch):
├─ Application Metrics
│  ├─ Request latency (p50, p95, p99)
│  ├─ Error rate (%)
│  ├─ Request count (per agent)
│  └─ Active users
├─ Infrastructure Metrics
│  ├─ CPU utilization
│  ├─ Memory utilization
│  ├─ Network I/O
│  └─ Disk I/O
├─ Database Metrics
│  ├─ Connection pool utilization
│  ├─ Query latency
│  ├─ Replication lag
│  └─ Backup duration
└─ Cost Metrics
   ├─ Daily spend
   ├─ Cost by service
   ├─ Cost anomalies
   └─ Reserved capacity utilization

Alarms:
├─ Critical (Page on-call)
│  ├─ Error rate > 5%
│  ├─ Latency p99 > 5s
│  ├─ Database unavailable
│  └─ Memory > 90%
├─ High (Create ticket)
│  ├─ Error rate > 2%
│  ├─ Latency p99 > 2s
│  ├─ Disk usage > 80%
│  └─ Unexpected costs spike
└─ Low (Log & review)
   ├─ Disk usage > 60%
   ├─ Backup failures
   └─ API rate limit warnings
```

---

## Summary

This architecture provides a **modular, scalable foundation** for the AI Finance Assistant that:
- ✅ Separates concerns (agents, services, data)
- ✅ Enables easy addition of new agents
- ✅ Supports robust error handling and fallbacks
- ✅ Maintains conversation context across turns
- ✅ Integrates real-time data efficiently
- ✅ Provides clear audit trails for regulatory compliance
- ✅ **Deploys reliably on AWS with high availability**
- ✅ **Scales automatically based on demand**
- ✅ **Implements security best practices**
- ✅ **Provides comprehensive monitoring & alerting**

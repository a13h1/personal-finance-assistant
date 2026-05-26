import yaml
import os
from dotenv import load_dotenv
from src.core.llm_interface import LLMInterface
from src.core.session_manager import SessionManager
from src.utils.market_data import MarketDataService
from src.rag.vector_store import FinancialVectorStore
from src.rag.retriever import RAGRetriever
from src.agents.finance_qa_agent import FinanceQAAgent
from src.agents.portfolio_agent import PortfolioAgent
from src.agents.market_agent import MarketAgent
from src.agents.goal_planning_agent import GoalPlanningAgent
from src.agents.news_agent import NewsAgent
from src.agents.tax_agent import TaxAgent
from src.workflow.router import create_workflow
import logging

logger = logging.getLogger(__name__)


class FinanceOrchestrator:
    def __init__(self, config_path: str = "config.yaml"):
        # Find .env relative to this file so it works regardless of cwd
        _env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
        load_dotenv(_env_path)
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        self._initialize_components()

    def _initialize_components(self):
        llm_config = self.config["llm"]
        self.llm = LLMInterface(
            model=llm_config["model"],
            temperature=llm_config["temperature"],
            max_tokens=llm_config["max_tokens"]
        )

        # pkg_root = ai_finance_assistant/src
        pkg_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        project_root = os.path.dirname(pkg_root)

        default_db = f"sqlite:///{os.path.join(project_root, 'data', 'sessions.db')}"
        database_url = os.getenv("DATABASE_URL", default_db)
        self.session_manager = SessionManager(database_url=database_url)
        self.market_data = MarketDataService(cache_ttl=self.config["cache"]["ttl"])

        # Initialize vector store
        self.vector_store = FinancialVectorStore(
            embedding_model=self.config["vector_db"]["embedding_model"],
            chunk_size=self.config["vector_db"]["chunk_size"],
            chunk_overlap=self.config["vector_db"]["chunk_overlap"]
        )

        # Knowledge base directory is relative to this file's package root
        kb_dir = os.path.join(pkg_root, "data", "knowledge_base")
        index_path = self.config["vector_db"]["index_path"]

        if not os.path.isabs(index_path):
            index_path = os.path.join(project_root, index_path)

        if os.path.exists(index_path):
            logger.info("Loading existing FAISS index...")
            self.vector_store.load(index_path)
        elif os.path.exists(kb_dir):
            logger.info("Building FAISS index from knowledge base...")
            self.vector_store.build_from_directory(kb_dir)
            self.vector_store.save(index_path)
        else:
            logger.warning(f"Knowledge base directory not found: {kb_dir}")

        self.retriever = RAGRetriever(self.vector_store)

        agent_configs = self.config["agents"]
        self.agents = {
            "finance_qa": FinanceQAAgent(self.llm, self.retriever, agent_configs["finance_qa"]["system_prompt"]),
            "portfolio": PortfolioAgent(self.llm, self.market_data, agent_configs["portfolio"]["system_prompt"]),
            "market": MarketAgent(self.llm, self.market_data, agent_configs["market"]["system_prompt"]),
            "goal_planning": GoalPlanningAgent(self.llm, agent_configs["goal_planning"]["system_prompt"]),
            "news": NewsAgent(self.llm, self.market_data, agent_configs["news"]["system_prompt"], agent_configs["news"]["max_articles"]),
            "tax": TaxAgent(self.llm, self.retriever, agent_configs["tax"]["system_prompt"]),
        }

        self.workflow = create_workflow(self.agents, synthesis_llm=self.llm)

    def process_query(self, query: str, session_id: str) -> dict:
        """Process a user query through the finance workflow.

        Args:
            query: The user's input query.
            session_id: The session identifier for storing and retrieving session state.

        Returns:
            A dictionary containing the assistant response and the agent intent.
        """
        from langchain_core.messages import HumanMessage, AIMessage
        
        self.session_manager.add_message(session_id, "user", query)

        history = self.session_manager.get_history(session_id, last_n=10)
        portfolio = self.session_manager.get_portfolio(session_id)
        profile = self.session_manager.get_profile(session_id)
        
        messages = []
        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

        state = {
            "messages": messages,
            "intents": [],
            "portfolio": portfolio,
            "profile": {
                "risk_tolerance": profile.risk_tolerance,
                "investment_horizon": profile.investment_horizon,
                "experience_level": profile.experience_level,
            },
            "session_id": session_id,
            "error": None,
        }

        result = self.workflow.invoke(state)

        # The final message is the synthesized response or the single agent response
        final_message = result.get("messages", [])[-1]
        response = final_message.content if final_message else "I'm sorry, I couldn't process your request."
        
        # We can extract the identified intents
        intents = result.get("intents", [])
        intent_str = ",".join(intents) if intents else "unknown"

        self.session_manager.add_message(session_id, "assistant", response, agent=intent_str)

        return {"response": response, "agent": intent_str}

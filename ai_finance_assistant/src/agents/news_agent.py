from src.agents.base_agent import BaseAgent
from src.core.llm_interface import LLMInterface
from src.utils.market_data import MarketDataService
import re


class NewsAgent(BaseAgent):
    def __init__(self, llm: LLMInterface, market_data: MarketDataService, system_prompt: str, max_articles: int = 5):
        super().__init__(llm, system_prompt, "News Synthesizer")
        self.market_data = market_data
        self.max_articles = max_articles

    def process(self, query: str, context: dict) -> str:
        symbols = re.findall(r'\b[A-Z]{1,5}\b', query)
        news_context = ""

        if symbols:
            for symbol in symbols[:2]:
                news = self.market_data.get_news(symbol)
                if news:
                    news_context += f"\nRecent news for {symbol}:\n"
                    for article in news[:self.max_articles]:
                        title = article.get("title", "")
                        publisher = article.get("publisher", "")
                        if title:
                            news_context += f"- {title} ({publisher})\n"
        else:
            # General market news from major indices
            for symbol in ["SPY", "QQQ"]:
                news = self.market_data.get_news(symbol)
                if news:
                    news_context += "\nRecent market news:\n"
                    for article in news[:self.max_articles]:
                        title = article.get("title", "")
                        publisher = article.get("publisher", "")
                        if title:
                            news_context += f"- {title} ({publisher})\n"
                    break

        prompt = f"""Recent Financial News:
{news_context if news_context else "No specific news articles available at this time."}

User question: {query}

Synthesize the available news and provide context about what this means for investors."""

        return self.llm.generate(prompt, self.system_prompt)

from typing import Optional
from src.agents.base_agent import BaseAgent
from src.core.llm_interface import LLMInterface
from src.utils.market_data import MarketDataService
import re


class MarketAgent(BaseAgent):
    def __init__(self, llm: LLMInterface, market_data: MarketDataService, system_prompt: str):
        super().__init__(llm, system_prompt, "Market Analysis")
        self.market_data = market_data

    def _extract_symbols(self, query: str) -> list:
        # Simple regex to find stock ticker patterns
        return re.findall(r'\b[A-Z]{1,5}\b', query)

    def process(self, query: str, context: dict, trace_metadata: Optional[dict] = None) -> str:
        symbols = self._extract_symbols(query)
        market_context = ""

        # Get market indices
        indices = self.market_data.get_market_indices()
        if indices:
            market_context += "Current Market Overview:\n"
            for name, data in indices.items():
                if data and data.get("price"):
                    change = data.get("change_pct", 0) or 0
                    market_context += f"- {name}: {data['price']:.2f} ({change:+.2f}%)\n"

        # Get specific stock data
        if symbols:
            market_context += "\nSpecific Stock Data:\n"
            for symbol in symbols[:5]:  # Limit to 5 symbols
                quote = self.market_data.get_quote(symbol)
                if quote and quote.get("price"):
                    change = quote.get("change_pct", 0) or 0
                    market_context += f"- {symbol}: ${quote['price']:.2f} ({change:+.2f}%)\n"
                    if quote.get("pe_ratio"):
                        market_context += f"  P/E: {quote['pe_ratio']:.1f}\n"

        prompt = f"""Market Data:
{market_context}

User question: {query}

Provide market analysis based on the data above."""

        return self.llm.generate(prompt, self.system_prompt, trace_metadata=trace_metadata)

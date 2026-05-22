from src.agents.base_agent import BaseAgent
from src.core.llm_interface import LLMInterface
from src.utils.market_data import MarketDataService
import json


class PortfolioAgent(BaseAgent):
    def __init__(self, llm: LLMInterface, market_data: MarketDataService, system_prompt: str):
        super().__init__(llm, system_prompt, "Portfolio Analysis")
        self.market_data = market_data

    def process(self, query: str, context: dict) -> str:
        portfolio = context.get("portfolio")

        if not portfolio or not portfolio.get("holdings"):
            return (
                "Please provide your portfolio holdings first. Use the Portfolio tab to enter your holdings, "
                "or describe your portfolio in your message (e.g., '100 shares of AAPL at $150, 50 shares of MSFT at $300')."
            )

        analysis = self.market_data.analyze_portfolio(portfolio["holdings"])

        analysis_text = f"""Portfolio Analysis Results:
- Total Value: ${analysis.get('total_value', 0):,.2f}
- Total Cost Basis: ${analysis.get('total_cost', 0):,.2f}
- Total Gain/Loss: ${analysis.get('total_gain_loss', 0):,.2f} ({analysis.get('total_gain_loss_pct', 0):.1f}%)

Holdings:
"""
        for h in analysis.get("holdings", []):
            analysis_text += (
                f"- {h['symbol']} ({h['name']}): {h['shares']} shares @ ${h['current_price']:.2f} "
                f"= ${h['current_value']:,.2f} ({h['gain_loss_pct']:+.1f}%)\n"
            )

        if analysis.get("sector_allocation_pct"):
            analysis_text += "\nSector Allocation:\n"
            for sector, pct in analysis["sector_allocation_pct"].items():
                analysis_text += f"- {sector}: {pct:.1f}%\n"

        prompt = f"""Portfolio data:
{analysis_text}

User question: {query}

Provide analysis including:
1. Performance assessment
2. Diversification analysis
3. Risk assessment
4. Specific suggestions for improvement"""

        return self.llm.generate(prompt, self.system_prompt)

from typing import Optional
from src.agents.base_agent import BaseAgent
from src.core.llm_interface import LLMInterface


class GoalPlanningAgent(BaseAgent):
    def __init__(self, llm: LLMInterface, system_prompt: str):
        super().__init__(llm, system_prompt, "Goal Planning")

    def process(self, query: str, context: dict, trace_metadata: Optional[dict] = None) -> str:
        profile = context.get("profile", {})
        history = context.get("history", [])

        profile_context = ""
        if profile:
            profile_context = f"""User Profile:
- Risk Tolerance: {profile.get('risk_tolerance', 'moderate')}
- Investment Horizon: {profile.get('investment_horizon', 'medium')}
- Experience Level: {profile.get('experience_level', 'beginner')}
"""

        prompt = f"""{profile_context}
User Goal Question: {query}

Provide a detailed financial goal plan including:
1. Goal clarification and timeline
2. Required monthly savings calculation
3. Recommended investment approach based on risk tolerance
4. Key milestones to track progress
5. Potential obstacles and how to overcome them"""

        if history:
            return self.llm.generate_with_history(
                history + [{"role": "user", "content": prompt}],
                self.system_prompt,
                trace_metadata=trace_metadata,
            )
        return self.llm.generate(prompt, self.system_prompt, trace_metadata=trace_metadata)

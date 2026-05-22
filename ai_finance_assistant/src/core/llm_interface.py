from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage


class LLMInterface:
    def __init__(self, model: str, temperature: float, max_tokens: int):
        self.llm = ChatOpenAI(model=model, temperature=temperature, max_tokens=max_tokens)

    def generate(self, user_message: str, system_prompt: str = None) -> str:
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=user_message))
        response = self.llm.invoke(messages)
        return response.content

    def generate_with_history(self, messages: list, system_prompt: str = None) -> str:
        # messages is list of dicts with 'role' and 'content'
        lc_messages = []
        if system_prompt:
            lc_messages.append(SystemMessage(content=system_prompt))
        for m in messages:
            if m['role'] == 'user':
                lc_messages.append(HumanMessage(content=m['content']))
            elif m['role'] == 'assistant':
                lc_messages.append(AIMessage(content=m['content']))
        response = self.llm.invoke(lc_messages)
        return response.content

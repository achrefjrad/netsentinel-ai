import os
from dotenv import load_dotenv

load_dotenv()


def get_llm(temperature: float = 0):
    provider = os.getenv("LLM_PROVIDER", "ollama")
    model = os.getenv("LLM_MODEL", "qwen2.5:3b")

    if provider == "ollama":
        from langchain_ollama import ChatOllama
        # num_ctx raised because Ollama's default context can truncate configs
        return ChatOllama(model=model, temperature=temperature, num_ctx=8192)
    raise ValueError(f"Unknown LLM_PROVIDER: {provider}")

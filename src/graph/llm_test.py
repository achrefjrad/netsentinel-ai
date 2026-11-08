from src.llm import get_llm

print(get_llm().invoke("Reply with: ready").content)

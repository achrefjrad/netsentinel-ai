from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    text: str


def hello(state: State) -> dict:
    return {"text": state["text"] + " -> graph works"}


g = StateGraph(State)
g.add_node("hello", hello)
g.add_edge(START, "hello")
g.add_edge("hello", END)

print(g.compile().invoke({"text": "NetSentinel"}))

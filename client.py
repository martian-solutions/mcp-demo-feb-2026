import asyncio
from typing import Any
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langchain_mcp_adapters.client import MultiServerMCPClient

SERVER_URL = "http://localhost:8000/mcp"
AUTH_TOKEN = "my-secret-token"


class State(TypedDict):
    history: list[dict[str, Any]]
    response: str


async def call_tool(state: State, chat_tool) -> State:
    result = await chat_tool.ainvoke({"history": state["history"]})
    if isinstance(result, list):
        text = result[0]["text"]
    else:
        text = result
    return {"response": text}


async def build_graph(chat_tool):
    async def node(state: State) -> State:
        return await call_tool(state, chat_tool)

    graph = StateGraph(State)
    graph.add_node("call_tool", node)
    graph.add_edge(START, "call_tool")
    graph.add_edge("call_tool", END)
    return graph.compile()


def find_tool(tools, name):
    for tool in tools:
        if tool.name == name:
            return tool
    raise ValueError(f"Tool '{name}' not found")


async def main():
    client = MultiServerMCPClient(
        {
            "rot13": {
                "url": SERVER_URL,
                "transport": "streamable_http",
                "headers": {"Authorization": f"Bearer {AUTH_TOKEN}"},
            }
        }
    )
    tools = await client.get_tools()
    chat_tool = find_tool(tools, "process_chat")
    graph = await build_graph(chat_tool)

    history = []
    print("Chat started. Type your message (Ctrl+C to quit):")

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        history.append({"role": "user", "content": user_input})
        result = await graph.ainvoke({"history": history})
        text = result["response"]
        print(f"Bot: {text}")
        history.append({"role": "assistant", "content": text})


if __name__ == "__main__":
    asyncio.run(main())

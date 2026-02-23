import asyncio

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END, MessagesState
from langchain_mcp_adapters.client import MultiServerMCPClient

SERVER_URL = "http://localhost:8141/mcp"
AUTH_TOKEN = "xxmy-secret-token"


def messages_as_dicts(messages):
    return [{"role": m.type, "content": m.content} for m in messages]


async def call_tool(state: MessagesState, chat_tool) -> MessagesState:
    history = messages_as_dicts(state["messages"])
    result = await chat_tool.ainvoke({"history": history})
    if isinstance(result, list):
        text = result[0]["text"]
    else:
        text = result
    return {"messages": [AIMessage(content=text)]}


async def build_graph(chat_tool):
    async def node(state: MessagesState) -> MessagesState:
        return await call_tool(state, chat_tool)

    graph = StateGraph(MessagesState)
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

    messages = []
    print("Chat started. Type your message (Ctrl+C to quit):")

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        messages.append(HumanMessage(content=user_input))
        result = await graph.ainvoke({"messages": messages})
        messages = result["messages"]
        text = messages[-1].content
        print(f"Bot: {text}")


if __name__ == "__main__":
    asyncio.run(main())

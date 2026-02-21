import asyncio
from typing import Any, List, TypedDict

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, START, END, MessagesState
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.callbacks import Callbacks, CallbackContext
from rich.console import Console
from rich.panel import Panel

console = Console()

SERVER_URL = "http://localhost:8080/mcp/"
AUTH_TOKEN = "demo-token"

# 1. Properly typed ASYNC callbacks
async def on_progress(progress: float, total: float | None, message: str | None, context: CallbackContext) -> None:
    # Print every detail for transparency
    console.print(f"[dim]PROGRESS EVENT: {progress}/{total} - {message} (Server: {context.server_name})[/dim]")
    if message:
        # Color code the streaming token in CYAN
        console.print(f"[cyan]{message.strip()}[/cyan]")

async def on_logging_message(params: Any, context: CallbackContext) -> None:
    console.print(f"[dim]LOG EVENT: {params.data} (Level: {params.level})[/dim]")

async def call_tool_node(state: MessagesState, chat_tool) -> MessagesState:
    # Based on the user's pattern: invoke the tool
    result = await chat_tool.ainvoke({})
    
    if isinstance(result, list):
        text = "".join([p.get("text", "") if isinstance(p, dict) else str(p) for p in result])
    else:
        text = str(result)
        
    return {"messages": [AIMessage(content=text)]}

async def build_graph(chat_tool):
    async def node(state: MessagesState) -> MessagesState:
        return await call_tool_node(state, chat_tool)

    graph = StateGraph(MessagesState)
    graph.add_node("call_anthem_tool", node)
    graph.add_edge(START, "call_anthem_tool")
    graph.add_edge("call_anthem_tool", END)
    return graph.compile()

def find_tool(tools, name):
    for tool in tools:
        if tool.name == name:
            return tool
    raise ValueError(f"Tool '{name}' not found")

async def main():
    console.print(f"[bold blue]Connecting to MCP Server at {SERVER_URL}...[/bold blue]")
    
    # Initialize correctly formatted callbacks
    callbacks = Callbacks(
        on_progress=on_progress,
        on_logging_message=on_logging_message
    )
    
    client = MultiServerMCPClient(
        {
            "anthem-server": {
                "url": SERVER_URL,
                "transport": "streamable_http",
                "headers": {"Authorization": f"Bearer {AUTH_TOKEN}"},
            }
        },
        callbacks=callbacks
    )
    
    try:
        tools = await client.get_tools()
    except Exception as e:
        console.print(f"[bold red]Failed to load tools: {e}[/bold red]")
        return

    chat_tool = find_tool(tools, "sing_anthem")
    graph = await build_graph(chat_tool)

    console.print("\n[bold magenta]Graph execution started. Watching for async callback events...[/bold magenta]\n")

    # Run the graph using ainvoke
    result = await graph.ainvoke({"messages": [HumanMessage(content="Sing the anthem!")]})
    
    # Final response in GREEN
    final_text = result["messages"][-1].content
    console.print()
    console.print(Panel(
        final_text, 
        title="[bold green]Final Response[/bold green]", 
        border_style="green"
    ))

    console.print("\n[bold blue]Python Client Done.[/bold blue]")

if __name__ == "__main__":
    asyncio.run(main())

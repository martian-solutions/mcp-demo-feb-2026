import os
import asyncio
from typing import Any, List, TypedDict

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, START, END, MessagesState
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.callbacks import Callbacks, CallbackContext
from rich.console import Console
from rich.panel import Panel

console = Console()

SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8081/mcp/")
AUTH_TOKEN = "song-token"

async def on_progress(progress: float, total: float | None, message: str | None, context: CallbackContext) -> None:
    if message:
        # Print tokens as they arrive in CYAN
        console.print(f"[cyan]{message}[/cyan]", end="")

async def call_song_tool_node(state: MessagesState, chat_tool) -> MessagesState:
    topic = state["messages"][-1].content
    
    # ainvoke the tool wrapper
    result = await chat_tool.ainvoke({"prompt": topic})
    
    # MultiServerMCPClient tool results are often list of dicts: [{'type': 'text', 'text': '...'}]
    if isinstance(result, list):
        text_parts = []
        for part in result:
            if isinstance(part, dict) and part.get("type") == "text":
                text_parts.append(part.get("text", ""))
            else:
                text_parts.append(str(part))
        text = "".join(text_parts)
    else:
        text = str(result)
        
    return {"messages": [AIMessage(content=text)]}

async def build_graph(chat_tool):
    async def node(state: MessagesState) -> MessagesState:
        return await call_song_tool_node(state, chat_tool)

    graph = StateGraph(MessagesState)
    graph.add_node("generate_song", node)
    graph.add_edge(START, "generate_song")
    graph.add_edge("generate_song", END)
    return graph.compile()

def find_tool(tools, name):
    for tool in tools:
        if tool.name == name:
            return tool
    raise ValueError(f"Tool '{name}' not found")

async def main():
    console.print(f"[bold blue]Connecting to Song Generator at {SERVER_URL}...[/bold blue]")
    
    callbacks = Callbacks(on_progress=on_progress)
    
    client = MultiServerMCPClient(
        {
            "song-server": {
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

    try:
        chat_tool = find_tool(tools, "generate_song")
    except ValueError as e:
        console.print(f"[bold red]{e}[/bold red]")
        return
        
    graph = await build_graph(chat_tool)

    try:
        topic = console.input("\n[bold green]Enter a topic for your bedtime song: [/bold green]")
        if not topic.strip():
            topic = "The joy of Go programming"
            
        console.print(f"\n[bold magenta]Generating lyrics for '{topic}'...[/bold magenta]\n")

        result = await graph.ainvoke({"messages": [HumanMessage(content=topic)]})
        
        if "messages" in result and result["messages"]:
            final_text = result["messages"][-1].content
            console.print("\n")
            console.print(Panel(
                final_text, 
                title=f"[bold green]Final Annotated Song: {topic}[/bold green]", 
                border_style="green"
            ))
    except (KeyboardInterrupt, EOFError):
        console.print("\n[bold yellow]Aborted by user.[/bold yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Error during execution: {e}[/bold red]")

    console.print("\n[bold blue]Done.[/bold blue]")

if __name__ == "__main__":
    asyncio.run(main())

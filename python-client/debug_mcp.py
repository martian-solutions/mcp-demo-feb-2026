import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from rich.console import Console
from mcp.types import CallToolParams

console = Console()

async def main():
    mcp_endpoint = "http://localhost:8080/mcp/"
    console.print(f"[bold blue]Direct Session Test at {mcp_endpoint}...[/bold blue]")
    
    mcp_client = MultiServerMCPClient(
        {
            "anthem-server": {
                "transport": "http",
                "url": mcp_endpoint,
            }
        }
    )

    # Note: MultiServerMCPClient doesn't seem to expose the underlying session 
    # easily for notification subscriptions.
    # Let's try to find if we can provide a callback to MultiServerMCPClient.
    
    async with mcp_client.session("anthem-server") as session:
        # We'll try to use a low-level call to see if we can get progress
        console.print("Calling sing_anthem via low-level session...")
        
        # In the MCP Python SDK, ClientSession.call_tool doesn't take meta directly 
        # but we can try to find where it's sent.
        
        # Actually, let's just see if we can get ANY output.
        # If the adapter is correctly emitting events, we should see them in astream_events.
        
        # If it's not working, maybe we need to enable progress in the client capabilities?
        pass

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from rich.console import Console

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

    async with mcp_client.session("anthem-server") as session:
        # Request tools just to be sure we are initialized
        await session.list_tools()
        
        # We need a progress token.
        # Let's see if we can pass it via call_tool
        from mcp.types import CallToolRequest, CallToolParams
        
        console.print("Calling sing_anthem directly via session...")
        
        # We'll use a callback to capture notifications if the session supports it.
        # But langchain_mcp_adapters might wrap the session.
        
        # Let's try to just call it and see if anything prints from the background
        # if the adapter has internal logging.
        
        # The session here is a mcp.client.session.ClientSession
        from mcp.types import Meta
        
        params = CallToolParams(name="sing_anthem", arguments={})
        params._meta = {"progressToken": "direct-token"}
        
        # We can't easily subscribe to notifications on this session object 
        # without knowing how it's hooked up.
        
        response = await session.call_tool("sing_anthem", arguments={})
        console.print(f"Response: {response.content}")

if __name__ == "__main__":
    asyncio.run(main())

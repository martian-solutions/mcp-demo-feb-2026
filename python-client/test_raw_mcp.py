import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from rich.console import Console

console = Console()

async def main():
    url = "http://localhost:8080/mcp/"
    console.print(f"[blue]Connecting to SSE at {url}...[/blue]")
    
    async with sse_client(url) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()
            
            # Subscribe to logs
            await session.set_logging_level("info")
            
            # Listen for notifications in background
            async def listen():
                async for notification in session.incoming_notifications:
                    console.print(f"[yellow]Notification:[/yellow] {notification}")

            listener = asyncio.create_task(listen())
            
            console.print("Calling sing_anthem...")
            # Tool call
            result = await session.call_tool("sing_anthem", arguments={})
            console.print(f"[green]Result received.[/green]")
            # console.print(result)
            
            await asyncio.sleep(1) # wait for final logs
            listener.cancel()

if __name__ == "__main__":
    asyncio.run(main())

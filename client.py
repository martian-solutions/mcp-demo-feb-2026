import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient

SERVER_URL = "http://localhost:8000/mcp"
AUTH_TOKEN = "my-secret-token"


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
    chat_tool = next(t for t in tools if t.name == "process_chat")

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
        result = await chat_tool.ainvoke({"history": history})
        # result is a list of content blocks; extract the text from the first one
        text = result[0]["text"] if isinstance(result, list) else result
        print(f"Bot: {text}")
        history.append({"role": "assistant", "content": text})


if __name__ == "__main__":
    asyncio.run(main())

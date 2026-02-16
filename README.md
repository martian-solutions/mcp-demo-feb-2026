# LangGraph MCP Demo

A minimal demo of a LangGraph MCP client talking to a custom MCP server. The server exposes a single tool that rot13-encodes the newest message in a chat history.

## Setup

```bash
pip install -r requirements.txt
```

## Running

Start the server in one terminal:

```bash
python server.py
```

Start the client in another:

```bash
python client.py
```

## How it works

- **`server.py`**: A FastMCP server with one tool, `process_chat`, that accepts a full chat history and returns the rot13-encoded content of the most recent message.
- **`client.py`**: A LangGraph `MultiServerMCPClient` that connects to the server over HTTP with a Bearer token, maintains chat history across turns, and sends the full history on each prompt.

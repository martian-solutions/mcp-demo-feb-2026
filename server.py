import codecs
import json
from typing import Any

from mcp.server.auth.middleware.bearer_auth import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.server import Context

VALID_TOKEN = "my-secret-token"


class StaticTokenVerifier(TokenVerifier):
    async def verify_token(self, token: str) -> AccessToken | None:
        if token != VALID_TOKEN:
            return None
        return AccessToken(token=token, client_id="demo-client", scopes=[])


mcp = FastMCP(
    "rot13-server",
    host="0.0.0.0",
    port=8000,
    token_verifier=StaticTokenVerifier(),
    auth=AuthSettings(
        issuer_url="http://localhost:8000",
        resource_server_url="http://localhost:8000",
    ),
)


@mcp.tool()
def process_chat(history: list[dict[str, Any]], ctx: Context) -> str:
    """Rot13 encodes the content of the newest message in the chat history."""
    user = ctx.request_context.request.user
    token = user.access_token.token if hasattr(user, "access_token") else "(unauthenticated)"
    print(f"\nAuth token: {token}")
    print("Chat history:")
    print(json.dumps(history, indent=2))

    if not history:
        return ""
    newest = history[-1]
    content = newest.get("content", "")
    return codecs.encode(content, "rot_13")


if __name__ == "__main__":
    mcp.run(transport="streamable-http")

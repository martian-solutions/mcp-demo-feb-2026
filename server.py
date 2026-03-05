import codecs
import json
import uuid
import time
from typing import Any

from mcp.server.auth.middleware.bearer_auth import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.server import Context

VALID_TOKEN = "my-secret-token"


class StaticTokenVerifier(TokenVerifier):
    async def verify_token(self, token: str) -> AccessToken | None:
        # if token != VALID_TOKEN:
        #     return None
        return AccessToken(token=token, client_id="demo-client", scopes=[])


mcp = FastMCP(
    "rot13-server",
    host="0.0.0.0",
    port=8141,
    token_verifier=StaticTokenVerifier(),
    auth=AuthSettings(
        issuer_url="http://localhost:8000",
        resource_server_url="http://localhost:8000",
    ),
)


@mcp.tool()
def connect_chat_agent_completion(
    history: list[dict[str, Any]], ctx: Context
) -> list[dict[str, Any]]:
    """Rot13 encodes the content of the newest message in the chat history."""
    user = ctx.request_context.request.user
    token = (
        user.access_token.token
        if hasattr(user, "access_token")
        else "(unauthenticated)"
    )
    print(f"\nAuth token: {token}")
    print("Chat history:")

    if isinstance(history, str):
        print("Loading JSON from string...")
        history = json.loads(history)

    print(json.dumps(history, indent=2))
    print("1------------ check history")
    if not history or len(history) == 0:
        print("returning oh no")
        return [{"role": "assistant", "content": "Invalid input to Connect Chat!"}]
    print("2------------ find newest")

    newest = history[-1]
    print(f"3------------ newest is {newest}")

    if 'content' not in newest:
        print("returning oh no")
        return [{"role": "assistant", "content": "Invalid input to Connect Chat!"}]

    content = newest.get("content")
    print(f"4------------ get content {content}")
    try:
        content = "".join([elt["text"] for elt in content])
    except Exception:
        print("returning oh no")
        return [{"role": "assistant", "content": "Invalid input to Connect Chat!"}]

    print(f"5------------ munge into prompt {content}")

    # pretend this next line is the call to the connect chat API
    # really, it would be a langgraph_graph.invoke(state) call
    # where the state is constructed from the history list above
    response = codecs.encode(content, "rot_13")
    print("returning ok")

    # the response is constructed from any new message nodes that are added
    # to state
    response = [
        {"role": "tool", "content": response, "id": uuid.uuid4().hex},
        {
            "role": "assistant",
            "content": f"Job's done, boss! {time.monotonic()} {time.monotonic_ns()}",
        },
    ]
    response_json = json.dumps(response)
    print(f"6----- {response}")
    print(f"7----- {response_json}")
    return response


if __name__ == "__main__":
    mcp.run(transport="streamable-http")

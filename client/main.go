package main

import (
	"context"
	"fmt"
	"log"
	"time"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

func runAnthemClient(ctx context.Context, endpoint string) {
	fmt.Printf("\n--- Connecting to Anthem MCP at %s ---\n", endpoint)

	transport := &mcp.StreamableClientTransport{
		Endpoint: endpoint,
	}

	client := mcp.NewClient(&mcp.Implementation{
		Name:    "anthem-client",
		Version: "1.0.0",
	}, &mcp.ClientOptions{
		ProgressNotificationHandler: func(ctx context.Context, req *mcp.ProgressNotificationClientRequest) {
			// Print the streamed line
			fmt.Print(req.Params.Message)
		},
	})

	session, err := client.Connect(ctx, transport, nil)
	if err != nil {
		log.Fatalf("failed to connect: %v", err)
	}
	defer session.Close()

	params := &mcp.CallToolParams{
		Meta:      mcp.Meta{},
		Name:      "sing_anthem",
		Arguments: map[string]any{},
	}
	params.SetProgressToken("anthem-token")

	callCtx, cancel := context.WithTimeout(ctx, 60*time.Second)
	defer cancel()

	fmt.Printf("Starting the anthem...\n")
	res, err := session.CallTool(callCtx, params)
	if err != nil {
		fmt.Printf("\nCall failed: %v\n", err)
	} else {
		fmt.Printf("\n--- Final Complete Song ---\n")
		fmt.Printf("%v\n", res.Content[0].(*mcp.TextContent).Text)
	}
}

func main() {
	ctx := context.Background()

	// Connect to the HTTP server
	runAnthemClient(ctx, "http://localhost:8080/mcp/")

	fmt.Println("\nAnthem Demo finished.")
}

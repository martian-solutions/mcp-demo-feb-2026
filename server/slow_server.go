package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

type ProcessArgs struct {
	Name string `json:"name"`
	Secs int    `json:"secs"`
}

func main() {
	f, _ := os.OpenFile("server_slow.log", os.O_RDWR|os.O_CREATE|os.O_APPEND, 0666)
	defer f.Close()
	logger := log.New(f, "[SLOW] ", log.LstdFlags)

	s := mcp.NewServer(&mcp.Implementation{
		Name:    "slow-server",
		Version: "1.0.0",
	}, nil)

	mcp.AddTool(s, &mcp.Tool{
		Name:        "long_running_task",
		Description: "Simulates a long process with status updates",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args ProcessArgs) (*mcp.CallToolResult, any, error) {
		token := req.GetParams().(mcp.RequestParams).GetProgressToken()
		logger.Printf("Task %s starting for %d secs. Token: %v", args.Name, args.Secs, token)

		if token != nil {
			for i := 1; i <= args.Secs; i++ {
				status := fmt.Sprintf("Processing %s: step %d/%d... ", args.Name, i, args.Secs)
				req.Session.NotifyProgress(ctx, &mcp.ProgressNotificationParams{
					ProgressToken: token,
					Progress:      float64(i),
					Total:         float64(args.Secs),
					Message:       status,
				})
				time.Sleep(1 * time.Second)
			}
		}

		return &mcp.CallToolResult{
			Content: []mcp.Content{&mcp.TextContent{Text: "Task " + args.Name + " completed."}},
		}, nil, nil
	})

	if err := s.Run(context.Background(), &mcp.StdioTransport{}); err != nil {
		logger.Fatalf("Exit: %v", err)
	}
}

package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"strings"
	"time"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

var anthemLines = []string{
	"Oh, say can you see by the dawn's early light\n",
	"What so proudly we hailed at the twilight's last gleaming?\n",
	"Whose broad stripes and bright stars through the perilous fight,\n",
	"O'er the ramparts we watched were so gallantly streaming?\n",
	"And the rocket's red glare, the bombs bursting in air,\n",
	"Gave proof through the night that our flag was still there.\n",
	"Oh, say does that star-spangled banner yet wave\n",
	"O'er the land of the free and the home of the brave?\n",
}

func main() {
	s := mcp.NewServer(&mcp.Implementation{
		Name:    "anthem-server",
		Version: "1.0.0",
	}, nil)

	mcp.AddTool(s, &mcp.Tool{
		Name:        "sing_anthem",
		Description: "Streams the Star Spangled Banner and returns the full lyrics with historical context",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args any) (*mcp.CallToolResult, any, error) {
		params := req.GetParams().(mcp.RequestParams)
		token := params.GetProgressToken()
		if token == nil {
			token = "demo-token"
		}

		// 1. Stream the PLAIN lines as progress notifications
		for i, line := range anthemLines {
			select {
			case <-ctx.Done():
				return nil, nil, ctx.Err()
			default:
				_ = req.Session.NotifyProgress(ctx, &mcp.ProgressNotificationParams{
					ProgressToken: token,
					Progress:      float64(i + 1),
					Total:         float64(len(anthemLines)),
					Message:       line,
				})
				time.Sleep(500 * time.Millisecond)
			}
		}

		// 2. Construct the FINAL response with flavor text and emojis
		var sb strings.Builder
		sb.WriteString("📜 HISTORICAL CONTEXT:\n")
		sb.WriteString("The 'Star-Spangled Banner' was written by Francis Scott Key in September 1814 ")
		sb.WriteString("after he witnessed the British bombardment of Fort McHenry during the War of 1812. ")
		sb.WriteString("It was officially adopted as the U.S. National Anthem in 1931. 🇺🇸✨\n\n")

		// Interspersing emojis for the final output
		emojis := []string{"🇺🇸", "🌅", "⭐", "🛡️", "🚀", "💥", "🚩", "🦅"}
		for i, line := range anthemLines {
			emoji := "🇺🇸"
			if i < len(emojis) {
				emoji = emojis[i]
			}
			sb.WriteString(strings.TrimSpace(line) + " " + emoji + "\n")
		}
		sb.WriteString("\n🎆 Let freedom ring! 🎆")

		return &mcp.CallToolResult{
			Content: []mcp.Content{&mcp.TextContent{Text: sb.String()}},
		}, nil, nil
	})

	handler := mcp.NewStreamableHTTPHandler(func(req *http.Request) *mcp.Server {
		return s
	}, nil)

	http.Handle("/mcp/", handler)

	fmt.Println("Anthem MCP Server starting on http://localhost:8080/mcp/")
	if err := http.ListenAndServe(":8080", nil); err != nil {
		log.Fatal(err)
	}
}

package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strings"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

const (
	OllamaURL = "http://localhost:11434/api/generate"
	ModelName = "gemma3:12b-it-qat"
)

type SongArgs struct {
	Prompt string `json:"prompt"`
}

type OllamaResponse struct {
	Response string `json:"response"`
	Done     bool   `json:"done"`
}

func main() {
	// 1. Setup Logging
	f, _ := os.OpenFile("song_server.log", os.O_RDWR|os.O_CREATE|os.O_APPEND, 0666)
	defer f.Close()
	logger := log.New(f, "[SONG-GEN] ", log.LstdFlags)
	logger.Println("Server starting...")

	s := mcp.NewServer(&mcp.Implementation{
		Name:    "song-generation-server",
		Version: "1.0.0",
	}, nil)

	mcp.AddTool(s, &mcp.Tool{
		Name:        "generate_song",
		Description: "Generates a custom song using Gemma and streams it via progress notifications",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args SongArgs) (*mcp.CallToolResult, any, error) {
		params := req.GetParams().(mcp.RequestParams)
		token := params.GetProgressToken()
		if token == nil {
			token = "song-gen-token"
		}

		logger.Printf("Generating song for prompt: %s", args.Prompt)

		// 1. Generate the initial song from Gemma (Streaming)
		lyricsPrompt := fmt.Sprintf("Write a song about: %s. The song should have at least 10 lines. Just the lyrics, please. No talk, just song.", args.Prompt)
		
		var rawLyrics strings.Builder
		err := streamFromOllama(ctx, lyricsPrompt, func(chunk string) {
			rawLyrics.WriteString(chunk)
			// Send progress notification for every chunk/token
			_ = req.Session.NotifyProgress(ctx, &mcp.ProgressNotificationParams{
				ProgressToken: token,
				Progress:      0, // indeterminate progress
				Message:       chunk,
			})
		})
		if err != nil {
			logger.Printf("Streaming error: %v", err)
			return nil, nil, fmt.Errorf("failed to generate lyrics: %v", err)
		}

		logger.Println("Initial lyrics generated. Starting refinement...")

		// 2. Refinement step (Non-streaming)
		refinePrompt := fmt.Sprintf(`Here is a song:
%s

Please refine this song by:
1. Adding relevant emojis throughout the lyrics.
2. Adding a section at the beginning titled "CONTEXT & FEELINGS" describing the intended mood and your thoughts on the original prompt: "%s".
Return the full annotated song. Do not include any meta-talk about your instructions.`, rawLyrics.String(), args.Prompt)

		refinedContent, err := callOllama(ctx, refinePrompt)
		if err != nil {
			logger.Printf("Refinement error: %v", err)
			return nil, nil, fmt.Errorf("failed to refine lyrics: %v", err)
		}

		logger.Println("Refinement complete.")
		return &mcp.CallToolResult{
			Content: []mcp.Content{&mcp.TextContent{Text: refinedContent}},
		}, nil, nil
	})

	handler := mcp.NewStreamableHTTPHandler(func(req *http.Request) *mcp.Server {
		return s
	}, nil)

	// Support both /mcp and /mcp/
	http.Handle("/mcp", handler)
	http.Handle("/mcp/", handler)

	addr := ":8081"
	fmt.Printf("Song Generation Server listening on http://localhost%s/mcp/\n", addr)
	if err := http.ListenAndServe(addr, nil); err != nil {
		log.Fatal(err)
	}
}

func streamFromOllama(ctx context.Context, prompt string, onToken func(string)) error {
	body, _ := json.Marshal(map[string]any{
		"model":  ModelName,
		"prompt": prompt,
		"stream": true,
	})

	req, _ := http.NewRequestWithContext(ctx, "POST", OllamaURL, bytes.NewBuffer(body))
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("ollama returned status %d", resp.StatusCode)
	}

	scanner := bufio.NewScanner(resp.Body)
	for scanner.Scan() {
		var part OllamaResponse
		if err := json.Unmarshal(scanner.Bytes(), &part); err != nil {
			continue
		}
		onToken(part.Response)
		if part.Done {
			break
		}
	}
	return scanner.Err()
}

func callOllama(ctx context.Context, prompt string) (string, error) {
	body, _ := json.Marshal(map[string]any{
		"model":  ModelName,
		"prompt": prompt,
		"stream": false,
	})

	req, _ := http.NewRequestWithContext(ctx, "POST", OllamaURL, bytes.NewBuffer(body))
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("ollama returned status %d", resp.StatusCode)
	}

	var result OllamaResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return "", err
	}
	return result.Response, nil
}

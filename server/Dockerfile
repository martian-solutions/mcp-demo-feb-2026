FROM golang:1.23-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN go build -o song_server server/song_server.go

FROM alpine:latest
WORKDIR /app
COPY --from=builder /app/song_server .
EXPOSE 8081
CMD ["./song_server"]

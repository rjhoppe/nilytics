# Build stage (context must be repo root: docker-compose uses context: .)
FROM golang:1.24-alpine AS builder
WORKDIR /app

COPY go.mod ./
RUN go mod download

COPY app/api ./app/api
COPY data/models ./data/models
RUN CGO_ENABLED=0 go build -o server ./app/api

# Run stage
FROM alpine:3.21
WORKDIR /app
COPY --from=builder /app/server .

EXPOSE 8080
CMD ["./server"]

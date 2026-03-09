# API

Go HTTP API (stdlib, no Gin). Reads from Postgres and returns JSON shaped by the shared proto schema.

## Build

**Generate Go from the proto first** (required before building or running):

```bash
# From repo root
make proto
```

Requires:

- `protoc` (e.g. `brew install protobuf`)
- `protoc-gen-go`: `go install google.golang.org/protobuf/cmd/protoc-gen-go@latest`  
  Ensure `$GOBIN` or `$GOPATH/bin` is on your `PATH`.

This generates `data/models/player.pb.go` from [data/models/player.proto](../../data/models/player.proto). The API uses these types for DB results and JSON responses; do not hand-edit the generated file.

Build/run from repo root (the Go module is at root): `go build ./app/api`, or use Docker (build context is repo root; see [docker-compose.yaml](../../docker-compose.yaml)).

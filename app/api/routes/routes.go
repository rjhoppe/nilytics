package routes

import (
	"encoding/json"
	"log"
	"net/http"

	"nilytics/app/api/internal/database"
	"nilytics/app/api/internal/pb"
)

func Register(mux *http.ServeMux, db *database.DB) {
	mux.HandleFunc("GET /health", healthHandler)
	mux.HandleFunc("GET /players", listPlayersHandler(db))
}

func listPlayersHandler(db *database.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		players, err := db.ListPlayers(r.Context())
		if err != nil {
			log.Printf("ListPlayers: %v", err)
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusInternalServerError)
			_ = json.NewEncoder(w).Encode(map[string]string{"error": "failed to list players"})
			return
		}
		if players == nil {
			players = []*pb.Player{}
		}
		w.Header().Set("Content-Type", "application/json")
		if err := json.NewEncoder(w).Encode(players); err != nil {
			log.Printf("Encode players: %v", err)
		}
	}
}

// TODO: Implement func to pull projection for player for current season
func playerHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Write([]byte(`{"status":"ok - testing"}`))
}

// TODO: Implement func to pull projection for team for current season
func teamHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Write([]byte(`{"status":"ok - testing"}`))
}

// TODO: Implement func to pull most overvalued players per their projected performance in relation to NIL demands
func overratedHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Write([]byte(`{"status":"ok - testing"}`))
}

// TODO: Implement func to pull best value players per their projected performance in relation to NIL demands
func bestValueHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Write([]byte(`{"status":"ok - testing"}`))
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Write([]byte(`{"status":"ok"}`))
}
package main

import (
	"log"
	"net/http"

	"nilytics/app/api/internal/database"
	"nilytics/app/api/routes"
)

func main() {
	db, err := database.Open()
	if err != nil {
		log.Fatalf("Database: %v", err)
	}
	defer db.Pool.Close()

	mux := http.NewServeMux()
	routes.Register(mux, db)

	addr := ":8080"
	log.Printf("Starting server on %s", addr)
	if err := http.ListenAndServe(addr, mux); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
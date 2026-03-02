package database

import (
	"context"
	"database/sql"
	"fmt"
	"os"

	"nilytics/app/api/internal/pb"

	_ "github.com/jackc/pgx/v5/stdlib"
)

// DB holds the database pool for the API.
type DB struct {
	Pool *sql.DB
}

// Open opens a Postgres connection using DB_* env vars (same as the scrape service).
// Returns an error if connection fails.
func Open() (*DB, error) {
	connStr := fmt.Sprintf(
		"postgres://%s:%s@%s:%s/%s?sslmode=disable",
		getEnv("DB_USER", ""),
		getEnv("DB_PASSWORD", ""),
		getEnv("DB_HOST", "localhost"),
		getEnv("DB_PORT", "5432"),
		getEnv("DB_NAME", ""),
	)
	pool, err := sql.Open("pgx", connStr)
	if err != nil {
		return nil, fmt.Errorf("database open: %w", err)
	}
	if err := pool.Ping(); err != nil {
		_ = pool.Close()
		return nil, fmt.Errorf("database ping: %w", err)
	}
	return &DB{Pool: pool}, nil
}

func getEnv(key, def string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return def
}

// ListPlayers returns all players from the players table as proto-backed structs.
func (db *DB) ListPlayers(ctx context.Context) ([]*pb.Player, error) {
	rows, err := db.Pool.QueryContext(ctx, `
		SELECT player_id, player_name, profile_url, position, rating, status,
		       highschool, height, weight, old_school, new_school
		FROM players
		ORDER BY player_id
	`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var out []*pb.Player
	for rows.Next() {
		var (
			playerID   int
			playerName, profileURL, position, rating, status sql.NullString
			highschool, height, weight, oldSchool, newSchool sql.NullString
		)
		if err := rows.Scan(
			&playerID, &playerName, &profileURL, &position, &rating, &status,
			&highschool, &height, &weight, &oldSchool, &newSchool,
		); err != nil {
			return nil, err
		}
		out = append(out, &pb.Player{
			PlayerId:   fmt.Sprint(playerID),
			PlayerName: nullStr(playerName),
			ProfileUrl: nullStr(profileURL),
			Position:   nullStr(position),
			Rating:     nullStr(rating),
			Status:     nullStr(status),
			Highschool: nullStr(highschool),
			Height:     nullStr(height),
			Weight:     nullStr(weight),
			OldSchool:  nullStr(oldSchool),
			NewSchool:  nullStr(newSchool),
		})
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return out, nil
}

func nullStr(n sql.NullString) string {
	if n.Valid {
		return n.String
	}
	return ""
}

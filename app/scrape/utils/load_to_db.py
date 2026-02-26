import os
import pandas as pd
import psycopg2
from psycopg2 import sql

# --- Database Configuration ---
# It's recommended to set these as environment variables
DB_NAME = os.getenv("DB_NAME")

# Single source of truth: CSV header -> DB/proto field (matches data.models.player_pb2.Player).
# Order matches INSERT column order for players table.
CSV_PLAYER_COLUMNS = {
    'Player Name': 'player_name',
    '247Sports Profile URL': 'profile_url',
    'Position': 'position',
    'Rating': 'rating',
    'Status': 'status',
    'Highschool': 'highschool',
    'Height': 'height',
    'Weight': 'weight',
    'Old School': 'old_school',
    'New School': 'new_school',
}
REQUIRED_CSV_COLUMNS = list(CSV_PLAYER_COLUMNS.keys())

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")


def parse_seasonal_column(col: str) -> tuple[str, str] | None:
    """
    If col is a seasonal stat column like "Points Per Game (2024-5)", returns (stat_name, season_year).
    Otherwise returns None.
    """
    if " (" not in col or not col.endswith(")"):
        return None
    stat_name, rest = col.rsplit(" (", 1)
    season_part = rest[:-1]  # drop trailing )
    if len(season_part) < 6 or season_part[4] != "-":
        return None
    year1, _, year2 = season_part.partition("-")
    if not (year1.isdigit() and len(year1) == 4 and year2.isdigit() and 1 <= len(year2) <= 2):
        return None
    return (stat_name.strip(), season_part)


def validate_csv_structure(csv_path):
    """
    Validates that the CSV has the required columns before any DB work.
    Raises FileNotFoundError if the file does not exist.
    Raises ValueError if required columns are missing or no seasonal stat columns exist.
    """
    df = pd.read_csv(csv_path, nrows=0)
    columns = set(df.columns)
    required = set(REQUIRED_CSV_COLUMNS)
    missing = required - columns
    if missing:
        raise ValueError(
            f"CSV missing required columns: {sorted(missing)}. "
            f"Required: {sorted(required)}"
        )

    seasonal_columns = [c for c in columns if parse_seasonal_column(c) is not None]
    if not seasonal_columns:
        raise ValueError(
            "CSV has no seasonal stat columns. "
            "Expected columns matching pattern: 'Stat Name (YYYY-N)' (e.g. 'Points Per Game (2024-5)')."
        )


def get_db_connection():
    """Establishes and returns a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        print("Database connection established successfully.")
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error: Could not connect to the database. Please check your connection details and ensure the database is running.")
        print(f"Details: {e}")
        return None

def convert_to_type(value, target_type):
    """Safely converts a value to a target type (int or float), returning None on failure."""
    if pd.isna(value):
        return None
    try:
        return target_type(value)
    except (ValueError, TypeError):
        return None

def insert_player_data(conn, player_row):
    """
    Inserts a player's static data into the 'players' table if they don't already exist.
    Returns the player's ID (either existing or newly created).
    """
    static_data = {db_field: player_row.get(csv_col) for csv_col, db_field in CSV_PLAYER_COLUMNS.items()}
    profile_url = static_data['profile_url']
    player_id = None

    with conn.cursor() as cur:
        # Check if player already exists
        cur.execute("SELECT player_id FROM players WHERE profile_url = %s;", (profile_url,))
        result = cur.fetchone()
        
        if result:
            player_id = result[0]
            print(f"Player '{static_data['player_name']}' already exists with ID: {player_id}.")
        else:
            # Insert new player
            insert_sql = sql.SQL("""
                INSERT INTO players (player_name, profile_url, position, rating, status, highschool, height, weight, old_school, new_school)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING player_id;
            """)
            cur.execute(insert_sql, tuple(static_data.values()))
            player_id = cur.fetchone()[0]
            print(f"Inserted new player '{static_data['player_name']}' with ID: {player_id}.")
            
    return player_id

def insert_season_stats(conn, player_id, season_year, stats_row):
    """Inserts a player's seasonal stats into the 'player_season_stats' table."""
    
    stats_data = {
        'player_id': player_id,
        'season_year': season_year,
        'games_played': convert_to_type(stats_row.get('Games Played'), int),
        'minutes_played': convert_to_type(stats_row.get('Minutes Played'), float),
        'points_per_game': convert_to_type(stats_row.get('Points Per Game'), float),
        'rebounds_per_game': convert_to_type(stats_row.get('Rebounds Per Game'), float),
        'assists_per_game': convert_to_type(stats_row.get('Assists Per Game'), float),
        'blocks_per_game': convert_to_type(stats_row.get('Blocks Per Game'), float),
        'steals_per_game': convert_to_type(stats_row.get('Steals Per Game'), float),
        'field_goal_percentage': convert_to_type(stats_row.get('Field Goal Percentage'), float),
        'three_point_percentage': convert_to_type(stats_row.get('3 Point Field Goal Percentage'), float),
        'free_throw_percentage': convert_to_type(stats_row.get('Free Throw Percentage'), float),
    }

    with conn.cursor() as cur:
        insert_sql = sql.SQL("""
            INSERT INTO player_season_stats (player_id, season_year, games_played, minutes_played, points_per_game, rebounds_per_game, assists_per_game, blocks_per_game, steals_per_game, field_goal_percentage, three_point_percentage, free_throw_percentage)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (player_id, season_year) DO NOTHING;
        """)
        cur.execute(insert_sql, tuple(stats_data.values()))

def load_data_from_csv(csv_path):
    """Main function to read a CSV, transform the data, and load it into the database."""
    try:
        validate_csv_structure(csv_path)
    except FileNotFoundError:
        print(f"Error: The file '{csv_path}' was not found.")
        return
    except ValueError as e:
        print(f"Error: Invalid CSV structure. {e}")
        return

    conn = get_db_connection()
    if conn is None:
        return

    try:
        df = pd.read_csv(csv_path)

        for _, row in df.iterrows():
            player_id = insert_player_data(conn, row)

            if player_id is None:
                print(f"Skipping stats for player '{row.get('Player Name')}' due to missing ID.")
                continue

            # --- Transform from wide to long format ---
            seasonal_stats = {}
            for col_name, value in row.items():
                parsed = parse_seasonal_column(col_name)
                if parsed is not None:
                    stat_name, season_year = parsed
                    if season_year not in seasonal_stats:
                        seasonal_stats[season_year] = {}
                    seasonal_stats[season_year][stat_name] = value
            
            # --- Insert each season's stats ---
            for season, stats in seasonal_stats.items():
                insert_season_stats(conn, player_id, season, stats)
                
        conn.commit()
        print("\nData loading process completed successfully.")

    except FileNotFoundError:
        print(f"Error: The file '{csv_path}' was not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == '__main__':
    # We will use the test data file generated by the scraper
    load_data_from_csv('test_transfer_data.csv')

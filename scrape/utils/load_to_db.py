import os
import re
import pandas as pd
import psycopg2
from psycopg2 import sql

# --- Database Configuration ---
# It's recommended to set these as environment variables
DB_NAME = os.getenv("DB_NAME", "cbb_transfers")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

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
    player_id = None
    # Use profile_url as the unique identifier for a player
    profile_url = player_row.get('247Sports Profile URL')

    static_data = {
        'player_name': player_row.get('Player Name'),
        'profile_url': profile_url,
        'position': player_row.get('Position'),
        'rating': player_row.get('Rating'),
        'status': player_row.get('Status'),
        'highschool': player_row.get('Highschool'),
        'height': player_row.get('Height'),
        'weight': player_row.get('Weight'),
        'old_school': player_row.get('Old School'),
        'new_school': player_row.get('New School'),
    }

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
    conn = get_db_connection()
    if conn is None:
        return

    try:
        df = pd.read_csv(csv_path)
        
        # Regex to find all seasonal stat columns
        stat_pattern = re.compile(r'^(.*) \((\d{4}-\d{1,2})\)$')
        
        for index, row in df.iterrows():
            player_id = insert_player_data(conn, row)
            
            if player_id is None:
                print(f"Skipping stats for player '{row.get('Player Name')}' due to missing ID.")
                continue

            # --- Transform from wide to long format ---
            seasonal_stats = {}
            for col_name, value in row.items():
                match = stat_pattern.match(col_name)
                if match:
                    stat_name = match.group(1)
                    season_year = match.group(2)
                    
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

import os
import tempfile
import unittest
import psycopg2
from psycopg2.extras import RealDictCursor
from app.scrape.utils import load_to_db
from data.models import player_pb2

# --- Database Configuration for Testing ---
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")


class TestCsvValidation(unittest.TestCase):
    """Tests for validate_csv_structure and parse_seasonal_column (no DB required)."""

    def test_parse_seasonal_column_valid(self):
        self.assertEqual(
            load_to_db.parse_seasonal_column("Points Per Game (2024-5)"),
            ("Points Per Game", "2024-5"),
        )
        self.assertEqual(
            load_to_db.parse_seasonal_column("Games Played (2023-24)"),
            ("Games Played", "2023-24"),
        )
        self.assertEqual(
            load_to_db.parse_seasonal_column("3 Point Field Goal Percentage (2024-5)"),
            ("3 Point Field Goal Percentage", "2024-5"),
        )

    def test_parse_seasonal_column_invalid(self):
        self.assertIsNone(load_to_db.parse_seasonal_column("Games Played (TOTAL)"))
        self.assertIsNone(load_to_db.parse_seasonal_column("Player Name"))
        self.assertIsNone(load_to_db.parse_seasonal_column(""))
        self.assertIsNone(load_to_db.parse_seasonal_column("No parens here"))

    def test_validate_csv_structure_valid(self):
        """Valid CSV with required columns and at least one seasonal stat column passes."""
        valid_path = os.path.join(os.path.dirname(__file__), "output", "test_transfer_data.csv")
        if not os.path.isfile(valid_path):
            self.skipTest("test_transfer_data.csv not found")
        load_to_db.validate_csv_structure(valid_path)

    def test_validate_csv_structure_missing_columns(self):
        """CSV missing required columns raises ValueError with missing names."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("Player Name,Position,Rating\n")  # missing most required
            f.write("Alice,PG,99\n")
            path = f.name
        try:
            with self.assertRaises(ValueError) as ctx:
                load_to_db.validate_csv_structure(path)
            self.assertIn("CSV missing required columns", str(ctx.exception))
            self.assertIn("247Sports Profile URL", str(ctx.exception))
        finally:
            os.unlink(path)

    def test_validate_csv_structure_no_seasonal_columns(self):
        """CSV with all player columns but no seasonal stat columns raises ValueError."""
        headers = ",".join(load_to_db.REQUIRED_CSV_COLUMNS)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(headers + "\n")
            f.write("Alice,http://x.com/1,PG,99,Enrolled,N/A,6-0,180,Old,New\n")
            path = f.name
        try:
            with self.assertRaises(ValueError) as ctx:
                load_to_db.validate_csv_structure(path)
            self.assertIn("no seasonal stat columns", str(ctx.exception))
        finally:
            os.unlink(path)

    def test_validate_csv_structure_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            load_to_db.validate_csv_structure("/nonexistent/path/to/file.csv")


class TestDatabaseLoader(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up a database connection and create a clean slate before tests run."""
        try:
            cls.conn = psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT
            )
            with cls.conn.cursor() as cur:
                # Clear any existing data from previous runs
                cur.execute("TRUNCATE TABLE player_season_stats, players RESTART IDENTITY CASCADE;")
                cls.conn.commit()
        except psycopg2.OperationalError as e:
            raise unittest.SkipTest(f"Database connection failed. Skipping tests. Details: {e}")

    @classmethod
    def tearDownClass(cls):
        """Close the database connection after all tests have run."""
        if hasattr(cls, 'conn') and cls.conn:
            cls.conn.close()

    def test_data_loading_and_verification(self):
        """
        Runs the main loader function and then verifies the data in the database.
        """
        # 1. Run the loader function
        print("\n--- Running Data Loader ---")
        # The test file is now expected to be in the same directory as this test script
        test_csv_path = os.path.join(os.path.dirname(__file__), 'test_transfer_data.csv')
        load_to_db.load_data_from_csv(test_csv_path)
        print("--- Data Loader Finished ---\n")

        # 2. Verify the data
        print("--- Running Verifications ---")
        with self.conn.cursor() as cur:
            # Verify number of players
            cur.execute("SELECT COUNT(*) FROM players;")
            player_count = cur.fetchone()[0]
            self.assertGreater(player_count, 0, "No players were inserted.")
            print(f"Verified: {player_count} players inserted.")

            # Verify number of season stat entries
            cur.execute("SELECT COUNT(*) FROM player_season_stats;")
            stats_count = cur.fetchone()[0]
            self.assertGreater(stats_count, 0, "No season stats were inserted.")
            print(f"Verified: {stats_count} season stat records inserted.")

            # Verify specific data for Kadary Richmond
            cur.execute("SELECT position, old_school, new_school FROM players WHERE player_name = 'Kadary Richmond';")
            pos, old_school, new_school = cur.fetchone()
            
            self.assertEqual(pos, 'PG')
            self.assertEqual(old_school, 'Seton Hall')
            self.assertEqual(new_school, "St. John's")
            print("Verified specific data for Kadary Richmond.")

            # Verify a specific season stat for Yaxel Lendeborg
            cur.execute("""
                SELECT pss.points_per_game, pss.rebounds_per_game
                FROM player_season_stats pss
                JOIN players p ON pss.player_id = p.player_id
                WHERE p.player_name = 'Yaxel Lendeborg' AND pss.season_year = '2024-5';
            """)
            ppg, rpg = cur.fetchone()
            self.assertEqual(ppg, 17.5)
            self.assertEqual(rpg, 11.0)
            print("Verified specific season stats for Yaxel Lendeborg.")

        # 3. Proto validation: loaded data conforms to Player / PlayerSeasonStats schema
        print("--- Proto validation ---")
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT player_id, player_name, profile_url, position, rating, status,
                       highschool, height, weight, old_school, new_school
                FROM players WHERE player_name = 'Kadary Richmond';
            """)
            row = cur.fetchone()
            self.assertIsNotNone(row, "Kadary Richmond row not found.")

            player = player_pb2.Player(
                player_id=str(row['player_id']),
                player_name=row['player_name'] or '',
                profile_url=row['profile_url'] or '',
                position=row['position'] or '',
                rating=row['rating'] or '',
                status=row['status'] or '',
                highschool=row['highschool'] or '',
                height=row['height'] or '',
                weight=row['weight'] or '',
                old_school=row['old_school'] or '',
                new_school=row['new_school'] or '',
            )
            self.assertEqual(player.player_name, 'Kadary Richmond')
            self.assertEqual(player.position, 'PG')
            self.assertEqual(player.old_school, 'Seton Hall')
            self.assertEqual(player.new_school, "St. John's")
            player.SerializeToString()  # raises if message is invalid
            print("Verified Player proto for Kadary Richmond.")

            cur.execute("""
                SELECT pss.player_id, pss.season_year, pss.games_played, pss.minutes_played,
                       pss.points_per_game, pss.rebounds_per_game, pss.assists_per_game,
                       pss.blocks_per_game, pss.steals_per_game, pss.field_goal_percentage,
                       pss.three_point_percentage, pss.free_throw_percentage
                FROM player_season_stats pss
                JOIN players p ON pss.player_id = p.player_id
                WHERE p.player_name = 'Yaxel Lendeborg' AND pss.season_year = '2024-5';
            """)
            row = cur.fetchone()
            self.assertIsNotNone(row, "Yaxel Lendeborg 2024-5 stats row not found.")

            stats = player_pb2.PlayerSeasonStats(
                player_id=str(row['player_id']),
                season_year=row['season_year'] or '',
                games_played=int(row['games_played']) if row['games_played'] is not None else 0,
                minutes_played=float(row['minutes_played']) if row['minutes_played'] is not None else 0.0,
                points_per_game=float(row['points_per_game']) if row['points_per_game'] is not None else 0.0,
                rebounds_per_game=float(row['rebounds_per_game']) if row['rebounds_per_game'] is not None else 0.0,
                assists_per_game=float(row['assists_per_game']) if row['assists_per_game'] is not None else 0.0,
                blocks_per_game=float(row['blocks_per_game']) if row['blocks_per_game'] is not None else 0.0,
                steals_per_game=float(row['steals_per_game']) if row['steals_per_game'] is not None else 0.0,
                field_goal_percentage=float(row['field_goal_percentage']) if row['field_goal_percentage'] is not None else 0.0,
                three_point_percentage=float(row['three_point_percentage']) if row['three_point_percentage'] is not None else 0.0,
                free_throw_percentage=float(row['free_throw_percentage']) if row['free_throw_percentage'] is not None else 0.0,
            )
            self.assertEqual(stats.points_per_game, 17.5)
            self.assertEqual(stats.rebounds_per_game, 11.0)
            stats.SerializeToString()  # raises if message is invalid
            print("Verified PlayerSeasonStats proto for Yaxel Lendeborg 2024-5.")

if __name__ == '__main__':
    unittest.main()

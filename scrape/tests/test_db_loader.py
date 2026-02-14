import os
import unittest
import psycopg2
from scrape.utils import load_to_db
from data.models import player_pb2

# --- Database Configuration for Testing ---
DB_NAME = os.getenv("DB_NAME", "cbb_transfers")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

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

if __name__ == '__main__':
    unittest.main()

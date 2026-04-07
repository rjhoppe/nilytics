"""
Scraper tests: unit tests use mocked/fixture data (no network).
Integration test hits 247sports.com; run with RUN_INTEGRATION=1 to execute it.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

# This finds the directory 'app' resides in (repo root) and adds it to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(root_dir))

from bs4 import BeautifulSoup

from app.scrape.utils.scrape_transfers import (
    extract_player_stats,
    load_progress,
    save_progress,
    scrape_transfer_portal,
)

# --- Unit tests: no network, use fixture HTML or temp files ---


class TestExtractPlayerStats(unittest.TestCase):
    """Test stats extraction from profile HTML. Uses inline fixture HTML only."""

    def test_returns_empty_list_when_tables_missing(self):
        soup = BeautifulSoup("<html><body></body></html>", "html.parser")
        result = extract_player_stats(soup)
        self.assertEqual(result, [])

    def test_returns_empty_list_when_only_left_table(self):
        html = """
        <table class="left-table"><tbody><tr><td>2024</td></tr></tbody></table>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = extract_player_stats(soup)
        self.assertEqual(result, [])

    def test_extracts_stats_with_mapped_headers(self):
        html = """
        <table class="left-table">
          <tbody><tr><td>2024-5</td></tr></tbody>
        </table>
        <table class="right-table">
          <thead><tr><th title="Games Played">GP</th><th>Minutes</th><th>Points</th></tr></thead>
          <tbody><tr><td>18</td><td>33.0</td><td>17.5</td></tr></tbody>
        </table>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = extract_player_stats(soup)
        self.assertEqual(len(result), 1)
        row = result[0]
        self.assertEqual(row["Year"], "2024-5")
        self.assertEqual(row["Games Played"], "18")
        self.assertEqual(row["Minutes Played"], "33.0")
        self.assertEqual(row["Points Per Game"], "17.5")

    def test_skips_rows_when_cell_count_mismatch(self):
        html = """
        <table class="left-table">
          <tbody><tr><td>2024</td></tr><tr><td>2023</td></tr></tbody>
        </table>
        <table class="right-table">
          <thead><tr><th>Points</th></tr></thead>
          <tbody>
            <tr><td>10</td></tr>
            <tr><td>8</td><td>extra</td></tr>
          </tbody>
        </table>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = extract_player_stats(soup)
        # Only the first row has matching cell count
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["Points Per Game"], "10")


class TestProgressPersistence(unittest.TestCase):
    """Test load_progress / save_progress with a temp file (no real progress file touched)."""

    def test_load_progress_returns_empty_set_when_file_missing(self):
        with patch("app.scrape.utils.scrape_transfers.PROGRESS_FILE", "/nonexistent/path.json"):
            result = load_progress()
        self.assertEqual(result, set())

    def test_save_and_load_roundtrip(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            path = f.name
        try:
            with patch("app.scrape.utils.scrape_transfers.PROGRESS_FILE", path):
                urls = {"https://example.com/a", "https://example.com/b"}
                save_progress(urls)
                loaded = load_progress()
                self.assertEqual(loaded, urls)
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_load_progress_returns_empty_set_on_invalid_json(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write("not valid json {")
            path = f.name
        try:
            with patch("app.scrape.utils.scrape_transfers.PROGRESS_FILE", path):
                result = load_progress()
                self.assertEqual(result, set())
        finally:
            if os.path.exists(path):
                os.remove(path)


# --- Integration test: hits 247sports.com; run only when requested ---

RUN_INTEGRATION = os.environ.get("RUN_INTEGRATION", "").strip().lower() in (
    "1",
    "true",
    "yes",
)


@unittest.skipUnless(
    RUN_INTEGRATION,
    "Integration test (hits 247sports.com). Set RUN_INTEGRATION=1 to run.",
)
class TestScraperIntegration(unittest.TestCase):
    """Limited live run: 3 records per year, then validate output shape and quality."""

    def setUp(self):
        self.output_filename = f"test_transfer_data_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self.progress_file = "scrape_progress.json"
        if os.path.exists(self.progress_file):
            os.remove(self.progress_file)

    def test_scrape_produces_valid_csv_with_expected_columns(self):
        scrape_transfer_portal(
            max_records_per_year=3,
            output_filename=self.output_filename,
        )
        self.assertTrue(
            os.path.exists(self.output_filename),
            f"Output file {self.output_filename} was not created.",
        )
        df = pd.read_csv(self.output_filename)

        # Columns actually produced by scrape_transfers (no Highschool/Status in current impl)
        expected_static_columns = [
            "Player Name",
            "247Sports Profile URL",
            "Listing Year",
            "Position",
            "Height",
            "Rating",
            "Old School",
            "New School",
            "Weight",
        ]
        for col in expected_static_columns:
            self.assertIn(col, df.columns, f"Missing expected static column: {col}")

        # Dynamic stat columns (mapped names)
        self.assertTrue(
            any("Games Played (" in col for col in df.columns),
            "Missing dynamic 'Games Played' column.",
        )
        self.assertTrue(
            any("Minutes Played (" in col for col in df.columns),
            "Missing dynamic 'Minutes Played' column.",
        )
        self.assertTrue(
            any("Points Per Game (" in col for col in df.columns),
            "Missing dynamic 'Points Per Game' column.",
        )

        # Data quality: not all N/A
        self.assertFalse(
            (df["Height"] == "N/A").all(),
            "Height column contains only N/A values.",
        )
        self.assertFalse(
            (df["Rating"] == "N/A").all(),
            "Rating column contains only N/A values.",
        )
        self.assertGreater(len(df), 0, "No records were captured.")


if __name__ == "__main__":
    unittest.main()

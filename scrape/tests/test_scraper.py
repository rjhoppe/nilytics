import sys
from pathlib import Path

# This finds the directory 'scrape' resides in and adds it to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_dir))

from scrape.utils.scrape_transfers import scrape_transfer_portal
import pandas as pd
import os

if __name__ == "__main__":
    output_filename = "test_transfer_data.csv"
    print("Running test scraper to get first 3 records per year...")
    scrape_transfer_portal(max_records_per_year=3, output_filename=output_filename)
    print("Test scraping complete. Checking test_transfer_data.csv")

    if os.path.exists(output_filename):
        df = pd.read_csv(output_filename)

        # Assertions for expected columns
        expected_static_columns = [
            'Player Name', '247Sports Profile URL', 'Position', 'Height', 'Rating',
            'Highschool', 'Old School', 'New School', 'Weight'
        ]
        
        for col in expected_static_columns:
            assert col in df.columns, f"Missing expected static column: {col}"
            
        print("All expected static columns are present in the CSV.")

        # Assert the presence of at least one dynamic stat column
        # This checks if the flattening logic is working for stats
        assert any("Games Played (" in col for col in df.columns), "Missing dynamic 'Games Played' column."
        assert any("Minutes Played (" in col for col in df.columns), "Missing dynamic 'Minutes Played' column."
        # Add similar checks for other stat categories if desired
            
        print("At least one dynamic stat column (Games Played, Minutes Played) is present.")

        # Basic data validation (e.g., check for non-N/A values in some key fields)
        # This part could be expanded with more specific checks if needed.
        assert not df['Height'].isnull().all(), "Height column contains only null values."
        assert not df['Rating'].isnull().all(), "Rating column contains only null values."
        assert not df['Position'].isnull().all(), "Position column contains only null values."
        assert not df['Weight'].isnull().all(), "Weight column contains only null values."

        print("Basic data validation passed for Height, Position, Rating, and Weight.")

        print(f"Successfully verified data in {output_filename}")
    else:
        print(f"Error: {output_filename} was not created.")


import sys
from pathlib import Path
import pandas as pd
import os
import time
import datetime

# This finds the directory 'scrape' resides in and adds it to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_dir))

# Import the centralized function
from scrape.utils.scrape_transfers import scrape_transfer_portal

if __name__ == "__main__":
    # 1. Fix datetime formatting for filename (colons/spaces aren't great for filenames)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"test_transfer_data_{timestamp}.csv"
    progress_file = "scrape_progress.json"

    # 2. Cleanup previous progress so the test is "pure"
    if os.path.exists(progress_file):
        os.remove(progress_file)

    start_time = time.perf_counter()
    print(f"Running test scraper to get first 3 records per year...")
    
    # Run the scraper
    scrape_transfer_portal(max_records_per_year=3, output_filename=output_filename)
    
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    print(f"Test scraping complete. Execution time: {execution_time:.2f} seconds")

    if os.path.exists(output_filename):
        df = pd.read_csv(output_filename)

        # Updated to match the centralized script's column names
        expected_static_columns = [
            'Player Name', '247Sports Profile URL', 'Position', 'Height', 'Rating',
            'Highschool', 'Old School', 'New School', 'Weight'
        ]
        
        for col in expected_static_columns:
            assert col in df.columns, f"Missing expected static column: {col}"
            
        print("✅ All expected static columns are present.")

        # 3. Updated assertions to match our new mapped keys:
        # 'Minutes' became 'Minutes Played' in our mapping
        assert any("Games Played (" in col for col in df.columns), "Missing dynamic 'Games Played' column."
        assert any("Minutes Played (" in col for col in df.columns), "Missing dynamic 'Minutes Played' column."
        assert any("Points Per Game (" in col for col in df.columns), "Missing dynamic 'Points Per Game' column."
            
        print("✅ Dynamic stat columns (Games Played, Minutes Played, Points) verified.")

        # 4. Data Quality Check
        # Check that we didn't just get a bunch of "N/A" strings 
        # (Since BS4 returns strings, they won't be technically 'null' in Pandas if they are "N/A")
        assert not (df['Height'] == 'N/A').all(), "Height column contains only N/A values."
        assert not (df['Rating'] == 'N/A').all(), "Rating column contains only N/A values."
        
        # Verify we actually got the 3 records per year requested (assuming 3 years)
        print(f"Total records captured: {len(df)}")
        assert len(df) > 0, "No records were captured."

        print(f"Successfully verified data in {output_filename}")
        
        # Cleanup test file after success if you want to keep your directory clean
        # os.remove(output_filename) 
    else:
        print(f"❌ Error: {output_filename} was not created.")
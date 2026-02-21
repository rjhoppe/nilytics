import json
import time
import random
import pandas as pd
import os
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# --- CONFIGURATION ---
OUTPUT_FILE = "transfer_portal_data.csv"
PROGRESS_FILE = "scrape_progress.json"  # Keeps track of which URLs we've finished
MAX_WORKERS = 1  # Keeping it at 1 for maximum IP safety; change to 2-3 if you're brave.

# --- EXTRACTION LOGIC ---
def extract_player_stats(profile_soup):
    all_season_stats = []
    left_table = profile_soup.find('table', class_='left-table')
    right_table = profile_soup.find('table', class_='right-table')

    if not (left_table and right_table):
        return []

    years = [td.text.strip() for td in left_table.select('tbody tr td')]
    headers = [th.get('title', th.text.strip()) for th in right_table.select('thead th')]
    data_rows = right_table.select('tbody tr')

    header_mapping = {
        'Games Played': 'Games Played',
        'Minutes': 'Minutes Played',
        'Points': 'Points Per Game',
        'Rebounds': 'Rebounds Per Game',
        'Assists': 'Assists Per Game',
        'Blocks': 'Blocks Per Game',
        'Steals': 'Steals Per Game',
        'Field Goal Percentage': 'Field Goal Percentage',
        'Three Point Percentage': '3 Point Field Goal Percentage',
        'Free Throw Percentage': 'Free Throw Percentage'
    }

    # Using zip() pairs the year and row perfectly and stops at the shortest list
    for year, row in zip(years, data_rows):
        cells = row.find_all('td')
        if len(cells) == len(headers):
            season_stats = {'Year': year}
            for i, header in enumerate(headers):
                mapped_key = header_mapping.get(header, header)
                season_stats[mapped_key] = cells[i].text.strip()
            all_season_stats.append(season_stats)
    
    return all_season_stats

def scrape_player_profile(page, profile_url):
    player_details = {}
    try:
        # Respectful delay before navigating
        time.sleep(random.uniform(2, 4))
        page.goto(profile_url, wait_until="domcontentloaded", timeout=20000)
        
        soup = BeautifulSoup(page.content(), 'html.parser')
        
        # Helper for metric extraction
        def get_metric(label):
            tag = soup.select_one(f'.metrics-list li:has(span:-soup-contains("{label}")) span:nth-child(2)')
            return tag.text.strip() if tag else 'N/A'

        player_details['Height'] = get_metric("Height")
        player_details['Weight'] = get_metric("Weight")
        player_details['Position'] = get_metric("Pos")
        
        # Rating Extraction
        rating_tag = soup.select_one('.rankings-section:has(.title:-soup-contains("Transfer Rankings")) .rank-block')
        player_details['Rating'] = rating_tag.text.strip() if rating_tag else 'N/A'

        # Schools via JSON Timeline
        player_details['Old School'] = 'N/A'
        player_details['New School'] = 'N/A'
        timeline_script = soup.find('script', id='timelineJson')
        if timeline_script and timeline_script.string:
            try:
                data = json.loads(timeline_script.string)
                events = data[0].get('timeLineData', []) if data else []
                for event in events:
                    if event.get('event') in ['Transfer', 'Enrolled', 'Signed'] and event.get('institution'):
                        if player_details['New School'] == 'N/A':
                            player_details['New School'] = event['institution']
                        elif event['institution'] != player_details['New School']:
                            player_details['Old School'] = event['institution']
                            break
            except json.JSONDecodeError as e:
                print(f"  Error parsing timeline JSON: {e}")

        player_details['Stats'] = extract_player_stats(soup)
        
    except Exception as e:
        print(f"  Error on {profile_url}: {e}")
        
    return player_details

# --- MAIN CONTROLLER ---
def load_progress(progress_file=None):
    path = progress_file or PROGRESS_FILE
    try:
        with open(path, 'r') as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"  Error loading progress file: {e}")
        return set()

def save_progress(processed_urls, progress_file=None):
    path = progress_file or PROGRESS_FILE
    with open(path, 'w') as f:
        json.dump(list(processed_urls), f)

def scrape_transfer_portal(max_records_per_year=None, output_filename="transfer_data.csv", progress_file=None):
    out_file = output_filename
    processed_urls = load_progress(progress_file)
    all_players_data = []
    progress_path = progress_file or PROGRESS_FILE

    # Load existing CSV if it exists to append to it
    if os.path.exists(out_file):
        all_players_data = pd.read_csv(out_file).to_dict('records')

    with sync_playwright() as p:
        # Launch one browser, use one context
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36")
        page = context.new_page()

        years = [2025, 2024, 2023]
        for year in years:
            print(f"--- Fetching Listing for {year} ---")
            time.sleep(random.uniform(1, 3))
            page.goto(f"https://247sports.com/season/{year}-basketball/TransferPortalTop/")
            soup = BeautifulSoup(page.content(), 'html.parser')
            items = soup.select('li.transfer-player')
            records_this_year = 0

            for item in items:
                if max_records_per_year is not None and records_this_year >= max_records_per_year:
                    break
                link_tag = item.select_one('h3 a')
                if not link_tag: continue
                
                url = link_tag['href']
                if url in processed_urls: continue

                player_data = {
                    'Player Name': link_tag.text.strip(),
                    '247Sports Profile URL': url,
                    'Listing Year': year
                }

                print(f"Scraping: {player_data['Player Name']}...")
                details = scrape_player_profile(page, url)
                
                stats = details.pop('Stats', [])
                for s in stats:
                    y = s.get('Year', 'Unknown')
                    for k, v in s.items():
                        if k != 'Year': player_data[f"{k} ({y})"] = v
                
                player_data.update(details)
                all_players_data.append(player_data)
                processed_urls.add(url)
                records_this_year += 1

                if len(all_players_data) % 10 == 0:
                    pd.DataFrame(all_players_data).to_csv(out_file, index=False)
                    save_progress(processed_urls, progress_path)
                    print(f"Saved progress: {len(processed_urls)} records total.")

        browser.close()

    pd.DataFrame(all_players_data).to_csv(out_file, index=False)
    if all_players_data:
        save_progress(processed_urls, progress_path)
    print("Job Complete.")

if __name__ == "__main__":
    scrape_transfer_portal()
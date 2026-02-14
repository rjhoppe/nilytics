import time
import random
import pandas as pd
import json
import re # Import regex module
from datetime import datetime # Import datetime module
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup


def extract_player_stats(profile_soup):
    """
    Extracts player statistics for every previous season from the profile page.
    """
    all_season_stats = []
    
    # Find both left-table (for years) and right-table (for stats)
    left_table = profile_soup.find('table', class_='left-table')
    right_table = profile_soup.find('table', class_='right-table')

    if left_table and right_table:
        print(f"  Found both left-table and right-table.")
        
        # Extract years from the left table
        years = [td.text.strip() for td in left_table.select('tbody tr td')]
        
        # Extract headers from the right table
        headers = []
        for th in right_table.find('thead').find_all('th'):
            header_text = th.get('title', th.text.strip())
            headers.append(header_text)
        print(f"  Extracted stat headers: {headers}")

        # Define a mapping from table headers to desired output keys
        # This ensures consistent naming across the final CSV
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
            'Free Throw Percentage': 'Free Throw Percentage',
            'Year': 'Year' # Add Year to mapping for consistency, though it's handled separately
        }
        
        # Extract data rows from the right table
        data_rows = right_table.find('tbody').find_all('tr')
        print(f"  Found {len(data_rows)} data rows in right table.")

        # Combine years with data rows
        for i, row in enumerate(data_rows):
            print(f"  Processing row {i}...")
            if i < len(years): # Ensure there's a corresponding year
                season_stats = {'Year': years[i]}
                cells = row.find_all('td')
                print(f"    Cells in row: {len(cells)}, Headers: {len(headers)}")
                if len(cells) == len(headers):
                    for j in range(len(headers)):
                        original_key = headers[j]
                        mapped_key = header_mapping.get(original_key, original_key) # Use mapped key
                        season_stats[mapped_key] = cells[j].text.strip()
                    all_season_stats.append(season_stats)
                    print(f"    Appended season_stats: {season_stats}")
                else:
                    print(f"    Skipping row due to mismatch: len(cells)={len(cells)}, len(headers)={len(headers)}")
            else:
                print(f"  Warning: Mismatch between number of years ({len(years)}) and data rows ({len(data_rows)}).")
    else:
        print("  Could not find both left-table and right-table.")
    
    return all_season_stats


def scrape_player_profile(page, profile_url):
    """
    Navigates to a player's profile page and extracts detailed information.
    
    Args:
        page (playwright.sync_api.Page): The Playwright page object.
        profile_url (str): The URL of the player's profile page.
        
    Returns:
        dict: A dictionary containing detailed player information.
    """
    player_details = {}
    
    try:
        page.goto(profile_url, wait_until="networkidle")
        profile_soup = BeautifulSoup(page.content(), 'html.parser')
        
        # Extract Height
        # Found with CSS selector: .metrics-list li:has(span:contains("Height")) span:nth-child(2)
        height_tag = profile_soup.select_one('.metrics-list li:has(span:contains("Height")) span:nth-child(2)')
        if height_tag:
            player_details['Height'] = height_tag.text.strip()
        else:
            # Fallback to regex if specific selector fails
            height_match = re.search(r'(\d-\d+)', profile_soup.text) # Look for pattern like 6-5
            if height_match:
                player_details['Height'] = height_match.group(1)
            else:
                player_details['Height'] = 'N/A' # Default to N/A if not found

        # Extract Weight
        # Found with CSS selector: .metrics-list li:has(span:contains("Weight")) span:nth-child(2)
        weight_tag = profile_soup.select_one('.metrics-list li:has(span:contains("Weight")) span:nth-child(2)')
        if weight_tag:
            player_details['Weight'] = weight_tag.text.strip()
        else:
            # Fallback to regex if specific selector fails
            weight_match = re.search(r'(\d+)\s*(?:lbs|lb)', profile_soup.text, re.IGNORECASE) # Look for pattern like 175 lbs
            if weight_match:
                player_details['Weight'] = weight_match.group(1)
            else:
                player_details['Weight'] = 'N/A' # Default to N/A if not found
        
        # Extract Position
        # Found with CSS selector: .metrics-list li:has(span:contains("Pos")) span:nth-child(2)
        position_tag = profile_soup.select_one('.metrics-list li:has(span:contains("Pos")) span:nth-child(2)')
        if position_tag:
            player_details['Position'] = position_tag.text.strip()
        else:
            # Alternative: sometimes position is in a span near the name, or other generic classes
            position_span = profile_soup.find('span', class_='position')
            if position_span:
                player_details['Position'] = position_span.text.strip()
            else:
                player_details['Position'] = 'N/A'

        # Extract Rating (Composite Rating)
        # Found with CSS selector: .rankings-section:has(.title:contains("247Sports Transfer Rankings")) .rank-block
        rating_tag = profile_soup.select_one('.rankings-section:has(.title:contains("247Sports Transfer Rankings")) .rank-block')
        if rating_tag:
            player_details['Rating'] = rating_tag.text.strip()
        else:
            player_details['Rating'] = 'N/A'
            
        # Extract Highschool
        # Removing Highschool extraction from profile page as it's not reliably found here.
        # Relying on extraction from listing page in scrape_transfer_portal if available.
        # player_details['Highschool'] = 'N/A' # Will be set by scrape_transfer_portal

        # Extract Old School (transferring from) and New School (transferring to)
        old_school = 'N/A'
        new_school = 'N/A'
        
        timeline_script = profile_soup.find('script', id='timelineJson')
        if timeline_script and timeline_script.string:
            try:
                timeline_data = json.loads(timeline_script.string)
                if isinstance(timeline_data, list) and timeline_data:
                    # timelineData is already reversed (latest first)
                    events = timeline_data[0].get('timeLineData', [])
                    
                    if events:
                        # Find the New School (latest transfer/enrollment)
                        for event in events:
                            if event.get('event') in ['Transfer', 'Enrolled', 'Signed'] and event.get('institution'):
                                new_school = event['institution']
                                break
                        
                        # Find the Old School (previous distinct institution)
                        found_new_school_event = False
                        for event in events:
                            if event.get('event') in ['Transfer', 'Enrolled', 'Signed'] and event.get('institution'):
                                if event['institution'] == new_school:
                                    found_new_school_event = True
                                elif found_new_school_event and event['institution'] != new_school:
                                    old_school = event['institution']
                                    break
            except json.JSONDecodeError as e:
                print(f"  Error decoding timelineJson: {e}")
        
        player_details['Old School'] = old_school
        player_details['New School'] = new_school
        
        # Placeholder for stats extraction
        player_details['Stats'] = extract_player_stats(profile_soup)
        
    except Exception as e:
        print(f"Error scraping player profile {profile_url}: {e}")
        
    return player_details


def scrape_transfer_portal(max_records_per_year=None, output_filename="transfer_data.csv"):
    all_players_data = []
    
    # Define years to scrape dynamically based on the current year
    current_year = datetime.now().year
    years_to_scrape = [current_year - 1, current_year - 2, current_year - 3, current_year - 4] # Last three seasons

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        for year in years_to_scrape:
            print(f"Scraping transfer portal for {year} season...")
            url = f"https://247sports.com/season/{year}-basketball/TransferPortalTop/"
            
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    
                soup = BeautifulSoup(page.content(), 'html.parser')

                # Find all player list items using the identified selector
                player_list_items = soup.select('li.transfer-player')
                
                print(f"  Found {len(player_list_items)} player list items.")
                
                records_count = 0
                for player_item in player_list_items:
                    if max_records_per_year and records_count >= max_records_per_year:
                        break

                    player_data = {}
                    
                    # Extract Player Name and Profile URL
                    name_link_tag = player_item.select_one('h3 a')
                    if name_link_tag:
                        player_data['Player Name'] = name_link_tag.text.strip()
                        player_data['247Sports Profile URL'] = name_link_tag['href']
                    else:
                        print("  Player name or link not found, skipping item.")
                        continue 
                    
                    # Extract Position
                    position_tag = player_item.select_one('.position')
                    if position_tag:
                        player_data['Position'] = position_tag.text.strip()
                    else:
                        player_data['Position'] = 'N/A'

                    # Extract Rating
                    rating_tag = player_item.select_one('.rating')
                    if rating_tag:
                        player_data['Rating'] = rating_tag.text.strip()
                    else:
                        player_data['Rating'] = 'N/A'

                    # Extract Status (e.g., Enrolled, Entered Portal)
                    status_tag = player_item.select_one('.status')
                    if status_tag:
                        player_data['Status'] = status_tag.text.strip()
                    else:
                        player_data['Status'] = 'N/A'
                    
                    # Extract Highschool (from bio, if available)
                    bio_tag = player_item.select_one('.bio')
                    if bio_tag and 'HS:' in bio_tag.text:
                        player_data['Highschool'] = bio_tag.text.split('HS:')[1].strip()
                    else:
                        player_data['Highschool'] = 'N/A'

                    print(f"  Scraping details for {player_data['Player Name']} (Position: {player_data['Position']})...")
                    # Scrape detailed player profile
                    detailed_player_info = scrape_player_profile(page, player_data['247Sports Profile URL'])
                    
                    # Flatten the 'Stats' from detailed_player_info into individual columns
                    season_stats_list = detailed_player_info.pop('Stats', [])
                    for season_stats in season_stats_list:
                        year = season_stats.get('Year', 'N/A')
                        for stat_name, stat_value in season_stats.items():
                            if stat_name != 'Year':
                                player_data[f"{stat_name} ({year})"] = stat_value
                    
                    player_data.update(detailed_player_info)
                        
                    print(f"  Final player_data before append: {player_data}")
                    all_players_data.append(player_data)
                    records_count += 1
                    time.sleep(random.uniform(1, 3)) # Be polite

            except Exception as e:
                print(f"Error scraping {year} transfer portal: {e}")
            
            time.sleep(random.uniform(2, 5)) # Delay between years

        browser.close()

    df = pd.DataFrame(all_players_data)
    df.to_csv(output_filename, index=False)
    print(f"Scraping complete. Data saved to {output_filename}")


from scrape.utils import load_to_db, scrape_transfers

if __name__ == '__main__':
  # Potentially do a small test run here first?
  scrape_transfers.scrape_transfer_portal()
  load_to_db.load_data_from_csv()

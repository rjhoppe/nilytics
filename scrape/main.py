from scrape.utils import load_to_db, scrape_transfers

if __name__ == '__main__':
  scrape_transfers.scrape_transfer_portal()
  load_to_db.load_data_from_csv(scrape_transfers.OUTPUT_FILE)

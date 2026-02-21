# --- Application ---
run:
	docker compose up -d postgres

kill:
	docker compose down

# --- Scrape ---
scrape-dev:
	docker build -f scrape/Dockerfile -t scrape-dev .
	docker run --env-file .env scrape-dev

dryrun:
	docker run --env-file .env scrape-dev python -m scrape.utils.dryrun

# Add all csv files to scrape directory before running this command
load_to_db:
	.venv/bin/python -c "import glob; from scrape.utils import load_to_db; \
		[load_to_db.load_data_from_csv(f) for f in sorted(glob.glob('scrape/*.csv'))]"

# --- API ---

# --- UI ---
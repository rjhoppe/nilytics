# --- Application ---
run:
	docker compose up -d postgres

kill:
	docker compose down

# --- Scrape ---
# Output dir for CSV/progress (mount as container CWD so files appear on host)
SCRAPE_OUTPUT := app/scrape/output

scrape-dev:
	docker build -f app/scrape/Dockerfile -t scrape-dev .
	mkdir -p $(SCRAPE_OUTPUT)
	docker run --env-file .env -v "$$(pwd)/$(SCRAPE_OUTPUT):/workspace" scrape-dev \
		bash -c "cd /workspace && python -m app.scrape.utils.dryrun && python -m app.scrape.main"

dryrun:
	docker run --env-file .env -v "$$(pwd)/$(SCRAPE_OUTPUT):/workspace" scrape-dev \
		bash -c "cd /workspace && python -m app.scrape.utils.dryrun"

# Add all csv files to app/scrape directory before running this command
load_to_db:
	.venv/bin/python -c "import glob; from app.scrape.utils import load_to_db; \
		[load_to_db.load_data_from_csv(f) for f in sorted(glob.glob('app/scrape/*.csv'))]"

# --- API ---

# --- UI ---
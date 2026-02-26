# Nilytics

## Prerequisites

- Docker (for scrape service and Postgres)
- Python 3.11+ with `.venv` (for local `load_to_db` and tests)
- `.env` with `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`

## Scrape service

The scraper (247sports transfer portal) and DB loader live under `app/scrape/`. It runs in Docker so Playwright has a browser; output files are written to your machine via a volume mount.

### How it works

1. **Build and run** (from repo root):

   ```bash
   make scrape-dev
   ```

   - Builds the image from `app/scrape/Dockerfile`.
   - Mounts `app/scrape/output` on your host to `/workspace` in the container.
   - Runs dryrun (small fetch to check DOM), then the full scrape and load.
   - The scraper writes to the current working directory inside the container, which is `/workspace`, so files appear in **`app/scrape/output/`** on your machine.

2. **Output files** (on your machine):

   - `app/scrape/output/transfer_portal_data.csv` — scraped player/transfer data
   - `app/scrape/output/scrape_progress.json` — progress so you can resume

   No need to copy from the container; the volume makes that directory the same inside and outside the container.

3. **Dry run only** (check that the site layout hasn’t changed, no full scrape):

   ```bash
   make dryrun
   ```

   Uses the same output dir; dry run uses its own filenames so it doesn’t overwrite production data.

### Loading CSV into the database

With Postgres up (`make run`), load CSVs from `app/scrape/` (including `app/scrape/output/`) into the DB:

```bash
make load_to_db
```

This globs `app/scrape/*.csv`. To load only the main output file:

```bash
.venv/bin/python -c "from app.scrape.utils import load_to_db; load_to_db.load_data_from_csv('app/scrape/output/transfer_portal_data.csv')"
```

### Running tests

From repo root (so `app` is importable):

```bash
.venv/bin/python -m unittest app.scrape.tests.test_scraper -v
.venv/bin/python -m unittest app.scrape.tests.test_db_loader.TestCsvValidation -v
```

DB-backed tests in `test_db_loader` require Postgres and env vars; the CSV-validation tests above do not.

## Other

- **Postgres:** `make run` / `make kill`
- API and UI sections are placeholders for future components.

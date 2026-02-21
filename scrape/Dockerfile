# Scrape service: transfer portal scraper + load to DB.
# Uses Playwright for browser automation; base image includes browsers.
#
# Build from repo root:  docker build -f scrape/Dockerfile .
# Run example:
#   docker run --env-file .env \
#     -e DB_HOST=host.docker.internal \
#     your-image
#
# Required env: DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

ARG PLAYWRIGHT_VERSION=1.58.0
FROM mcr.microsoft.com/playwright/python:v${PLAYWRIGHT_VERSION}-noble

WORKDIR /app

# Install Python dependencies (playwright version matches base image)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application and shared data (protos etc.)
COPY scrape ./scrape
COPY data ./data

# Scraper writes transfer_portal_data.csv and scrape_progress.json in CWD
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["./entrypoint.sh"]

#!/bin/bash

# Run the dry run
python -m app.scrape.utils.dryrun

# If dry run is successful, run the main script
if [ $? -eq 0 ]; then
    python -m app.scrape.main
fi

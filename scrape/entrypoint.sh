#!/bin/bash

# Run the dry run
python -m scrape.utils.dryrun

# If dry run is successful, run the main script
if [ $? -eq 0 ]; then
    python -m scrape.main
fi
#!/bin/bash

# Create virtual environment if it doesn't exist and install dependencies
# NOTE: This script assumes Python 3.12 is installed and available as 'python3.12'.
# If you have a different version, adjust the command accordingly.
if [ ! -d "venv" ]; then
    python3.12 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

# Activate virtual environment if not already active
if [ -z "$VIRTUAL_ENV" ]; then
    source venv/bin/activate
fi

# NOTE: If you change requirements.txt, run 'pip install -r requirements.txt' manually.

# Run the server as a module so package-relative imports work
python -m src.server

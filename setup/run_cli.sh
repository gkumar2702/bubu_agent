#!/bin/bash

# Bubu Agent CLI Runner
# This script runs the CLI tool from the setup directory

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Go to the parent directory (project root)
cd "$SCRIPT_DIR/.."

# Run the CLI with all arguments passed to this script
python bubu_cli.py "$@"

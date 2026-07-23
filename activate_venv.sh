#!/bin/bash
# Activates the virtual environment for this project

VENV_DIR="./venv"

if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
    echo "Virtual environment activated. Use 'deactivate' to exit."
else
    echo "Virtual environment not found. Run 'make venv' first."
fi


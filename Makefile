# Makefile for creating a virtual environment for Python scripts

VENV_DIR := venv
PYTHON := python3
REQS := requirements.txt

.PHONY: venv

venv:
	@if [ ! -d $(VENV_DIR) ]; then \
		$(PYTHON) -m venv $(VENV_DIR); \
		echo "Virtual environment created in $(VENV_DIR)"; \
	else \
		echo "Virtual environment already exists in $(VENV_DIR)"; \
	fi
	@echo "Installing requirements..."
	@$(VENV_DIR)/bin/pip install --upgrade pip
	@$(VENV_DIR)/bin/pip install -r $(REQS)
	@echo "Virtual environment setup complete."
	@echo "Run 'source activate_venv.sh' to activate the venv."


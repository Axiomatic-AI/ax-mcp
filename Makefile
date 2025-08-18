.PHONY: install dev test format clean

install:
	@command -v uv >/dev/null 2>&1 || (echo "Installing uv..." && curl -LsSf https://astral.sh/uv/install.sh | sh)
	@echo "Installing ax-mcp..."
	@uv pip install -e .
	@echo "✅ Installation complete! Run 'axiomatic-pic' to start the server."

install-dev:
	@command -v uv >/dev/null 2>&1 || (echo "Installing uv..." && curl -LsSf https://astral.sh/uv/install.sh | sh)
	@echo "Setting up development environment..."
	@uv venv
	@uv pip install -e ".[dev]"
	@echo "✅ Dev environment ready!"

test:
	@uv run pytest tests/ -v --tb=short || true

format:
	@uv run ruff check --fix .
	@uv run black .

clean:
	@rm -rf build/ dist/ *.egg-info .pytest_cache .ruff_cache .mypy_cache
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleaned build artifacts"
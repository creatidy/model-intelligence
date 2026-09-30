.PHONY: check

check:
	uv sync --locked --group dev
	uv run --no-sync ruff check .
	uv run --no-sync ruff format --check .
	uv run --no-sync basedpyright
	uv run --no-sync python -m unittest discover -s tests -v
	git diff --check
	git diff --cached --check

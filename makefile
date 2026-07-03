.PHONY: run
run:
	uvicorn app.main:application --reload

.PHONY: makemigrations
makemigrations:
	@if [ -z "$(name)" ]; then \
		tortoise makemigrations; \
	else \
		tortoise makemigrations --name $(name); \
	fi

.PHONY: migrate-up
migrate-up:
	@tortoise upgrade

.PHONY: test-pytest
test-pytest:
	@uv run pytest tests/ -v

.PHONY: install
install:
	@uv sync

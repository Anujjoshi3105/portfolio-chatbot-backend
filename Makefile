.PHONY: install lint test typecheck mdlint docker-build docker-run clean

install:
	uv sync

lint:
	uv run ruff format --check
	uv run ruff check --output-format github

typecheck:
	uv run mypy

test:
	uv run pytest --cov=src/ --cov-report=xml

mdlint:
	uv run pymarkdown scan README.md docs/

docker-build:
	docker build -t chatbot.service .

docker-run:
	docker run -d --name service-container --network host \
		-e USE_FAKE_MODEL=true -e PORT=7860 chatbot.service

clean:
	rm -rf coverage.xml .coverage

all: install lint typecheck test mdlint

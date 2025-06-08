.PHONY: install setup lint test coverage run build_docker run_docker stop_docker clean init deploy destroy

install:
	@echo "Installing dependencies with Poetry..."
	@poetry install

setup: install
	@echo "Copying .env.example to .env if not exists..."
	@cp -n .env.example .env || true
	@echo "Project setup complete. Remember to edit .env with your specific configurations."

lint:
	@echo "Running Ruff linter..."
	@poetry run ruff check . --fix

format:
	@echo "Running Ruff formatter..."
	@poetry run ruff format .

test:
	@echo "Running tests with pytest..."
	@poetry run pytest tests/

coverage:
	@echo "Running tests with coverage report..."
	@poetry run pytest --cov=app --cov-report=term-missing --cov-fail-under=90 tests/

run:
	@echo "Starting FastAPI application with Uvicorn..."
	@poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

build_docker:
	@echo "Building Docker image..."
	@docker build -t foundlab-backend:latest .

run_docker:
	@echo "Running Docker containers with docker-compose..."
	@docker-compose up --build

stop_docker:
	@echo "Stopping Docker containers..."
	@docker-compose down

init:
	@echo "Running init.sh script to seed initial data..."
	@poetry run python init.sh

deploy:
	@echo "Running deploy.sh script to build and deploy to Cloud Run."
	@poetry run python deploy.sh && poetry run python init.sh # Deploy then init

destroy:
	@echo "Running destroy.sh script to delete Cloud Run service."
	@poetry run python destroy.sh

clean:
	@echo "Cleaning up build artifacts and caches..."
	@find . -name "__pycache__" -type d -exec rm -rf {} +
	@find . -name "*.pyc" -exec rm -f {} +
	@rm -rf .pytest_cache .coverage .ruff_cache
	@echo "Clean complete."

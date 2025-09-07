.PHONY: help install install-dev test lint format type-check clean run

help:  ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Installe les dépendances de production
	pip install -r requirements.txt

install-dev:  ## Installe toutes les dépendances (dev inclus)
	pip install -r requirements-dev.txt
	pre-commit install

test:  ## Lance les tests unitaires
	python -m pytest tests/ -v --cov=venantvr --cov-report=term-missing

lint:  ## Vérifie le style du code avec ruff
	ruff check venantvr tests

format:  ## Formate le code avec black et ruff
	black venantvr tests
	ruff check --fix venantvr tests

type-check:  ## Vérifie les types avec mypy
	mypy venantvr

clean:  ## Nettoie les fichiers temporaires
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true

run:  ## Lance le bot
	python tests/main.py

check-all: lint type-check test  ## Lance toutes les vérifications

pre-commit:  ## Lance pre-commit sur tous les fichiers
	pre-commit run --all-files
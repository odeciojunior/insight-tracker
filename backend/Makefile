.PHONY: help install clean lint test format run-dev all

help:
	@echo "Makefile para desenvolvimento do Insight Tracker API"
	@echo ""
	@echo "Uso:"
	@echo "    make install    - Instala dependências"
	@echo "    make clean      - Remove arquivos temporários"
	@echo "    make lint       - Executa verificadores de código"
	@echo "    make test       - Executa testes"
	@echo "    make format     - Formata o código conforme padrões"
	@echo "    make run-dev    - Inicia o servidor de desenvolvimento"
	@echo "    make all        - Executa lint, test e format"

install:
	pip install -r requirements.txt

clean:
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name "*.py[cod]" -exec rm -rf {} +
	find . -type d -name "*$py.class" -exec rm -rf {} +

lint:
	flake8 app tests
	mypy app tests
	ruff check app tests

test:
	pytest -v

format:
	isort app tests
	black app tests

run-dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

all: lint test format

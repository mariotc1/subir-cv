# Makefile para CV Upload System
.PHONY: help install run test docker-build docker-run docker-stop docker-logs clean

# Variables
PYTHON := python3
PIP := pip3
DOCKER_COMPOSE := docker compose

# Colores para output
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

help: ## Muestra esta ayuda
	@echo "$(GREEN)CV Upload System - Comandos disponibles:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'

install: ## Instala dependencias localmente
	@echo "$(GREEN)Instalando dependencias...$(NC)"
	cd backend && $(PIP) install -r requirements.txt
	@echo "$(GREEN)Dependencias instaladas correctamente$(NC)"

run: ## Ejecuta la aplicación localmente (requiere PostgreSQL)
	@echo "$(GREEN)Iniciando aplicación...$(NC)"
	cd backend && $(PYTHON) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test: ## Ejecuta los tests
	@echo "$(GREEN)Ejecutando tests...$(NC)"
	cd backend && $(PYTHON) -m pytest ../tests -v --tb=short
	@echo "$(GREEN)Tests completados$(NC)"

test-coverage: ## Ejecuta tests con cobertura
	@echo "$(GREEN)Ejecutando tests con cobertura...$(NC)"
	cd backend && $(PYTHON) -m pytest ../tests -v --cov=app --cov-report=html
	@echo "$(GREEN)Reporte de cobertura generado en htmlcov/$(NC)"

docker-build: ## Construye la imagen Docker
	@echo "$(GREEN)Construyendo imagen Docker...$(NC)"
	$(DOCKER_COMPOSE) build
	@echo "$(GREEN)Imagen construida correctamente$(NC)"

docker-run: ## Inicia los contenedores Docker
	@echo "$(GREEN)Iniciando contenedores...$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)Aplicación disponible en http://localhost:8000$(NC)"

docker-stop: ## Detiene los contenedores Docker
	@echo "$(GREEN)Deteniendo contenedores...$(NC)"
	$(DOCKER_COMPOSE) down
	@echo "$(GREEN)Contenedores detenidos$(NC)"

docker-logs: ## Muestra los logs de los contenedores
	$(DOCKER_COMPOSE) logs -f

docker-clean: ## Elimina contenedores, volúmenes e imágenes
	@echo "$(YELLOW)Eliminando contenedores, volúmenes e imágenes...$(NC)"
	$(DOCKER_COMPOSE) down -v --rmi all
	@echo "$(GREEN)Limpieza completada$(NC)"

clean: ## Limpia archivos temporales
	@echo "$(GREEN)Limpiando archivos temporales...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	rm -rf htmlcov .coverage 2>/dev/null || true
	@echo "$(GREEN)Limpieza completada$(NC)"

lint: ## Ejecuta linters (requiere ruff)
	@echo "$(GREEN)Ejecutando linters...$(NC)"
	cd backend && $(PYTHON) -m ruff check app/
	@echo "$(GREEN)Linting completado$(NC)"

security-check: ## Ejecuta análisis de seguridad (requiere bandit)
	@echo "$(GREEN)Ejecutando análisis de seguridad...$(NC)"
	cd backend && $(PYTHON) -m bandit -r app/ -ll
	@echo "$(GREEN)Análisis completado$(NC)"

setup-env: ## Crea archivo .env desde el ejemplo
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(GREEN)Archivo .env creado. Edita los valores antes de usar.$(NC)"; \
	else \
		echo "$(YELLOW)El archivo .env ya existe$(NC)"; \
	fi

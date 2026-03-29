.PHONY: frontend setup infra seed-images services local cleanup publish consume wp-uploader pin-maker style-editor account-analytics title-generator bg-remover logs tests az-setup-entra az-deploy az-init-db az-build-push az-seed az-status az-logs az-destroy help

# Default target
.DEFAULT_GOAL := help

# ==========================================
# Development Setup
# ==========================================

setup:  ## Create venv and install dependencies
	@command -v pyenv >/dev/null || (echo "pyenv not found. Install with: brew install pyenv" && exit 1)
	pyenv install 3.12.12
	python -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -e common/
	@for req in services/*/requirements.txt; do .venv/bin/pip install -r $$req; done
	@for req in dev-tools/*/requirements.txt; do .venv/bin/pip install -r $$req; done
	.venv/bin/pip install -r test/requirements.txt
	@echo "Done! Activate with: source .venv/bin/activate"

# ==========================================
# Docker Compose (Original)
# ==========================================
frontend:
	docker compose \
	--env-file ./config/local/variables.env \
	-f docker-compose.yaml \
	-f config/local/docker-compose.override.yaml \
	up --build -d --no-deps frontend
infra:
	docker compose \
	  --env-file ./config/local/variables.env \
	  -f docker-compose.yaml \
	  -f config/local/docker-compose.override.yaml \
	  up --build -d --no-deps db && \
	docker compose \
	  --env-file ./config/local/variables.env \
	  -f docker-compose.yaml \
	  -f config/local/docker-compose.override.yaml \
	  up --build -d --no-deps redis && \
	docker compose \
	  --env-file ./config/local/variables.env \
	  -f docker-compose.yaml \
	  -f config/local/docker-compose.override.yaml \
	  up --build -d --no-deps azurite

seed-images:  ## Run seed-worker (DB seeding + seed image upload)
	docker compose \
	  --env-file ./config/local/variables.env \
	  -f docker-compose.yaml \
	  -f config/local/docker-compose.override.yaml \
	  up --build --no-deps seed-worker

services:
	docker compose \
	  --env-file ./config/local/variables.env \
	  -f docker-compose.yaml \
	  -f config/local/docker-compose.override.yaml \
	  up --build -d --no-deps \
	  management-api scheduler channel-worker \
	  analytics-collector activity-reporter promotion-orchestrator

local: infra services frontend seed-images

cleanup:
	docker compose \
	  --env-file ./config/local/variables.env \
	  -f docker-compose.yaml \
	  -f config/local/docker-compose.override.yaml \
	  down -v

publish:
	. dev-tools/dev-shell.sh && python dev-tools/local_topic_publish.py

consume:
	. dev-tools/dev-shell.sh && python dev-tools/local_topic_consume.py

wp-uploader:
	. dev-tools/dev-shell.sh && cd dev-tools && python wp-uploader/wp_uploader.py

pin-maker:
	. dev-tools/dev-shell.sh && cd dev-tools && python pin-maker/pin_maker.py pin-maker/data/input.json

style-editor:
	. dev-tools/dev-shell.sh && cd dev-tools/style-editor && streamlit run style_editor.py

account-analytics:
	. dev-tools/dev-shell.sh && cd dev-tools && python account-analytics/account_analytics.py --open

title-generator:
	. dev-tools/dev-shell.sh && cd dev-tools && python title-generator/title_generator.py

bg-remover:
	. dev-tools/dev-shell.sh && cd dev-tools && python bg-remover/bg_remover.py bg-remover/data/input.json

logs:
	docker compose logs -f

# ===========================================
# Testing
# ===========================================

tests:  ## Run tests in Docker container
	docker compose --env-file ./config/local/variables.env --profile test run --rm --build test-runner

# ==========================================
# Azure Container Apps
# ==========================================

az-setup-entra:  ## Create Azure Entra app registration (run once)
	@bash infra/azure/scripts/setup-entra.sh \
		$$(az deployment sub show --name cae-deployment --query properties.outputs.keyVaultName.value -o tsv 2>/dev/null || echo "KEYVAULT_NAME") \
		$$(az deployment sub show --name management-api-deployment --query properties.outputs.managementApiUrl.value -o tsv 2>/dev/null || echo "API_URL")

az-deploy:  ## Deploy/update all Azure infrastructure
	@bash infra/azure/scripts/deploy.sh --postgres-password "$${POSTGRES_ADMIN_PASSWORD:?Set POSTGRES_ADMIN_PASSWORD env var}"

az-init-db:  ## Run database init scripts against Azure PostgreSQL
	@bash infra/azure/scripts/init-database.sh \
		$$(az deployment sub show --name postgres-deployment --query properties.outputs.postgresFqdn.value -o tsv) \
		pgadmin \
		"$${POSTGRES_ADMIN_PASSWORD:?Set POSTGRES_ADMIN_PASSWORD env var}" \
		contentengine_dev

az-build-push:  ## Build all Docker images and push to ACR
	@ACR=$$(az deployment sub show --name acr-deployment --query properties.outputs.acrLoginServer.value -o tsv) && \
	az acr login --name $${ACR%%.*} && \
	for svc in management-api template-service promotion-orchestrator scheduler channel-worker activity-reporter analytics-collector seed-worker; do \
		echo "Building $${svc}..." && \
		docker build -t "$${ACR}/$${svc}:latest" -f services/$${svc}/Dockerfile services/$${svc} && \
		docker push "$${ACR}/$${svc}:latest"; \
	done

az-seed:  ## Trigger seed-worker job
	az containerapp job start \
		--name content-engine-dev-seed-worker \
		--resource-group rg-content-engine-dev

az-status:  ## Show Container App status
	az containerapp list --resource-group rg-content-engine-dev --output table

az-logs:  ## Tail logs from Container Apps
	@echo "Use: az containerapp logs show --name <app-name> --resource-group rg-content-engine-dev --follow"

az-destroy:  ## Delete resource group (removes everything)
	az group delete --name rg-content-engine-dev --yes --no-wait
	@echo "Resource group deletion initiated (runs in background)"

# ==========================================
# Help
# ==========================================

help:  ## Show this help message
	@echo "Content Automation Engine - Makefile Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make setup           - Install Python and create venv"
	@echo ""
	@echo "Docker Compose:"
	@echo "  make infra          - Start db, redis, azurite"
	@echo "  make seed-images    - Run seed-worker (DB + blob images)"
	@echo "  make services       - Start application services"
	@echo "  make local          - Run infra → services → frontend → seed-images"
	@echo "  make cleanup        - Stop and remove all containers"
	@echo "  make logs           - Tail docker-compose logs"
	@echo "  make wp-uploader      - Generate and upload content to WordPress"
	@echo "  make pin-maker       - Create Pinterest pins (edit data/input.json)"
	@echo "  make style-editor   - Visual style editor (add ?channel=name in URL, default: pinterest)"
	@echo "  make account-analytics - Generate account-wide analytics report"
	@echo "  make title-generator  - Generate titles (edit data/input.json)"
	@echo "  make bg-remover       - Remove backgrounds and place on colored canvas"
	@echo ""
	@echo "Testing:"
	@echo "  make tests          - Run all tests in Docker"
	@echo ""
	@echo "Azure Container Apps:"
	@echo "  make az-setup-entra - Create Entra app registration (run once)"
	@echo "  make az-deploy      - Deploy/update all Azure infrastructure"
	@echo "  make az-init-db     - Run DB init scripts against Azure PostgreSQL"
	@echo "  make az-build-push  - Build all Docker images and push to ACR"
	@echo "  make az-seed        - Trigger seed-worker job"
	@echo "  make az-status      - Show Container App status"
	@echo "  make az-logs        - Tail logs from Container Apps"
	@echo "  make az-destroy     - Delete resource group (removes everything)"

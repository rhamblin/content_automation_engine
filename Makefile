.PHONY: frontend setup infra seed-images services local cleanup publish consume wp-upload wp-media-ids logs tests k8s-deploy k8s-status k8s-logs k8s-clean help

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

seed-images:
	docker run --rm \
	-v $(PWD)/config/local/seed-images:/seed \
	--network content_automation_engine_backend \
	-e AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://azurite:10000/devstoreaccount1;" \
	mcr.microsoft.com/azure-cli \
	sh -c "az storage container create -n images && az storage blob upload-batch -s /seed -d images"

services:
	docker compose \
	  --env-file ./config/local/variables.env \
	  -f docker-compose.yaml \
	  -f config/local/docker-compose.override.yaml \
	  up --build -d --no-deps \
	  management-api scheduler content-producer visual-composer \
	  publication-worker analytics-collector activity-reporter promotion-orchestrator

local: infra seed-images services frontend

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

wp-upload:
	. dev-tools/dev-shell.sh && cd dev-tools && python wp-uploader/wp_uploader.py

wp-media-ids:
	. dev-tools/dev-shell.sh && cd dev-tools && python wp-uploader/get_media_ids.py $(MEDIA_FOLDER)

logs:
	docker compose logs -f

# ==========================================
# Testing
# ==========================================

tests:  ## Run tests in Docker container
	docker compose --env-file ./config/local/variables.env --profile test run --rm --build test-runner

# ==========================================
# Kubernetes
# ==========================================

k8s-deploy:  ## Deploy K8s infrastructure and services
	@echo "Deploying K8s infrastructure..."
	kubectl apply -f infra/k8s/
	@echo "Deploying services with Helm..."
	helm upgrade --install content-engine ./infra/helm/content-engine
	@echo "✓ Deployment complete!"

k8s-status:  ## Show status of pods and services
	kubectl get pods -n content-automation
	@echo ""
	kubectl get svc -n content-automation

k8s-logs:  ## Tail logs from all pods
	kubectl logs -l app.kubernetes.io/name=content-engine -n content-automation -f --tail=50

k8s-clean:  ## Delete all K8s resources
	helm uninstall content-engine || true
	kubectl delete namespace content-automation || true
	@echo "✓ Cleanup complete!"

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
	@echo "  make seed-images    - Seed images to blob storage"
	@echo "  make services       - Start application services"
	@echo "  make local          - Run infra → seed-images → services"
	@echo "  make cleanup        - Stop and remove all containers"
	@echo "  make logs           - Tail docker-compose logs"
	@echo "  make wp-upload      - Generate and upload content to WordPress"
	@echo "  make wp-media-ids MEDIA_FOLDER=/path/to/images - Get WordPress media IDs"
	@echo ""
	@echo "Testing:"
	@echo "  make tests          - Run all tests in Docker"
	@echo ""
	@echo "Kubernetes:"
	@echo "  make k8s-deploy     - Deploy everything to K8s"
	@echo "  make k8s-status     - Show pods and services"
	@echo "  make k8s-logs       - Tail logs from all pods"
	@echo "  make k8s-clean      - Delete all K8s resources"

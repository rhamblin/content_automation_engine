.PHONY: infra local teardown publish consume logs k8s-deploy k8s-status k8s-logs k8s-clean help

# Default target
.DEFAULT_GOAL := help

# ==========================================
# Docker Compose (Original)
# ==========================================

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
	  up --build -d --no-deps redis

local:
	docker compose \
	  --env-file ./config/local/variables.env \
	  -f docker-compose.yaml \
	  -f config/local/docker-compose.override.yaml \
	  up --build -d

teardown:
	docker compose \
	  --env-file ./config/local/variables.env \
	  down -v

publish:
	. dev-tools/dev-shell.sh && python dev-tools/local_topic_publish.py

consume:
	. dev-tools/dev-shell.sh && python dev-tools/local_topic_consume.py
	
logs:
	docker compose logs -f

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
	@echo "Docker Compose:"
	@echo "  make infra          - Start PostgreSQL and Redis"
	@echo "  make local          - Start all services"
	@echo "  make teardown       - Stop and remove all containers"
	@echo "  make logs           - Tail docker-compose logs"
	@echo ""
	@echo "Kubernetes:"
	@echo "  make k8s-deploy     - Deploy everything to K8s"
	@echo "  make k8s-status     - Show pods and services"
	@echo "  make k8s-logs       - Tail logs from all pods"
	@echo "  make k8s-clean      - Delete all K8s resources"

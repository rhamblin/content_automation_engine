.PHONY: frontend setup infra seed-images services local cleanup publish consume wp-upload wp-media-ids pin-maker style-explorer get-pin-ids get-pin-stats plot-pin-analytics account-analytics campaign-manager unified-dashboard title-generator amazon-affiliate amazon-get amazon-url amazon-search logs tests k8s-deploy k8s-status k8s-logs k8s-clean help

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
	  management-api scheduler channel-worker \
	  analytics-collector activity-reporter promotion-orchestrator

local: infra seed-images services frontendw

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

pin-maker:
	. dev-tools/dev-shell.sh && cd dev-tools && python pin-maker/pin_maker.py $(FOLDER) $(if $(STYLE),--style $(STYLE),)

style-explorer:
	. dev-tools/dev-shell.sh && cd dev-tools/style-explorer && streamlit run style_explorer.py

get-pin-ids:
	. dev-tools/dev-shell.sh && cd dev-tools && python get-pin-ids/get_pin_ids.py

get-pin-stats:
	. dev-tools/dev-shell.sh && cd dev-tools && python get-pin-ids/get_pin_stats.py $(PIN_ID)

plot-pin-analytics:
	. dev-tools/dev-shell.sh && cd dev-tools && python get-pin-ids/plot_pin_analytics.py $(PIN_ID) --open

account-analytics:
	. dev-tools/dev-shell.sh && cd dev-tools && python account-analytics/account_analytics.py --open

campaign-manager:
	. dev-tools/dev-shell.sh && cd dev-tools && python campaign-manager/campaign_manager.py $(CMD)

unified-dashboard:
	. dev-tools/dev-shell.sh && cd dev-tools && python unified-dashboard/dashboard.py --open

title-generator:
	. dev-tools/dev-shell.sh && cd dev-tools && python title-generator/title_generator.py -c $(CHANNEL) -n $(NICHE) -k $(KEYWORD)

amazon-affiliate:
	. dev-tools/dev-shell.sh && cd dev-tools && python amazon-affiliate/amazon_affiliate.py $(CMD)

amazon-get:
	. dev-tools/dev-shell.sh && cd dev-tools && python amazon-affiliate/amazon_affiliate.py get $(ASIN) --json

amazon-url:
	. dev-tools/dev-shell.sh && cd dev-tools && python amazon-affiliate/amazon_affiliate.py url "$(URL)" --json

amazon-search:
	. dev-tools/dev-shell.sh && cd dev-tools && python amazon-affiliate/amazon_affiliate.py search "$(KEYWORDS)" --json

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
	@echo "  make pin-maker FOLDER=/path/to/images [STYLE=center_banner] - Create Pinterest pins"
	@echo "  make style-explorer - Visual style editor for Pinterest pins"
	@echo "  make get-pin-ids    - Fetch all Pinterest pins and IDs via OAuth"
	@echo "  make get-pin-stats PIN_ID=123 - Get pin campaign stats for yesterday"
	@echo "  make plot-pin-analytics PIN_ID=123 - Generate 14-day analytics HTML report"
	@echo "  make account-analytics - Generate account-wide analytics report"
	@echo "  make campaign-manager CMD='list' - Manage Pinterest campaigns"
	@echo "  make unified-dashboard - Multi-platform analytics dashboard"
	@echo "  make title-generator CHANNEL=pinterest NICHE=food KEYWORD='air fryer' - Generate titles"
	@echo "  make amazon-affiliate CMD='get B0BSHF7WHW' - Amazon affiliate (generic)"
	@echo "  make amazon-get ASIN=B0BSHF7WHW - Fetch product by ASIN (JSON)"
	@echo "  make amazon-url URL='https://www.amazon.com/dp/B0BSHF7WHW' - Fetch product by URL (JSON)"
	@echo "  make amazon-search KEYWORDS='chef knife' - Search products (JSON)"
	@echo ""
	@echo "Testing:"
	@echo "  make tests          - Run all tests in Docker"
	@echo ""
	@echo "Kubernetes:"
	@echo "  make k8s-deploy     - Deploy everything to K8s"
	@echo "  make k8s-status     - Show pods and services"
	@echo "  make k8s-logs       - Tail logs from all pods"
	@echo "  make k8s-clean      - Delete all K8s resources"

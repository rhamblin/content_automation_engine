.PHONY: infra local teardown push-message

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

push-message:
	. dev-tools/dev-shell.sh && python dev-tools/push_message.py

logs:
	docker compose logs -f

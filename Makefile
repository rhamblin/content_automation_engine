.PHONY: infra local down push-message

infra:
	docker compose \
	  --env-file ./config/dev/variables.env \
	  -f docker-compose.yaml \
	  -f config/dev/docker-compose.override.yaml \
	  up --build -d --no-deps db && \
	docker compose \
	  --env-file ./config/dev/variables.env \
	  -f docker-compose.yaml \
	  -f config/dev/docker-compose.override.yaml \
	  up --build -d --no-deps redis

local:
	docker compose \
	  --env-file ./config/dev/variables.env \
	  -f docker-compose.yaml \
	  -f config/dev/docker-compose.override.yaml \
	  up --build -d

down:
	docker compose \
	  --env-file ./config/dev/variables.env \
	  down -v

push-message:
	. dev-tools/dev-shell.sh && python dev-tools/push_message.py

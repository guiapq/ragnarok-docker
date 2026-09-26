SHELL := /bin/bash

SEED ?=
FORCE ?= --force

REGISTRY ?= 127.0.0.1:5000
TAG ?= v2

.PHONY: prepare up down world logs doctor ps build registry-up registry-down tag-images push-images clean-images prune

prepare:
	@./scripts/prepare.sh

up: prepare
	docker compose up -d

down:
	docker compose down

build: prepare
	docker compose build

registry-up:
	docker compose up -d registry

registry-down:
	docker compose stop registry

tag-images:
	docker tag ragnarok-docker-rathena:latest $(REGISTRY)/ragnarok/rathena:$(TAG) 2>/dev/null || docker tag ragnarok-docker-rathena $(REGISTRY)/ragnarok/rathena:$(TAG) || true
	docker tag ragnarok-docker-robrowser:latest $(REGISTRY)/ragnarok/robrowser:$(TAG) 2>/dev/null || docker tag ragnarok-docker-robrowser $(REGISTRY)/ragnarok/robrowser:$(TAG) || true
	docker tag ragnarok-docker-panel:latest $(REGISTRY)/ragnarok/panel:$(TAG) 2>/dev/null || docker tag ragnarok-docker-panel $(REGISTRY)/ragnarok/panel:$(TAG) || true

push-images: tag-images
	docker push $(REGISTRY)/ragnarok/rathena:$(TAG)
	docker push $(REGISTRY)/ragnarok/robrowser:$(TAG)
	docker push $(REGISTRY)/ragnarok/panel:$(TAG)

ps:
	docker compose ps

world:
	@if [ -z "$(SEED)" ]; then \
		echo "Uso: make world SEED=minha-seed"; \
		exit 1; \
	fi
	./new_world.sh "$(SEED)" "$(FORCE)"

logs:
	docker compose logs -f --tail=200

doctor:
	@echo "== Doctor =="
	@command -v docker >/dev/null || (echo "docker ausente" && exit 1)
	@command -v python3 >/dev/null || (echo "python3 ausente" && exit 1)
	@test -f .env || (echo ".env ausente" && exit 1)
	@test -f .env.rando || (echo ".env.rando ausente" && exit 1)
	@test -d data_base || (echo "data_base ausente" && exit 1)
	@test -f data/db/map_index.txt || (echo "data/db/map_index.txt ausente (execute: make prepare)" && exit 1)
	@echo "Ambiente básico OK"

clean-images:
	@echo "Removendo imagens locais construídas do projeto..."
	@docker images -q "*ragnarok*" | xargs -r docker rmi -f 2>/dev/null || true
	@docker image prune -f

prune: down
	@echo "Limpando containers parados, builder cache e imagens sem tag..."
	@docker container prune -f
	@docker builder prune -f
	@docker image prune -f

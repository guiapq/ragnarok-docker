#!/bin/bash

#set -euo pipefail

usage() {
    echo "Uso:"
    echo "  ./new_world.sh <seed> [--force]"
}

SEED="${1:-}"
FORCE="${2:-}"

if [ -z "$SEED" ]; then
    usage
    exit 1
fi

if [ "$FORCE" != "--force" ]; then
    echo "[ERRO] Esta operação remove data/db, data/npc e data/conf."
    echo "Execute novamente com --force para confirmar."
    usage
    exit 1
fi

if [ ! -f .env.rando ]; then
    echo "[ERRO] Arquivo .env.rando não encontrado."
    exit 1
fi

for cmd in docker python3 sed cp rm date tee; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "[ERRO] Dependência ausente: $cmd"
        exit 1
    fi
done

for dir in data_base/db data_base/npc data_base/conf; do
    if [ ! -d "$dir" ]; then
        echo "[ERRO] Diretório obrigatório ausente: $dir"
        exit 1
    fi
done

mkdir -p logs/world
LOG_FILE="logs/world/${SEED}-$(date +%Y%m%d-%H%M%S).log"

exec > >(tee -a "$LOG_FILE") 2>&1

echo "================================="
echo "Gerando novo mundo Ragnarok"
echo "Seed: $SEED"
echo "Log:  $LOG_FILE"
echo "================================="

echo
echo "Parando servidor para regeneração do mundo..."
docker compose stop rathena robrowser panel || true

echo
echo "Limpando mundo atual..."
rm -rf data/db data/npc data/conf

echo
echo "Copiando base limpa..."
cp -r data_base/db data/
cp -r data_base/npc data/
cp -r data_base/conf data/
mkdir -p data/db/import data/conf/import data/conf/msg_conf/import
if [ -d "data_base/db/import-tmpl" ]; then
    cp -n data_base/db/import-tmpl/* data/db/import/ 2>/dev/null || true
fi
if [ -d "data_base/conf/import-tmpl" ]; then
    cp -n data_base/conf/import-tmpl/* data/conf/import/ 2>/dev/null || true
fi
if [ -d "data_base/conf/msg_conf/import-tmpl" ]; then
    cp -n data_base/conf/msg_conf/import-tmpl/* data/conf/msg_conf/import/ 2>/dev/null || true
fi

echo
echo "Configurando seed..."
sed -i "s/^WORLD_SEED=.*/WORLD_SEED=$SEED/" .env.rando

echo
echo "Executando randomizer..."
bash scripts/randomize_world.sh

echo
echo "Reiniciando serviços do jogo..."
docker compose up -d rathena robrowser panel

echo
echo "Containers ativos:"
docker compose ps

echo
echo "================================="
echo "Mundo criado com sucesso!"
echo "Seed: $SEED"
echo "Log:  $LOG_FILE"
echo "================================="

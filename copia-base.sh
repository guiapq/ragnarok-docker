#!/bin/bash

set -e

FORCE=false
if [ "${1:-}" = "--force" ]; then
    FORCE=true
fi

# Se data/ já possui os arquivos vitais e não é force, pula
if [ "$FORCE" = false ] && [ -f "data/db/map_index.txt" ] && ([ -f "data/npc/pre-re/scripts_main.conf" ] || [ -f "data/npc/scripts_athena.conf" ]); then
    echo "=== [OK] Base local data/ (db, npc, conf) já está pronta ==="
    exit 0
fi

echo "================================="
echo "Copiando base do rAthena para data/"
echo "================================="

mkdir -p data/db data/npc data/conf

# Fonte 1: data_base/ local
if [ ! -f "data_base/db/map_index.txt" ]; then
    echo "data_base ausente ou incompleto. Executando setup-rathena-data_base-external.sh primeiro..."
    ./setup-rathena-data_base-external.sh
fi

if [ -f "data_base/db/map_index.txt" ]; then
    echo "Copiando DB a partir de data_base/db..."
    cp -r data_base/db/. ./data/db/

    echo "Copiando NPC a partir de data_base/npc..."
    cp -r data_base/npc/. ./data/npc/

    echo "Copiando CONF a partir de data_base/conf..."
    cp -r data_base/conf/. ./data/conf/

    # Garantir templates em db/import e conf/import para rAthena
    mkdir -p ./data/db/import ./data/conf/import ./data/conf/msg_conf/import
    if [ -d "data_base/db/import-tmpl" ]; then
        cp -n data_base/db/import-tmpl/* ./data/db/import/ 2>/dev/null || true
    fi
    if [ -d "data_base/conf/import-tmpl" ]; then
        cp -n data_base/conf/import-tmpl/* ./data/conf/import/ 2>/dev/null || true
    fi
    if [ -d "data_base/conf/msg_conf/import-tmpl" ]; then
        cp -n data_base/conf/msg_conf/import-tmpl/* ./data/conf/msg_conf/import/ 2>/dev/null || true
    fi
else
    # Fonte 2 (Fallback): Container Docker caso esteja construído
    CONTAINER="ragnarok-server"
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
        echo "Copiando a partir do container $CONTAINER..."
        docker cp $CONTAINER:/opt/rathena/db/. ./data/db/ 2>/dev/null || docker cp $CONTAINER:/usr/bin/rathena/db/. ./data/db/
        docker cp $CONTAINER:/opt/rathena/npc/. ./data/npc/ 2>/dev/null || docker cp $CONTAINER:/usr/bin/rathena/npc/. ./data/npc/
        docker cp $CONTAINER:/opt/rathena/conf/. ./data/conf/ 2>/dev/null || docker cp $CONTAINER:/usr/bin/rathena/conf/. ./data/conf/
    else
        echo "[ERRO CRÍTICO] Não foi possível encontrar a base limpa em data_base nem no container Docker!"
        exit 1
    fi
fi

echo "================================="
echo "Verificando integridade em data/"
echo "================================="

if [ -f data/db/map_index.txt ]; then
    echo "[OK] data/db/map_index.txt presente"
else
    echo "[ERRO CRÍTICO] data/db/map_index.txt ausente!"
    exit 1
fi

if [ -f data/npc/pre-re/scripts_main.conf ] || [ -f data/npc/scripts_athena.conf ]; then
    echo "[OK] Scripts de NPC presentes"
else
    echo "[ERRO CRÍTICO] Scripts de NPC ausentes em data/npc/!"
    exit 1
fi

echo "Cópia da base para data/ concluída com sucesso."

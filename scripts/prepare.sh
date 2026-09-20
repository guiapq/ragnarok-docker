#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "=== [CHECK] Verificando pré-requisitos do ambiente ragnarok-docker ==="

# 1. Arquivos de ambiente
if [ ! -f .env ]; then
    echo "[SETUP] Arquivo .env ausente. Criando a partir de .env.example..."
    cp .env.example .env
fi

if [ ! -f .env.rando ]; then
    echo "[SETUP] Arquivo .env.rando ausente. Criando a partir de .env.rando.example..."
    cp .env.rando.example .env.rando
fi

# 2. Base rAthena (data_base)
if [ ! -f "data_base/db/map_index.txt" ] || [ ! -d "data_base/.git" ]; then
    echo "[SETUP] data_base ausente ou incompleta. Executando setup do rAthena (preferindo momo)..."
    ./setup-rathena-data_base-external.sh
else
    echo "  ✓ rAthena base (data_base): OK"
fi

# 3. Base roBrowser (robrowser_base)
if [ ! -f "robrowser_base/package.json" ] || [ ! -d "robrowser_base/.git" ]; then
    echo "[SETUP] robrowser_base ausente. Executando setup do roBrowserLegacy (preferindo momo)..."
    ./setup-robrowser-base-external.sh
else
    echo "  ✓ roBrowser base (robrowser_base): OK"
fi

# 4. Dados em runtime (data/db, data/npc, data/conf)
if [ ! -f "data/db/map_index.txt" ] || ([ ! -f "data/npc/pre-re/scripts_main.conf" ] && [ ! -f "data/npc/scripts_athena.conf" ]); then
    echo "[SETUP] Runtime data/ (db, npc, conf) ausente ou vazio. Copiando da base..."
    ./copia-base.sh
else
    echo "  ✓ Runtime data/ (db, npc, conf): OK"
fi

echo "=== [OK] Ambiente 100% preparado e pronto para o Docker ==="

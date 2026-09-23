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

# 5. Templates de importação (db, conf, msg_conf) do rAthena
mkdir -p data_base/db/import data/db/import data_base/conf/import data/conf/import data_base/conf/msg_conf/import data/conf/msg_conf/import
if [ -d "data_base/db/import-tmpl" ]; then
    cp -n data_base/db/import-tmpl/* data_base/db/import/ 2>/dev/null || true
    cp -n data_base/db/import-tmpl/* data/db/import/ 2>/dev/null || true
fi
if [ -d "data_base/conf/import-tmpl" ]; then
    cp -n data_base/conf/import-tmpl/* data_base/conf/import/ 2>/dev/null || true
    cp -n data_base/conf/import-tmpl/* data/conf/import/ 2>/dev/null || true
fi
if [ -d "data_base/conf/msg_conf/import-tmpl" ]; then
    cp -n data_base/conf/msg_conf/import-tmpl/* data_base/conf/msg_conf/import/ 2>/dev/null || true
    cp -n data_base/conf/msg_conf/import-tmpl/* data/conf/msg_conf/import/ 2>/dev/null || true
fi

# 6. Painel Web Laravel (web/)
if [ ! -f "web/composer.json" ] || [ ! -f "web/artisan" ]; then
    echo "[SETUP] Painel Web (web/) ausente ou incompleto. Inicializando submódulo git..."
    git submodule update --init --force --recursive web 2>/dev/null || {
        echo "[WARN] git submodule falhou. Tentando clonar repositório do painel diretamente..."
        _tmp_web=$(mktemp -d)
        if git clone --depth=1 https://github.com/guiapq/ragnabraza-cp.git "$_tmp_web" 2>/dev/null; then
            mkdir -p web
            cp -rn "$_tmp_web"/. web/ 2>/dev/null || cp -r "$_tmp_web"/* web/ 2>/dev/null || true
            rm -rf "$_tmp_web"
        fi
    }
    if [ -f "web/composer.json" ]; then
        echo "  ✓ Painel Web (web): Configurado com sucesso!"
    else
        echo "[ERRO] Falha ao obter arquivos do painel web em web/."
    fi
else
    echo "  ✓ Painel Web (web): OK"
fi

echo "=== [OK] Ambiente 100% preparado e pronto para o Docker ==="

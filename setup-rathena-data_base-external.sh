#!/bin/bash

set -e

FORCE=false
if [ "${1:-}" = "--force" ]; then
    FORCE=true
fi

# Se já existe e está íntegro, pula download a não ser que --force seja passado
if [ "$FORCE" = false ] && [ -f "data_base/db/map_index.txt" ] && [ -d "data_base/.git" ]; then
    echo "=== [OK] Base data_base (rAthena) já está instalada e pronta ==="
    exit 0
fi

echo "================================="
echo "Preparando base do rAthena (data_base)"
echo "================================="

# Carrega configurações do .env caso existam
if [ -f .env ]; then
    export $(grep -E '^(RATHENA_REPO|RATHENA_COMMIT)=' .env | xargs) 2>/dev/null || true
fi

MOMO_REPO="${RATHENA_REPO:-http://192.168.0.128:3000/guiapq/rathena.git}"
GITHUB_REPO="https://github.com/guiapq/rathena.git"
COMMIT="${RATHENA_COMMIT:-ac46920e73819662811573253d9b22592e8ad985}"

# Detecta se momo está acessível (timeout de 2 segundos)
TARGET_REPO="$GITHUB_REPO"
echo -n "Testando conectividade com o repositório rAthena local (momo)... "
if timeout 2 git ls-remote --exit-code -h "$MOMO_REPO" >/dev/null 2>&1; then
    echo "[OK: MOMO DETECTADA]"
    TARGET_REPO="$MOMO_REPO"
else
    echo "[INDISPONÍVEL: Usando GitHub]"
    TARGET_REPO="$GITHUB_REPO"
fi

echo "Alvo: $TARGET_REPO (Commit: $COMMIT)"

rm -rf data_base
mkdir -p data_base
cd data_base
git init
git remote add origin "$TARGET_REPO"

echo "Baixando base do rAthena..."
if ! git fetch --depth 1 origin "$COMMIT" 2>/dev/null; then
    echo "Commit específico falhou no fetch shallow direto, tentando branch master..."
    git fetch --depth 1 origin master
fi
git checkout -B master FETCH_HEAD

cd ..

echo "================================="
echo "Verificando estrutura rAthena"
echo "================================="
if [ -f data_base/db/map_index.txt ]; then
    echo "[OK] db/map_index.txt encontrado"
else
    echo "[ERRO CRÍTICO] db/map_index.txt NÃO encontrado em data_base!"
    exit 1
fi

echo "Setup de data_base concluído com sucesso."

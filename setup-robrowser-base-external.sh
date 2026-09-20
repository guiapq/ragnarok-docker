#!/bin/bash

set -e

FORCE=false
if [ "${1:-}" = "--force" ]; then
    FORCE=true
fi

# Se já existe e está íntegro, pula download a não ser que --force seja passado
if [ "$FORCE" = false ] && [ -f "robrowser_base/package.json" ] && [ -d "robrowser_base/.git" ]; then
    echo "=== [OK] Base robrowser_base já está instalada e pronta ==="
    exit 0
fi

echo "================================="
echo "Preparando base do roBrowserLegacy (robrowser_base)"
echo "================================="

# Carrega configurações do .env caso existam
if [ -f .env ]; then
    export $(grep -E '^(ROBROWSER_REPO|ROBROWSER_COMMIT)=' .env | xargs) 2>/dev/null || true
fi

MOMO_REPO="${ROBROWSER_REPO:-http://192.168.0.128:3000/guiapq/roBrowserLegacy.git}"
GITHUB_REPO="https://github.com/guiapq/roBrowserLegacy.git"
COMMIT="${ROBROWSER_COMMIT:-1433244}"

# Detecta se momo está acessível (timeout de 2 segundos)
TARGET_REPO="$GITHUB_REPO"
echo -n "Testando conectividade com o repositório roBrowser local (momo)... "
if timeout 2 git ls-remote --exit-code -h "$MOMO_REPO" >/dev/null 2>&1; then
    echo "[OK: MOMO DETECTADA]"
    TARGET_REPO="$MOMO_REPO"
else
    echo "[INDISPONÍVEL: Usando GitHub]"
    TARGET_REPO="$GITHUB_REPO"
fi

echo "Alvo: $TARGET_REPO (Commit: $COMMIT)"

rm -rf robrowser_base
mkdir -p robrowser_base
cd robrowser_base
git init
git remote add origin "$TARGET_REPO"

echo "Baixando base do roBrowserLegacy..."
if ! git fetch --depth 1 origin "$COMMIT" 2>/dev/null; then
    echo "Commit específico falhou no fetch shallow direto, tentando branch master..."
    git fetch --depth 1 origin master
fi
git checkout -B master FETCH_HEAD

cd ..

echo "================================="
echo "Verificando estrutura roBrowserLegacy"
echo "================================="
if [ -f robrowser_base/package.json ]; then
    echo "[OK] package.json encontrado em robrowser_base"
else
    echo "[ERRO CRÍTICO] package.json NÃO encontrado em robrowser_base!"
    exit 1
fi

echo "Setup de robrowser_base concluído com sucesso."

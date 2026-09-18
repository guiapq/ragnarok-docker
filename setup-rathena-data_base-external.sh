#!/bin/bash

set -e

echo "================================="
echo "Baixando base limpa do rAthena (LOCKED)"
echo "================================="

REPO="https://github.com/guiapq/rathena.git"
COMMIT="ac46920e73819662811573253d9b22592e8ad985"

# limpa base anterior
rm -rf data_base

echo
echo "Clonando repositório (shallow fetch para commit travado)..."
mkdir -p data_base
cd data_base
git init
git remote add origin "$REPO"
git fetch --depth 1 origin "$COMMIT"
git checkout FETCH_HEAD

echo
echo "================================="
echo "Base instalada com sucesso"
echo "================================="

echo
echo "HEAD atual:"
git rev-parse HEAD

echo
echo "================================="
echo "Verificando estrutura esperada"
echo "================================="

if [ -f db/mob_db.txt ] || [ -f db/re/mob_db.txt ]; then
    echo "[OK] mob_db.txt encontrado"
else
    echo "[ERRO] mob_db.txt NÃO encontrado"
fi

if [ -f db/item_db.txt ] || [ -f db/re/item_db.txt ]; then
    echo "[OK] item_db.txt encontrado"
else
    echo "[ERRO] item_db.txt NÃO encontrado"
fi

echo
echo "================================="
echo "Setup concluído"
echo "================================="

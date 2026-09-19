#!/bin/bash

set -e

echo "================================="
echo "Baixando base de Tradução Cronus (guiapq/Cronus-traducao)"
echo "================================="

REPO="https://github.com/guiapq/Cronus-traducao.git"

if [ -d "cronus_base/.git" ]; then
    echo "Base local cronus_base já existe. Verificando commit..."
    cd cronus_base
    git rev-parse HEAD
    cd ..
    echo "OK."
    exit 0
fi

mkdir -p cronus_base
cd cronus_base
git init
git remote add origin "$REPO"
echo "Buscando arquivos do repositório..."
git fetch --depth 1 origin master
git checkout -B master FETCH_HEAD

echo
echo "================================="
echo "Cronus-traducao instalado com sucesso em cronus_base"
echo "================================="
echo "HEAD atual:"
git rev-parse HEAD

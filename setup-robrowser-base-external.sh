#!/bin/bash

set -e

echo "================================="
echo "Baixando base do roBrowserLegacy (LOCKED)"
echo "================================="

REPO="https://github.com/guiapq/roBrowserLegacy.git"
COMMIT="fd9183fe552739fa93ac555c8dfa0b67cbbdeff5"

if [ -d "robrowser_base/.git" ]; then
    echo "Base local robrowser_base já existe. Verificando commit..."
    cd robrowser_base
    git rev-parse HEAD
    cd ..
    echo "OK."
    exit 0
fi

mkdir -p robrowser_base
cd robrowser_base
git init
git remote add origin "$REPO"
git fetch --depth 1 origin "$COMMIT"
git checkout -B master FETCH_HEAD

echo
echo "================================="
echo "roBrowserLegacy instalado com sucesso"
echo "================================="
echo "HEAD atual:"
git rev-parse HEAD

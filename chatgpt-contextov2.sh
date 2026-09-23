#!/bin/bash

echo "=================================================="
echo "CHATGPT PROJECT CONTEXT DUMP"
echo "Projeto: Ragnarok Docker Server"
echo "=================================================="

############################################
# DATA
############################################

echo
echo "===== DATA ====="
date

############################################
# GIT INFO
############################################

if command -v git >/dev/null 2>&1; then

    echo
    echo "===== GIT INFO ====="

    echo
    echo "Commit atual:"
    git rev-parse HEAD 2>/dev/null || echo "repo git não detectado"

    echo
    echo "Branch atual:"
    git branch --show-current 2>/dev/null || true

    echo
    echo "Últimos commits:"
    git log --oneline -5 2>/dev/null || true

    echo
    echo "Status:"
    git status --short 2>/dev/null || true

fi

############################################
# DOCKER STATUS
############################################

if command -v docker >/dev/null 2>&1; then

    echo
    echo "===== DOCKER CONTAINERS ====="

    docker ps 2>/dev/null || echo "docker não disponível"

    echo
    echo "===== DOCKER COMPOSE ====="

    docker compose ps 2>/dev/null || true

fi

############################################
# ESTRUTURA DO PROJETO
############################################

echo
echo "===== ESTRUTURA DO PROJETO ====="

if command -v tree >/dev/null 2>&1; then
    tree -L 2 \
        -I "data|data_base|.git|__pycache__"
else
    find . -maxdepth 2 -type d \
        ! -path "./data*" \
        ! -path "./data_base*" \
        ! -path "./.git*" 
fi

############################################
# SCRIPTS PRINCIPAIS
############################################

echo
echo "===== SCRIPTS PRINCIPAIS ====="

ls -1 *.sh 2>/dev/null || true

############################################
# Função para imprimir arquivos
############################################

print_file () {

    FILE=$1
    DESC=$2

    if [ -f "$FILE" ]; then

        echo
        echo "--------------------------------------------------"
        echo "Arquivo: $FILE"
        echo "Descrição: $DESC"
        echo "--------------------------------------------------"

        sed -n '1,400p' "$FILE"

        echo
    fi
}

############################################
# Root do projeto
############################################

print_file README.md "README principal do projeto"
print_file docker-compose.yml "Orquestração dos containers"

############################################
# Scripts principais
############################################

print_file new_world.sh "Gerador de mundos procedural"
print_file copia-base.sh "Copia base limpa do rAthena"
print_file setup-rathena-data_base-external.sh "Download da base rAthena"

############################################
# Docker rAthena
############################################

print_file docker/rathena/Dockerfile "Imagem customizada do container rAthena"
print_file docker/rathena/start.sh "Script de inicialização do container"
print_file docker/rathena/casual.sh "Preset CASUAL do servidor"

############################################
# Ferramentas custom
############################################

print_file docker/rathena/cat_python.py "Ferramenta para inspeção de configs"

############################################
# Tools (randomizers)
############################################

if [ -d tools ]; then

    echo
    echo "===== TOOLS ====="

    for f in tools/*.py; do
        print_file "$f" "Ferramenta da pasta tools"
    done

fi

############################################
# Documentação
############################################

if [ -d docs ]; then

    echo
    echo "===== DOCUMENTAÇÃO ====="

    for f in docs/*.md; do
        print_file "$f" "Documento da pasta docs"
    done

fi

############################################
# SQL init
############################################

if [ -d sql-init ]; then

    echo
    echo "===== SQL INIT ====="

    for f in sql-init/*; do
        print_file "$f" "Script SQL de inicialização"
    done

fi

############################################
# Variáveis importantes do projeto
############################################

echo
echo "===== VARIÁVEIS IMPORTANTES ====="

grep -E "WORLD_|RATHENA_|ENABLE_RANDOM" .env* 2>/dev/null || true

echo
echo "=================================================="
echo "FIM DO CONTEXTO DO PROJETO"
echo "=================================================="

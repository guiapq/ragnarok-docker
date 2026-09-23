#!/bin/bash

echo "=================================================="
echo "CHATGPT PROJECT CONTEXT DUMP"
echo "Projeto: Ragnarok Docker Server"
echo "=================================================="

echo
echo "===== DATA ====="
date

############################################
# GIT INFO
############################################

if command -v git >/dev/null 2>&1; then
    echo
    echo "===== GIT COMMIT ====="
    git rev-parse HEAD 2>/dev/null || echo "git repo não detectado"

    echo
    echo "===== GIT STATUS ====="
    git status 2>/dev/null || true
fi

############################################
# DOCKER STATUS
############################################

if command -v docker >/dev/null 2>&1; then
    echo
    echo "===== DOCKER CONTAINERS ====="
    docker ps 2>/dev/null || echo "docker não disponível"
fi

############################################
# ESTRUTURA DO PROJETO
############################################

echo
echo "===== ESTRUTURA DO PROJETO ====="

if command -v tree >/dev/null 2>&1; then
    tree -L 3
else
    find . -maxdepth 3 -type d
fi


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

        sed -n '1,500p' "$FILE"

        echo
    fi
}

############################################
# Root do projeto
############################################

print_file README.md "README principal do projeto"
print_file docker-compose.yml "Orquestração dos containers"

############################################
# Docker rAthena
############################################

print_file docker/rathena/Dockerfile "Imagem customizada do container rAthena"
print_file docker/rathena/start.sh "Script de inicialização do container"
print_file docker/rathena/casual.sh "Preset CASUAL que configura o servidor"

############################################
# Ferramentas custom
############################################

print_file docker/rathena/cat_python.py "Ferramenta para inspeção de configs"

############################################
# Documentação
############################################

if [ -d docs ]; then
    for f in docs/*.md; do
        print_file "$f" "Documento da pasta docs"
    done
fi

############################################
# SQL init
############################################

if [ -d sql-init ]; then
    for f in sql-init/*; do
        print_file "$f" "Script SQL de inicialização"
    done
fi

echo
echo "=================================================="
echo "FIM DO CONTEXTO DO PROJETO"
echo "=================================================="

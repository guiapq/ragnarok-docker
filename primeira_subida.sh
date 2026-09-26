#!/bin/bash
set -euo pipefail

# ==============================================================================
# Script 1: Primeira Subida (RagnaRogue)
# Executa todos os comandos de inicialização descritos no README com uma
# seed procedural aleatória no formato: adjetivo-nome-de-monstro-numero
# ==============================================================================

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# Cores para saída amigável no terminal
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
CYAN="\033[0;36m"
RED="\033[0;31m"
BOLD="\033[1m"
RESET="\033[0m"

echo -e "${CYAN}${BOLD}================================================================${RESET}"
echo -e "${CYAN}${BOLD}          RagnaRogue — Script de Primeira Subida               ${RESET}"
echo -e "${CYAN}${BOLD}================================================================${RESET}"
echo

# 1. Dependências do host
for cmd in docker make python3; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo -e "${RED}[ERRO] Dependência obrigatória ausente no sistema: $cmd${RESET}"
        exit 1
    fi
done

# 2. Gerar seed procedural aleatória (adjetivo-nome-de-monstro-numero)
echo -e "${YELLOW}--> Gerando semente de mundo aleatória (adjetivo-nome-de-monstro-numero)...${RESET}"
if [ -f "tools/generate_seed.py" ]; then
    SEED=$(python3 tools/generate_seed.py)
else
    # Fallback caso o script python não esteja disponível
    ADJ_LIST=("furioso" "sombrio" "veloz" "valente" "lendario" "mistico" "eterno" "flamejante" "congelante" "arcano")
    MOB_LIST=("poring" "lunatic" "deviruchi" "baphomet" "pecopeco" "poporing" "angeling" "ghostring" "orc-hero")
    RAND_ADJ=${ADJ_LIST[$RANDOM % ${#ADJ_LIST[@]}]}
    RAND_MOB=${MOB_LIST[$RANDOM % ${#MOB_LIST[@]}]}
    RAND_NUM=$((RANDOM % 9000 + 1000))
    SEED="${RAND_ADJ}-${RAND_MOB}-${RAND_NUM}"
fi

echo -e "${GREEN}✓ Seed gerada para este mundo: ${BOLD}${SEED}${RESET}"
echo

# 3. Preparação inicial do ambiente (garante .env, .env.rando e bases antes do doctor)
echo -e "${CYAN}--> [1/6] Preparando ambiente e bases de dados (make prepare)...${RESET}"
make prepare

# 4. Validar pré-requisitos do ambiente (README passo 1)
echo -e "${CYAN}--> [2/6] Validando ambiente (make doctor)...${RESET}"
make doctor

# 5. Inicializar registry local de imagens na porta 5000 (README passo 2)
echo -e "${CYAN}--> [3/6] Inicializando Registry Docker local (make registry-up)...${RESET}"
make registry-up

# 6. Compilar imagens otimizadas (README passo 3)
echo -e "${CYAN}--> [4/6] Compilando imagens Docker otimizadas (make build)...${RESET}"
make build

# 7. Publicar imagens no registry local (README passo 4)
echo -e "${CYAN}--> [5/6] Publicando imagens no Registry local (make push-images)...${RESET}"
make push-images

# 8. Gerar mundo procedural com a semente aleatória (README passo 5)
echo -e "${CYAN}--> [6/6] Gerando mundo procedural com seed: ${SEED} (make world)...${RESET}"
make world SEED="${SEED}"

# 9. Inicializar stack completa (README passo 6)
echo -e "${CYAN}--> Inicializando todos os serviços da stack (make up)...${RESET}"
make up

echo
echo -e "${YELLOW}--> Aguardando estabilização dos serviços...${RESET}"
sleep 5

echo
echo -e "${GREEN}${BOLD}================================================================${RESET}"
echo -e "${GREEN}${BOLD}       SERVIDOR RAGNAROGUE INICIALIZADO COM SUCESSO!            ${RESET}"
echo -e "${GREEN}${BOLD}================================================================${RESET}"
echo -e "  ${BOLD}Seed Ativa:${RESET}      ${CYAN}${SEED}${RESET}"
echo -e "  🎮 ${BOLD}Jogar no Navegador:${RESET}  ${GREEN}http://localhost:8001${RESET}"
echo -e "  🌐 ${BOLD}Painel de Controle:${RESET}  ${GREEN}http://localhost:8000${RESET}"
echo -e "  🗄️ ${BOLD}phpMyAdmin:${RESET}          ${GREEN}http://localhost:8080${RESET}"
echo
echo -e "  🔑 ${BOLD}Credenciais Padrão:${RESET}"
echo -e "     - ${BOLD}Admin GM:${RESET}  roadmin / roadmin (ou admin / admin)"
echo -e "     - ${BOLD}Teste:${RESET}     teste_swordie ... teste_extended (senha: teste123)"
echo -e "     - ${BOLD}Banco:${RESET}     ragnarok / ragnarok (root: root)"
echo -e "${GREEN}${BOLD}================================================================${RESET}"

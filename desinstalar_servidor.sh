#!/bin/bash
set -euo pipefail

# ==============================================================================
# Script 4: Desinstalar Servidor (RagnaRogue)
# - Para e remove todos os containers Docker da stack.
# - Remove todos os volumes nomeados (db_data, registry_data, dados persistentes).
# - Remove todas as imagens Docker locais criadas para o projeto.
# - Apaga a pasta inteira do projeto no sistema de arquivos.
# ==============================================================================

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FORCE="${1:-}"

# Cores
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
CYAN="\033[0;36m"
RED="\033[0;31m"
BOLD="\033[1m"
RESET="\033[0m"

echo -e "${RED}${BOLD}================================================================${RESET}"
echo -e "${RED}${BOLD}        ATENÇÃO — DESINSTALAÇÃO TOTAL DO RAGNAROGUE            ${RESET}"
echo -e "${RED}${BOLD}================================================================${RESET}"
echo -e "${YELLOW}Esta operação é DESTRUTIVA e IRREVERSÍVEL:${RESET}"
echo -e "  1. Irá parar e remover TODOS os containers Docker do ecossistema."
echo -e "  2. Irá excluir TODOS os volumes Docker (banco de dados, contas, registry)."
echo -e "  3. Irá remover todas as imagens Docker compiladas do projeto."
echo -e "  4. Irá ${RED}${BOLD}DELETAR PERMANENTEMENTE A PASTA DO PROJETO:${RESET}"
echo -e "     ${BOLD}${ROOT_DIR}${RESET}"
echo

# Confirmação do usuário (a menos que passe --force ou -y)
if [ "$FORCE" != "--force" ] && [ "$FORCE" != "-y" ] && [ "$FORCE" != "-f" ]; then
    read -r -p "Você tem certeza absoluta que deseja desinstalar tudo e apagar a pasta? [digite 'sim' para confirmar]: " CONFIRM
    if [ "$CONFIRM" != "sim" ] && [ "$CONFIRM" != "SIM" ] && [ "$CONFIRM" != "s" ] && [ "$CONFIRM" != "S" ]; then
        echo -e "${GREEN}Operação cancelada pelo usuário. Nada foi alterado.${RESET}"
        exit 0
    fi
fi

echo
echo -e "${CYAN}--> [1/4] Parando e removendo todos os containers, redes e volumes Docker...${RESET}"
docker compose down -v --remove-orphans || true

echo -e "${CYAN}--> [2/4] Removendo imagens Docker associadas ao projeto...${RESET}"
docker images -q "*ragnarok*" 2>/dev/null | xargs -r docker rmi -f 2>/dev/null || true
docker image prune -f >/dev/null 2>&1 || true

echo -e "${CYAN}--> [3/4] Limpando eventuais volumes órfãos residuais...${RESET}"
docker volume ls -q -f "name=ragnarok" 2>/dev/null | xargs -r docker volume rm 2>/dev/null || true

echo -e "${CYAN}--> [4/4] Preparando remoção definitiva da pasta do projeto...${RESET}"

# Como o script está dentro da pasta a ser removida, criamos um sub-executor temporário em /tmp
# para liberar o diretório corrente e evitar erros de processo no sistema operacional.
CLEANUP_SCRIPT="/tmp/ragnarok_uninstall_$(date +%s).sh"

cat << EOF > "$CLEANUP_SCRIPT"
#!/bin/bash
set -e
cd /tmp
echo -e "${YELLOW}--> Excluindo diretório: ${ROOT_DIR}...${RESET}"
rm -rf "${ROOT_DIR}"

echo
echo -e "${GREEN}${BOLD}================================================================${RESET}"
echo -e "${GREEN}${BOLD}     RAGNAROGUE DESINSTALADO E DIRETÓRIO REMOVIDO COM SUCESSO!   ${RESET}"
echo -e "${GREEN}${BOLD}================================================================${RESET}"
echo -e "  ✓ Containers e redes removidos."
echo -e "  ✓ Volumes e banco de dados excluídos."
echo -e "  ✓ Imagens Docker limpas."
echo -e "  ✓ Pasta ${ROOT_DIR} apagada."
echo -e "${GREEN}${BOLD}================================================================${RESET}"

# Auto-remover o script de cleanup temporário
rm -f "\$0"
EOF

chmod +x "$CLEANUP_SCRIPT"

# Transfere a execução para o script temporário e encerra
exec "$CLEANUP_SCRIPT"

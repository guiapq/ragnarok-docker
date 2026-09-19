#!/bin/bash
set -euo pipefail

MOMO2_IP="${1:-192.168.0.128}"
MOMO2_PORT="${2:-3000}"
GIT_USER="${3:-guiapq}"

echo "======================================================"
echo "Sincronizador de Repositórios para o Git Local (momo2)"
echo "Alvo: http://${MOMO2_IP}:${MOMO2_PORT}/${GIT_USER}"
echo "======================================================"

MOMO2_PASS="${4:-}"
if [ -z "$MOMO2_PASS" ]; then
    echo -n "Digite a senha (ou token) do usuário '${GIT_USER}' no Gitea: "
    read -rs MOMO2_PASS
    echo ""
fi

sync_repo() {
    local name="$1"
    local dir="$2"

    if [ ! -e "$dir/.git" ]; then
        echo "[SKIP] Diretório $dir não é um repositório git válido."
        return
    fi

    echo "--- Sincronizando: $name ($dir) ---"
    cd "$dir"

    local push_url
    if [ -n "$MOMO2_PASS" ]; then
        push_url="http://${GIT_USER}:${MOMO2_PASS}@${MOMO2_IP}:${MOMO2_PORT}/${GIT_USER}/${name}.git"
    else
        push_url="http://${MOMO2_IP}:${MOMO2_PORT}/${GIT_USER}/${name}.git"
    fi

    local clean_url="http://${MOMO2_IP}:${MOMO2_PORT}/${GIT_USER}/${name}.git"

    if ! git remote get-url momo2 >/dev/null 2>&1; then
        echo "Adicionando remote 'momo2': $clean_url"
        git remote add momo2 "$push_url"
    else
        git remote set-url momo2 "$push_url"
    fi

    echo "Enviando branches e tags para momo2..."
    git push momo2 --all || {
        echo "[WARN] Falha ao enviar branches para $clean_url."
    }
    git push momo2 --tags || true

    # Sanitiza a URL do remote para não expor a senha em git remote -v
    git remote set-url momo2 "$clean_url"

    cd - >/dev/null
}

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 1. rAthena
sync_repo "rathena" "$ROOT_DIR/data_base"

# 2. ragnarok-docker
sync_repo "ragnarok-docker" "$ROOT_DIR"

# 3. ragnabraza-cp (web panel)
sync_repo "ragnabraza-cp" "$ROOT_DIR/web"

echo "======================================================"
echo "Sincronização concluída!"
echo "Para usar no docker-compose, defina em .env:"
echo "RATHENA_REPO=http://${MOMO2_IP}:${MOMO2_PORT}/${GIT_USER}/rathena.git"
echo "ROBROWSER_REPO=http://${MOMO2_IP}:${MOMO2_PORT}/${GIT_USER}/roBrowserLegacy.git"
echo "======================================================"

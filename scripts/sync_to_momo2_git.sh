#!/bin/bash
set -euo pipefail

MOMO2_IP="${1:-192.168.0.128}"
MOMO2_PORT="${2:-3000}"
GIT_USER="${3:-guiapq}"

echo "======================================================"
echo "Sincronizador de Repositórios para o Git Local (momo2)"
echo "Alvo: http://${MOMO2_IP}:${MOMO2_PORT}/${GIT_USER}"
echo "======================================================"

sync_repo() {
    local name="$1"
    local dir="$2"

    if [ ! -d "$dir/.git" ]; then
        echo "[SKIP] Diretório $dir não é um repositório git válido."
        return
    fi

    echo "--- Sincronizando: $name ($dir) ---"
    cd "$dir"

    local remote_url="http://${MOMO2_IP}:${MOMO2_PORT}/${GIT_USER}/${name}.git"

    if ! git remote get-url momo2 >/dev/null 2>&1; then
        echo "Adicionando remote 'momo2': $remote_url"
        git remote add momo2 "$remote_url"
    else
        git remote set-url momo2 "$remote_url"
    fi

    echo "Enviando branches e tags para momo2..."
    git push momo2 --all || {
        echo "[WARN] Não foi possível fazer push automático para $remote_url."
        echo "       Certifique-se de que o repositório foi criado no Gitea/GitLab ou que o login foi autenticado."
    }
    git push momo2 --tags || true

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

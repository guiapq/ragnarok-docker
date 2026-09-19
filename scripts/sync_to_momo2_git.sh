#!/bin/bash
set -euo pipefail

MOMO2_IP="${1:-192.168.0.128}"
MOMO2_PORT="${2:-3000}"
GIT_USER="${3:-guiapq}"

echo "======================================================"
echo "Sincronizador de Repositórios para o Git Local (momo2)"
echo "Alvo: http://${MOMO2_IP}:${MOMO2_PORT}/${GIT_USER}"
echo "======================================================"

MOMO2_SSH_PORT="2222"
USE_SSH=false

if ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout=2 -p "${MOMO2_SSH_PORT}" "git@${MOMO2_IP}" 2>&1 | grep -q "${GIT_USER}"; then
    echo "[AUTH] Chave SSH detectada e autenticada com sucesso no Gitea (porta ${MOMO2_SSH_PORT})!"
    USE_SSH=true
else
    echo "[AUTH] SSH direto não disponível ou sem chave configurada. Usando HTTP."
    MOMO2_PASS="${4:-}"
    if [ -z "$MOMO2_PASS" ]; then
        echo -n "Digite a senha (ou token) do usuário '${GIT_USER}' no Gitea: "
        read -rs MOMO2_PASS
        echo ""
    fi
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

    # Verifica se existem commits locais antes de enviar
    if ! git rev-parse HEAD >/dev/null 2>&1; then
        echo "[SKIP] $name não possui commits locais válidos para envio."
        cd - >/dev/null
        return
    fi

    # Se o repositório estiver em detached HEAD, cria/aponta o branch 'master'
    local current_branch
    current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
    if [ "$current_branch" = "HEAD" ] || [ -z "$current_branch" ]; then
        echo "[$name] Repositório em detached HEAD. Criando/apontando branch 'master'..."
        git checkout -B master
    fi

    local push_url
    local clean_url
    if [ "$USE_SSH" = true ]; then
        push_url="ssh://git@${MOMO2_IP}:${MOMO2_SSH_PORT}/${GIT_USER}/${name}.git"
        clean_url="$push_url"
    else
        if [ -n "${MOMO2_PASS:-}" ]; then
            push_url="http://${GIT_USER}:${MOMO2_PASS}@${MOMO2_IP}:${MOMO2_PORT}/${GIT_USER}/${name}.git"
        else
            push_url="http://${MOMO2_IP}:${MOMO2_PORT}/${GIT_USER}/${name}.git"
        fi
        clean_url="http://${MOMO2_IP}:${MOMO2_PORT}/${GIT_USER}/${name}.git"
    fi

    if ! git remote get-url momo2 >/dev/null 2>&1; then
        echo "Adicionando remote 'momo2': $clean_url"
        git remote add momo2 "$push_url"
    else
        git remote set-url momo2 "$push_url"
    fi

    echo "Enviando branches e tags para momo2..."
    local push_failed=false
    if ! git push momo2 --all; then
        echo "Tentando envio direto da branch master..."
        if ! git push -u momo2 master; then
            push_failed=true
        fi
    fi
    git push momo2 --tags >/dev/null 2>&1 || true

    if [ "$push_failed" = true ]; then
        echo "[WARN] Falha ao enviar para $clean_url."
        if [ -f .git/shallow ]; then
            echo "------------------------------------------------------------------"
            echo "[MOTIVO] Este repositório é shallow (.depth 1) e o Git do Gitea bloqueia"
            echo "         atualizações shallow por segurança por padrão."
            echo "         Para liberar commits shallow no seu Gitea do momo2, execute lá:"
            echo "         docker exec momo2-gitea git config --system receive.shallowUpdate true"
            echo "------------------------------------------------------------------"
        fi
    else
        echo "[OK] $name sincronizado com sucesso!"
    fi

    # Sanitiza a URL do remote para não expor senha em git remote -v
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

# 4. roBrowserLegacy
sync_repo "roBrowserLegacy" "$ROOT_DIR/robrowser_base"

# 5. Cronus-traducao
sync_repo "Cronus-traducao" "$ROOT_DIR/cronus_base"

echo "======================================================"
echo "Sincronização concluída!"
echo "Para usar no docker-compose, defina em .env:"
echo "RATHENA_REPO=http://${MOMO2_IP}:${MOMO2_PORT}/${GIT_USER}/rathena.git"
echo "ROBROWSER_REPO=http://${MOMO2_IP}:${MOMO2_PORT}/${GIT_USER}/roBrowserLegacy.git"
echo "CRONUS_REPO=http://${MOMO2_IP}:${MOMO2_PORT}/${GIT_USER}/Cronus-traducao.git"
echo "======================================================"

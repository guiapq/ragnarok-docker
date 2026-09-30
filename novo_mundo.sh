#!/bin/bash
set -euo pipefail

# ==============================================================================
# Script 3: Novo Mundo (RagnaRogue)
# - Cria uma nova seed procedural (aleatória no formato adjetivo-nome-de-monstro-numero
#   caso nenhum parâmetro seja fornecido).
# - Reconstrói a conta roadmin do zero (admin / GM 99).
# - Reconstrói todas as contas de teste do zero (classes, níveis, skills e inventários originais).
# - Regenera o mundo procedural completo a partir da base limpa.
# ==============================================================================

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# Cores
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
CYAN="\033[0;36m"
RED="\033[0;31m"
BOLD="\033[1m"
RESET="\033[0m"

echo -e "${CYAN}${BOLD}================================================================${RESET}"
echo -e "${CYAN}${BOLD}              RagnaRogue — Geração de Novo Mundo               ${RESET}"
echo -e "${CYAN}${BOLD}================================================================${RESET}"
echo

# 1. Determinar a Seed (Parâmetro ou Aleatória)
PARAM_SEED="${1:-}"

if [ -n "$PARAM_SEED" ] && [ "$PARAM_SEED" != "--force" ]; then
    SEED="$PARAM_SEED"
    echo -e "${GREEN}✓ Seed fornecida pelo usuário: ${BOLD}${SEED}${RESET}"
else
    echo -e "${YELLOW}--> Nenhuma seed informada. Gerando seed procedural aleatória...${RESET}"
    if [ -f "tools/generate_seed.py" ]; then
        SEED=$(python3 tools/generate_seed.py)
    else
        ADJ_LIST=("furioso" "sombrio" "veloz" "valente" "lendario" "mistico" "eterno" "flamejante" "congelante" "arcano")
        MOB_LIST=("poring" "lunatic" "deviruchi" "baphomet" "pecopeco" "poporing" "angeling" "ghostring" "orc-hero")
        RAND_ADJ=${ADJ_LIST[$RANDOM % ${#ADJ_LIST[@]}]}
        RAND_MOB=${MOB_LIST[$RANDOM % ${#MOB_LIST[@]}]}
        RAND_NUM=$((RANDOM % 9000 + 1000))
        SEED="${RAND_ADJ}-${RAND_MOB}-${RAND_NUM}"
    fi
    echo -e "${GREEN}✓ Nova seed gerada: ${BOLD}${SEED}${RESET}"
fi
echo

# 2. Validar pré-requisitos essenciais
for cmd in docker python3 sed cp rm; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo -e "${RED}[ERRO] Dependência obrigatória ausente: $cmd${RESET}"
        exit 1
    fi
done

for dir in data_base/db data_base/npc data_base/conf; do
    if [ ! -d "$dir" ]; then
        echo -e "${RED}[ERRO] Diretório base ausente: $dir. Execute make prepare primeiro.${RESET}"
        exit 1
    fi
done

# 3. Garantir que os containers de banco e painel estejam operacionais para reconstrução
echo -e "${YELLOW}--> Pausando servidores de jogo durante a reconstrução do mundo...${RESET}"
docker compose stop rathena robrowser >/dev/null 2>&1 || true

if ! docker compose ps db | grep -q "Up"; then
    echo -e "${CYAN}--> Inicializando MariaDB...${RESET}"
    docker compose up -d db
fi

# Aguardar DB responder
for i in {1..30}; do
    if docker exec ragnarok-db mysqladmin ping -u ragnarok -pragnarok --silent 2>/dev/null; then
        break
    fi
    sleep 1
done

# 4. Limpeza de personagens e dados de jogadores anteriores
echo -e "${CYAN}--> [1/4] Limpando dados de mundos e personagens antigos...${RESET}"
docker exec -i ragnarok-db mysql -u ragnarok -pragnarok ragnarok << 'EOSQL'
SET FOREIGN_KEY_CHECKS = 0;

-- Limpar todas as tabelas de estado do jogo anterior
TRUNCATE TABLE `inventory`;
TRUNCATE TABLE `cart_inventory`;
TRUNCATE TABLE `storage`;
TRUNCATE TABLE `skill`;
TRUNCATE TABLE `hotkey`;
TRUNCATE TABLE `memo`;
TRUNCATE TABLE `quest`;
TRUNCATE TABLE `achievement`;
TRUNCATE TABLE `bonus_script`;
TRUNCATE TABLE `sc_data`;
TRUNCATE TABLE `skillcooldown`;
TRUNCATE TABLE `char_reg_num`;
TRUNCATE TABLE `char_reg_str`;
TRUNCATE TABLE `acc_reg_num`;
TRUNCATE TABLE `acc_reg_str`;
TRUNCATE TABLE `global_acc_reg_num`;
TRUNCATE TABLE `global_acc_reg_str`;
TRUNCATE TABLE `elemental`;
TRUNCATE TABLE `homunculus`;
TRUNCATE TABLE `pet`;
TRUNCATE TABLE `mercenary`;
TRUNCATE TABLE `mercenary_owner`;
TRUNCATE TABLE `friends`;
TRUNCATE TABLE `mail`;
TRUNCATE TABLE `mail_attachments`;
TRUNCATE TABLE `auction`;
TRUNCATE TABLE `vendings`;
TRUNCATE TABLE `vending_items`;
TRUNCATE TABLE `buyingstores`;
TRUNCATE TABLE `buyingstore_items`;
TRUNCATE TABLE `guild_member`;
TRUNCATE TABLE `guild`;
TRUNCATE TABLE `party`;
TRUNCATE TABLE `event_speedruns`;
TRUNCATE TABLE `event_mvp_kills`;
TRUNCATE TABLE `run_goal_leaderboard`;
TRUNCATE TABLE `run_metadata`;
TRUNCATE TABLE `world_map_conquests`;
TRUNCATE TABLE `ragsrvinfo`;

-- Limpar todos os personagens anteriores
TRUNCATE TABLE `char`;

-- Limpar logins de jogadores comuns (mantendo apenas s1 para conexões internas)
DELETE FROM `login` WHERE account_id NOT IN (1);

SET FOREIGN_KEY_CHECKS = 1;
EOSQL

# Re-popular as 22 cidades capitais seguras e atualizar world_metadata com a nova seed real
docker exec ragnarok-db mysql -u ragnarok -pragnarok ragnarok -e "
INSERT INTO \`world_map_conquests\` (\`map_name\`, \`seed\`, \`conquered_by\`, \`conquered_at\`) VALUES
('prontera', '${SEED}', 'Sistema', NOW()),
('izlude', '${SEED}', 'Sistema', NOW()),
('geffen', '${SEED}', 'Sistema', NOW()),
('morocc', '${SEED}', 'Sistema', NOW()),
('payon', '${SEED}', 'Sistema', NOW()),
('alberta', '${SEED}', 'Sistema', NOW()),
('aldebaran', '${SEED}', 'Sistema', NOW()),
('comodo', '${SEED}', 'Sistema', NOW()),
('yuno', '${SEED}', 'Sistema', NOW()),
('amatsu', '${SEED}', 'Sistema', NOW()),
('gonryun', '${SEED}', 'Sistema', NOW()),
('umbala', '${SEED}', 'Sistema', NOW()),
('lighthalzen', '${SEED}', 'Sistema', NOW()),
('louyang', '${SEED}', 'Sistema', NOW()),
('ayothaya', '${SEED}', 'Sistema', NOW()),
('einbroch', '${SEED}', 'Sistema', NOW()),
('einbech', '${SEED}', 'Sistema', NOW()),
('hugel', '${SEED}', 'Sistema', NOW()),
('rachel', '${SEED}', 'Sistema', NOW()),
('veins', '${SEED}', 'Sistema', NOW()),
('lutie', '${SEED}', 'Sistema', NOW()),
('jawaii', '${SEED}', 'Sistema', NOW());

CREATE TABLE IF NOT EXISTS \`world_metadata\` (
    \`key\` VARCHAR(255) PRIMARY KEY,
    \`value\` TEXT NULL,
    \`created_at\` TIMESTAMP NULL,
    \`updated_at\` TIMESTAMP NULL
);
INSERT INTO \`world_metadata\` (\`key\`, \`value\`, \`updated_at\`) 
VALUES ('active_seed', '${SEED}', NOW())
ON DUPLICATE KEY UPDATE \`value\` = '${SEED}', \`updated_at\` = NOW();
"

# 5. Reconstruir roadmin do zero
echo -e "${CYAN}--> [2/4] Reconstruindo conta roadmin do zero...${RESET}"
docker exec -i ragnarok-db mysql -u ragnarok -pragnarok ragnarok << 'EOSQL'
INSERT INTO `login` (`account_id`, `userid`, `user_pass`, `sex`, `email`, `group_id`, `state`, `unban_time`, `expiration_time`, `logincount`, `lastlogin`, `last_ip`, `birthdate`, `character_slots`, `pincode`, `pincode_change`, `vip_time`, `old_group`)
VALUES (2000001, 'roadmin', 'roadmin', 'M', 'admin@ragnarogue.local', 99, 0, 0, 0, 0, NULL, '', '2000-01-01', 9, '', 0, 0, 0)
ON DUPLICATE KEY UPDATE `user_pass` = 'roadmin', `group_id` = 99, `email` = 'admin@ragnarogue.local';
EOSQL
echo -e "${GREEN}✓ Conta roadmin reconstruída com sucesso (Login: roadmin | Senha: roadmin | GM 99).${RESET}"

# 6. Reconstruir contas de teste do zero via painel Laravel
echo -e "${CYAN}--> [3/4] Reconstruindo contas de teste do zero (personagens, classes, skills e itens)...${RESET}"
if ! docker compose ps panel | grep -q "Up"; then
    docker compose up -d panel
    sleep 3
fi

docker exec ragnarok-panel php artisan tinker --execute="
\$m = require database_path('migrations/2026_09_23_000001_seed_test_accounts.php');
\$m->down();
\$m->up();
" >/dev/null 2>&1 || {
    echo -e "${YELLOW}[WARN] Falha ao rodar tinker no container panel. Executando fallback via migrações diretas...${RESET}"
    docker exec ragnarok-panel php artisan migrate --force || true
}
echo -e "${GREEN}✓ 14 Contas e personagens de teste reconstruídos do zero com itens e habilidades originais.${RESET}"

# 7. Regeneração procedural dos arquivos do novo mundo (data/)
echo -e "${CYAN}--> [4/4] Regenerando arquitetura do mundo com a nova Seed (${SEED})...${RESET}"
rm -rf data/db data/npc data/conf
cp -r data_base/db data/
cp -r data_base/npc data/
cp -r data_base/conf data/

mkdir -p data/db/import data/conf/import data/conf/msg_conf/import data/npc/custom
if [ -d "data_base/db/import-tmpl" ]; then
    cp -n data_base/db/import-tmpl/* data/db/import/ 2>/dev/null || true
fi
if [ -d "data_base/conf/import-tmpl" ]; then
    cp -n data_base/conf/import-tmpl/* data/conf/import/ 2>/dev/null || true
fi
if [ -d "data_base/conf/msg_conf/import-tmpl" ]; then
    cp -n data_base/conf/msg_conf/import-tmpl/* data/conf/msg_conf/import/ 2>/dev/null || true
fi

# Garantir arquivos essenciais para o sanity check e o rAthena
if [ -f "data_base/npc/custom/event_telemetry.txt" ]; then
    cp -f data_base/npc/custom/event_telemetry.txt data/npc/custom/
fi
if [ -f "data_base/npc/custom/starter_items.txt" ]; then
    cp -f data_base/npc/custom/starter_items.txt data/npc/custom/
fi
if [ -f "data_base/npc/custom/map_conquest.txt" ]; then
    cp -f data_base/npc/custom/map_conquest.txt data/npc/custom/
fi
if [ -f "data_base/npc/custom/comet_system.txt" ]; then
    cp -f data_base/npc/custom/comet_system.txt data/npc/custom/
fi
if [ -f "data_base/npc/custom/pray.txt" ]; then
    cp -f data_base/npc/custom/pray.txt data/npc/custom/
fi

# Configurar nova seed no .env.rando
sed -i "s/^WORLD_SEED=.*/WORLD_SEED=$SEED/" .env.rando

# Executar randomizer do mundo
bash scripts/randomize_world.sh

# 8. Reinicializar todos os serviços com o novo mundo
echo -e "${CYAN}--> Inicializando containers do jogo com o novo mundo...${RESET}"
docker compose up -d rathena robrowser panel

echo
echo -e "${GREEN}${BOLD}================================================================${RESET}"
echo -e "${GREEN}${BOLD}           NOVO MUNDO GERADO E RECONSTRUÍDO DO ZERO!           ${RESET}"
echo -e "${GREEN}${BOLD}================================================================${RESET}"
echo -e "  🌱 ${BOLD}Nova Seed Ativa:${RESET}      ${CYAN}${SEED}${RESET}"
echo -e "  👑 ${BOLD}Conta Admin:${RESET}          ${GREEN}roadmin / roadmin (GM Nível 99)${RESET}"
echo -e "  🧪 ${BOLD}Contas de Teste:${RESET}      ${GREEN}14 contas prontas (teste_swordie ... teste_extended / teste123)${RESET}"
echo -e "  🎮 ${BOLD}Cliente Web:${RESET}          ${GREEN}http://localhost:8001${RESET}"
echo -e "  🌐 ${BOLD}Painel de Controle:${RESET}   ${GREEN}http://localhost:8000${RESET}"
echo -e "${GREEN}${BOLD}================================================================${RESET}"

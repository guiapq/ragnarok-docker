#!/bin/bash
set -euo pipefail

# ==============================================================================
# Script 2: Zerar Mundo (RagnaRogue)
# - Apaga personagens que NÃO sejam de contas de teste e NÃO sejam admin.
# - Zera o estado do servidor (sessões, rankings transitórios, dados de jogo normais).
# - NÃO muda a seed procedural atual.
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
echo -e "${CYAN}${BOLD}             RagnaRogue — Zerar Mundo (Manter Seed)            ${RESET}"
echo -e "${CYAN}${BOLD}================================================================${RESET}"
echo

# 1. Obter a seed atual para confirmação
CURRENT_SEED="desconhecida"
if [ -f .env.rando ]; then
    CURRENT_SEED=$(grep "^WORLD_SEED=" .env.rando | cut -d '=' -f2 | tr -d ' "\r' || echo "desconhecida")
fi
echo -e "  🌱 ${BOLD}Seed Ativa (será preservada):${RESET} ${CYAN}${CURRENT_SEED}${RESET}"
echo

# 2. Verificar se o container do banco está rodando
if ! docker compose ps db | grep -q "Up"; then
    echo -e "${YELLOW}--> Inicializando container de banco de dados (ragnarok-db)...${RESET}"
    docker compose up -d db
    sleep 5
fi

# Aguardar DB ficar pronto para comandos
echo -e "${CYAN}--> Testando conexão com MariaDB...${RESET}"
for i in {1..30}; do
    if docker exec ragnarok-db mysqladmin ping -u ragnarok -pragnarok --silent 2>/dev/null; then
        break
    fi
    sleep 1
done

# 3. Parar rAthena e roBrowser temporariamente para evitar corrupção de memória ou cache
echo -e "${YELLOW}--> Pausando servidores de jogo (rathena, robrowser) para limpeza do mundo...${RESET}"
docker compose stop rathena robrowser >/dev/null 2>&1 || true

# 4. Listar personagens que serão removidos (auditoria visual)
CHARS_TO_DELETE=$(docker exec ragnarok-db mysql -u ragnarok -pragnarok ragnarok -N -s -e "
SELECT CONCAT('Char ID: ', char_id, ' | Nome: ', name, ' | Conta: ', account_id)
FROM \`char\`
WHERE account_id NOT IN (1, 2000001)
  AND account_id NOT BETWEEN 2000010 AND 2000022
  AND account_id NOT IN (
      SELECT account_id FROM \`login\`
      WHERE group_id IN (6, 99)
         OR userid IN ('roadmin', 'admin')
         OR userid LIKE 'teste%'
  );
" 2>/dev/null || true)

COUNT_CHARS=$(docker exec ragnarok-db mysql -u ragnarok -pragnarok ragnarok -N -s -e "
SELECT COUNT(*)
FROM \`char\`
WHERE account_id NOT IN (1, 2000001)
  AND account_id NOT BETWEEN 2000010 AND 2000022
  AND account_id NOT IN (
      SELECT account_id FROM \`login\`
      WHERE group_id IN (6, 99)
         OR userid IN ('roadmin', 'admin')
         OR userid LIKE 'teste%'
  );
" 2>/dev/null || echo 0)

if [ "$COUNT_CHARS" -gt 0 ]; then
    echo -e "${YELLOW}--> Personagens não-teste e não-admin identificados para remoção (${COUNT_CHARS}):${RESET}"
    echo "$CHARS_TO_DELETE"
else
    echo -e "${GREEN}✓ Nenhum personagem de jogador comum encontrado para remoção.${RESET}"
fi

# 5. Executar limpeza relacional atômica no banco de dados
echo -e "${CYAN}--> Executando expurgo de dados de personagens não-teste e não-admin...${RESET}"

docker exec -i ragnarok-db mysql -u ragnarok -pragnarok ragnarok << 'EOSQL'
SET FOREIGN_KEY_CHECKS = 0;

-- 1. Criar tabela temporária com as contas de teste e admin protegidas
CREATE TEMPORARY TABLE temp_protected_accounts (
    account_id INT PRIMARY KEY
);

INSERT IGNORE INTO temp_protected_accounts (account_id)
SELECT account_id FROM `login`
WHERE account_id = 1
   OR account_id = 2000001
   OR account_id BETWEEN 2000010 AND 2000022
   OR group_id IN (6, 99)
   OR userid IN ('roadmin', 'admin')
   OR userid LIKE 'teste%';

-- Garantir pelo menos IDs fixos conhecidos
INSERT IGNORE INTO temp_protected_accounts (account_id) VALUES (1), (2000001);
INSERT IGNORE INTO temp_protected_accounts (account_id)
SELECT 2000010 UNION SELECT 2000011 UNION SELECT 2000012 UNION SELECT 2000013
UNION SELECT 2000014 UNION SELECT 2000015 UNION SELECT 2000016 UNION SELECT 2000017
UNION SELECT 2000018 UNION SELECT 2000019 UNION SELECT 2000020 UNION SELECT 2000021
UNION SELECT 2000022;

-- 2. Identificar char_ids que serão removidos
CREATE TEMPORARY TABLE temp_chars_to_delete (
    char_id INT PRIMARY KEY,
    account_id INT
);

INSERT INTO temp_chars_to_delete (char_id, account_id)
SELECT char_id, account_id FROM `char`
WHERE account_id NOT IN (SELECT account_id FROM temp_protected_accounts);

-- 3. Remover registros vinculados a esses char_ids
DELETE FROM `inventory` WHERE char_id IN (SELECT char_id FROM temp_chars_to_delete);
DELETE FROM `cart_inventory` WHERE char_id IN (SELECT char_id FROM temp_chars_to_delete);
DELETE FROM `skill` WHERE char_id IN (SELECT char_id FROM temp_chars_to_delete);
DELETE FROM `hotkey` WHERE char_id IN (SELECT char_id FROM temp_chars_to_delete);
DELETE FROM `memo` WHERE char_id IN (SELECT char_id FROM temp_chars_to_delete);
DELETE FROM `quest` WHERE char_id IN (SELECT char_id FROM temp_chars_to_delete);
DELETE FROM `achievement` WHERE char_id IN (SELECT char_id FROM temp_chars_to_delete);
DELETE FROM `bonus_script` WHERE char_id IN (SELECT char_id FROM temp_chars_to_delete);
DELETE FROM `sc_data` WHERE char_id IN (SELECT char_id FROM temp_chars_to_delete);
DELETE FROM `skillcooldown` WHERE char_id IN (SELECT char_id FROM temp_chars_to_delete);
DELETE FROM `char_reg_num` WHERE char_id IN (SELECT char_id FROM temp_chars_to_delete);
DELETE FROM `char_reg_str` WHERE char_id IN (SELECT char_id FROM temp_chars_to_delete);
DELETE FROM `elemental` WHERE char_id IN (SELECT char_id FROM temp_chars_to_delete);
DELETE FROM `homunculus` WHERE char_id IN (SELECT char_id FROM temp_chars_to_delete);
DELETE FROM `pet` WHERE char_id IN (SELECT char_id FROM temp_chars_to_delete);
DELETE FROM `mercenary` WHERE char_id IN (SELECT char_id FROM temp_chars_to_delete);
DELETE FROM `mercenary_owner` WHERE char_id IN (SELECT char_id FROM temp_chars_to_delete);
DELETE FROM `friends` WHERE char_id IN (SELECT char_id FROM temp_chars_to_delete)
                         OR friend_account NOT IN (SELECT account_id FROM temp_protected_accounts);

DELETE FROM `vending_items` WHERE vending_id IN (SELECT vending_id FROM `vendings` WHERE char_id IN (SELECT char_id FROM temp_chars_to_delete));
DELETE FROM `vendings` WHERE char_id IN (SELECT char_id FROM temp_chars_to_delete);
DELETE FROM `buyingstore_items` WHERE buyingstore_id IN (SELECT buyingstore_id FROM `buyingstores` WHERE char_id IN (SELECT char_id FROM temp_chars_to_delete));
DELETE FROM `buyingstores` WHERE char_id IN (SELECT char_id FROM temp_chars_to_delete);

-- Limpar mensagens e leilões
DELETE FROM `mail_attachments` WHERE id IN (SELECT id FROM `mail` WHERE send_id IN (SELECT char_id FROM temp_chars_to_delete) OR dest_id IN (SELECT char_id FROM temp_chars_to_delete));
DELETE FROM `mail` WHERE send_id IN (SELECT char_id FROM temp_chars_to_delete)
                      OR dest_id IN (SELECT char_id FROM temp_chars_to_delete);
DELETE FROM `auction` WHERE seller_id IN (SELECT char_id FROM temp_chars_to_delete)
                         OR buyer_id IN (SELECT char_id FROM temp_chars_to_delete);

-- Limpar guildas e parties de contas deletadas
DELETE FROM `guild_member` WHERE char_id IN (SELECT char_id FROM temp_chars_to_delete);
DELETE FROM `guild` WHERE char_id IN (SELECT char_id FROM temp_chars_to_delete);
DELETE FROM `party` WHERE leader_char IN (SELECT char_id FROM temp_chars_to_delete);

-- Limpar eventos e telemetrias desses chars
DELETE FROM `event_speedruns` WHERE char_id IN (SELECT char_id FROM temp_chars_to_delete);
DELETE FROM `event_mvp_kills` WHERE char_id IN (SELECT char_id FROM temp_chars_to_delete);

-- 4. Excluir os personagens da tabela char
DELETE FROM `char` WHERE char_id IN (SELECT char_id FROM temp_chars_to_delete);

-- 5. Excluir dados de conta e logins não-protegidos
DELETE FROM `storage` WHERE account_id NOT IN (SELECT account_id FROM temp_protected_accounts);
DELETE FROM `acc_reg_num` WHERE account_id NOT IN (SELECT account_id FROM temp_protected_accounts);
DELETE FROM `acc_reg_str` WHERE account_id NOT IN (SELECT account_id FROM temp_protected_accounts);
DELETE FROM `global_acc_reg_num` WHERE account_id NOT IN (SELECT account_id FROM temp_protected_accounts);
DELETE FROM `global_acc_reg_str` WHERE account_id NOT IN (SELECT account_id FROM temp_protected_accounts);
DELETE FROM `login` WHERE account_id NOT IN (SELECT account_id FROM temp_protected_accounts);

-- 6. Zerar o servidor: resetar status online e sessões
UPDATE `char` SET `online` = 0;
TRUNCATE TABLE `ragsrvinfo`;

SET FOREIGN_KEY_CHECKS = 1;
EOSQL

# Limpar sessões ativas do Laravel se existir
docker exec ragnarok-db mysql -u ragnarok -pragnarok ragnarok -e "
DELETE FROM \`sessions\` 
WHERE user_id NOT IN (SELECT account_id FROM \`login\` WHERE group_id = 99);
" 2>/dev/null || true

# 6. Reiniciar serviços do servidor
echo -e "${CYAN}--> Reiniciando rAthena e roBrowser com mundo zerado...${RESET}"
docker compose up -d rathena robrowser

# 7. Validar integridade da Seed
POST_SEED=$(grep "^WORLD_SEED=" .env.rando | cut -d '=' -f2 | tr -d ' "\r' || echo "desconhecida")

echo
echo -e "${GREEN}${BOLD}================================================================${RESET}"
echo -e "${GREEN}${BOLD}           MUNDO ZERADO COM SUCESSO!                           ${RESET}"
echo -e "${GREEN}${BOLD}================================================================${RESET}"
echo -e "  🌱 ${BOLD}Seed Mantida:${RESET}           ${CYAN}${POST_SEED}${RESET}"
echo -e "  🛡️  ${BOLD}Contas de Teste/Admin:${RESET} ${GREEN}Preservadas (roadmin e teste_* intactos)${RESET}"
echo -e "  🗑️  ${BOLD}Chars Normais Removidos:${RESET}${YELLOW} ${COUNT_CHARS} personagem(ns)${RESET}"
echo -e "  🔄 ${BOLD}Status do Servidor:${RESET}     ${GREEN}Zerado e pronto para novas conexões${RESET}"
echo -e "${GREEN}${BOLD}================================================================${RESET}"

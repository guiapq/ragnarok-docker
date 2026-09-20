#!/bin/bash
set -e

echo "=== Configurando rAthena nativo ==="

CONF_DIR="/opt/rathena/conf"
cd $CONF_DIR

RO_IP="${RO_IP:-127.0.0.1}"
DB_HOST="${RATHENA_DB_HOST:-db}"
DB_PORT="${RATHENA_DB_PORT:-3306}"
DB_USER="${MYSQL_USER:-ragnarok}"
DB_PASS="${MYSQL_PASSWORD:-ragnarok}"
DB_NAME="${MYSQL_DATABASE:-ragnarok}"

echo "RO_IP: ${RO_IP}"
echo "DB_HOST: ${DB_HOST}"

# Ajuste de IPs nos confs (suportando linhas comentadas e descomentadas)
sed -i "s|^\(//\)\?login_ip:.*|login_ip: 127.0.0.1|" char_athena.conf
sed -i "s|^\(//\)\?char_ip:.*|char_ip: ${RO_IP}|" char_athena.conf
sed -i "s|^\(//\)\?bind_ip:.*|bind_ip: 0.0.0.0|" char_athena.conf

sed -i "s|^\(//\)\?char_ip:.*|char_ip: 127.0.0.1|" map_athena.conf
sed -i "s|^\(//\)\?map_ip:.*|map_ip: ${RO_IP}|" map_athena.conf
sed -i "s|^\(//\)\?bind_ip:.*|bind_ip: 0.0.0.0|" map_athena.conf

# Configurações de banco no inter_athena.conf (formato rAthena inter_athena.conf)
for prefix in login_server ipban_db char_server map_server log_db; do
    sed -i "s|^${prefix}_ip:.*|${prefix}_ip: ${DB_HOST}|" inter_athena.conf || true
    sed -i "s|^${prefix}_port:.*|${prefix}_port: ${DB_PORT}|" inter_athena.conf || true
    sed -i "s|^${prefix}_id:.*|${prefix}_id: ${DB_USER}|" inter_athena.conf || true
    sed -i "s|^${prefix}_pw:.*|${prefix}_pw: ${DB_PASS}|" inter_athena.conf || true
    sed -i "s|^${prefix}_db:.*|${prefix}_db: ${DB_NAME}|" inter_athena.conf || true
done

# Compatibilidade caso use sintaxe sql.db_*
sed -i "s/sql.db_hostname:.*/sql.db_hostname: ${DB_HOST}/g" inter_athena.conf 2>/dev/null || true
sed -i "s/sql.db_port:.*/sql.db_port: ${DB_PORT}/g" inter_athena.conf 2>/dev/null || true
sed -i "s/sql.db_username:.*/sql.db_username: ${DB_USER}/g" inter_athena.conf 2>/dev/null || true
sed -i "s/sql.db_password:.*/sql.db_password: ${DB_PASS}/g" inter_athena.conf 2>/dev/null || true
sed -i "s/sql.db_name:.*/sql.db_name: ${DB_NAME}/g" inter_athena.conf 2>/dev/null || true

# Aguardar DB ficar online
echo "=== Aguardando banco de dados (${DB_HOST}:${DB_PORT}) ==="
until mysqladmin ping -h "$DB_HOST" -P "$DB_PORT" -u"$DB_USER" -p"$DB_PASS" --silent; do
    echo "Aguardando conexão com MariaDB..."
    sleep 2
done
echo "=== Banco de dados conectado com sucesso ==="

# Auto-inicialização de tabelas caso o banco esteja limpo
TABLE_COUNT=$(mysql -h "$DB_HOST" -P "$DB_PORT" -u"$DB_USER" -p"$DB_PASS" -D "$DB_NAME" -sse "SELECT count(*) FROM information_schema.tables WHERE table_schema='${DB_NAME}' AND table_name='login';" 2>/dev/null || echo 0)

if [ "$TABLE_COUNT" -eq 0 ]; then
    echo "=== Tabelas do rAthena ausentes. Executando importação automática (main.sql + logs.sql)... ==="
    if [ -f /opt/rathena/sql-files/main.sql ]; then
        mysql -h "$DB_HOST" -P "$DB_PORT" -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" < /opt/rathena/sql-files/main.sql
        echo "[OK] main.sql importado"
    fi
    if [ -f /opt/rathena/sql-files/logs.sql ]; then
        mysql -h "$DB_HOST" -P "$DB_PORT" -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" < /opt/rathena/sql-files/logs.sql
        echo "[OK] logs.sql importado"
    fi
    if [ -f /opt/rathena/sql-files/item_cash_db.sql ]; then
        mysql -h "$DB_HOST" -P "$DB_PORT" -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" < /opt/rathena/sql-files/item_cash_db.sql 2>/dev/null || true
    fi
    echo "=== Importação inicial concluída ==="
fi

# 1. Garantir tabelas de telemetria de torneios (Speedrun 99 e MVP Bounty)
echo "=== Verificando tabelas de torneio (event_speedruns, event_mvp_kills) ==="
mysql -h "$DB_HOST" -P "$DB_PORT" -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" -e "
CREATE TABLE IF NOT EXISTS event_speedruns (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    char_id INT UNSIGNED NOT NULL UNIQUE,
    name VARCHAR(30) NOT NULL,
    class SMALLINT UNSIGNED NOT NULL,
    base_level INT UNSIGNED NOT NULL DEFAULT 99,
    job_level INT UNSIGNED NOT NULL DEFAULT 50,
    total_seconds INT UNSIGNED NOT NULL,
    achieved_at DATETIME NOT NULL,
    created_at TIMESTAMP NULL,
    updated_at TIMESTAMP NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS event_mvp_kills (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    char_id INT UNSIGNED NOT NULL,
    char_name VARCHAR(30) NOT NULL,
    mob_id INT UNSIGNED NOT NULL,
    mob_name VARCHAR(50) NOT NULL,
    killed_at DATETIME NOT NULL,
    created_at TIMESTAMP NULL,
    updated_at TIMESTAMP NULL,
    INDEX idx_char_id (char_id),
    INDEX idx_mob_id (mob_id),
    INDEX idx_killed_at (killed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
" 2>/dev/null || true

# Garantir compatibilidade do schema da tabela char
mysql -h "$DB_HOST" -P "$DB_PORT" -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" -e "ALTER TABLE \`char\` MODIFY \`settings\` text NOT NULL DEFAULT '';" 2>/dev/null || true

# Limpar sessões fantasmas/travadas no boot
echo "=== Limpando status de sessões anteriores ==="
mysql -h "$DB_HOST" -P "$DB_PORT" -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" -e "UPDATE \`char\` SET \`online\` = 0;" 2>/dev/null || true

# 2. Provisionar conta de Administrador GM fixa (roadmin, roadmin)
echo "=== Provisionando conta de Administrador GM fixa (roadmin) ==="
mysql -h "$DB_HOST" -P "$DB_PORT" -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" -e "
INSERT INTO \`login\` (\`account_id\`, \`userid\`, \`user_pass\`, \`sex\`, \`email\`, \`group_id\`, \`birthdate\`, \`character_slots\`)
VALUES (2000001, 'roadmin', 'roadmin', 'M', 'admin@ragnarogue.local', 99, '2000-01-01', 9)
ON DUPLICATE KEY UPDATE \`user_pass\` = 'roadmin', \`group_id\` = 99;
" 2>/dev/null || true

# 3. Aplicar automaticamente o modo CASUAL / Roguelike antes de iniciar os servidores
echo "=== Aplicando modo CASUAL / Roguelike automaticamente ==="
if [ -f /casual.sh ]; then
    bash /casual.sh --apply-only
fi

# 3b. Provisionar contas de teste (apenas na primeira vez — idempotente)
echo "=== Provisionando contas de teste (seeder) ==="
if [ -f /seeder.sh ]; then
    bash /seeder.sh 2>&1 | grep -E "=== |→ |✓|criado|ok|Seeder" || true
fi

# 4. Arquivo de credenciais de recuperação rápida
cat <<EOF > /opt/rathena/CREDENTIALS.txt
=====================================================
RAGNAROGUE - CREDENCIAIS DO SISTEMA E RECUPERAÇÃO
=====================================================
Conta Administrador GM (In-game & Painel Web):
  Usuário: roadmin
  Senha:   roadmin
  Nível:   99 (Acesso total / GM @commands / Painel /admin)

Banco de Dados MariaDB (Host: ${DB_HOST}:${DB_PORT}):
  Database:      ${DB_NAME}
  Usuário App:   ${DB_USER}
  Senha App:     ${DB_PASS}
  Root Password: ${MYSQL_ROOT_PASSWORD:-root}
=====================================================
EOF

echo "=== Iniciando rAthena ==="
cd /opt/rathena

# Criação de logs caso ainda não existam para o tail
mkdir -p /opt/rathena/log
touch /opt/rathena/log/map-server.log /opt/rathena/log/char-server.log /opt/rathena/log/login-server.log

# Inicia servidores
./athena-start start 1 || ./athena-start start || true

echo "=== rAthena iniciado com sucesso (Modo CASUAL ativo) ==="
sleep 2

echo "=== Exibindo logs em tempo real ==="
exec tail -f /opt/rathena/log/map-server.log /opt/rathena/log/char-server.log /opt/rathena/log/login-server.log

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

echo "=== Iniciando rAthena ==="
cd /opt/rathena

# Criação de logs caso ainda não existam para o tail
mkdir -p /opt/rathena/log
touch /opt/rathena/log/map-server.log /opt/rathena/log/char-server.log /opt/rathena/log/login-server.log

# Inicia servidores
./athena-start start 1 || ./athena-start start || true

echo "=== rAthena iniciado ==="
sleep 2

echo "=== Exibindo logs em tempo real ==="
exec tail -f /opt/rathena/log/map-server.log /opt/rathena/log/char-server.log /opt/rathena/log/login-server.log

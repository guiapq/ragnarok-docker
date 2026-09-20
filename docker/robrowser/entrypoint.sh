#!/bin/bash
set -e

echo "=== Iniciando container roBrowser ==="
cd /opt/roBrowserLegacy

# 1. Garantir link simbólico /client para compatibilidade com FileManager.getHTTP
if [ ! -L /opt/roBrowserLegacy/client ]; then
    rm -rf /opt/roBrowserLegacy/client 2>/dev/null || true
    ln -s . /opt/roBrowserLegacy/client
fi

# 2. Pipeline dinâmica de sincronização do itemInfo.lua
if [ -f /opt/tools/generate_item_info_lua.py ]; then
    ITEM_DB_FOUND=""
    if [ -f "/opt/roBrowserLegacy/data/db/pre-re/item_db.txt" ]; then
        ITEM_DB_FOUND="/opt/roBrowserLegacy/data/db/pre-re/item_db.txt"
        RATHENA_DIR="/opt/roBrowserLegacy/data"
    elif [ -f "/opt/rathena/db/pre-re/item_db.txt" ]; then
        ITEM_DB_FOUND="/opt/rathena/db/pre-re/item_db.txt"
        RATHENA_DIR="/opt/rathena"
    fi

    if [ -n "$ITEM_DB_FOUND" ]; then
        echo "=== [Pipeline roBrowser] Gerando System/itemInfo.lua a partir de $ITEM_DB_FOUND ==="
        RATHENA_ROOT="$RATHENA_DIR" \
        OUTPUT_ITEM_INFO="/opt/roBrowserLegacy/System/itemInfo.lua" \
        python3 /opt/tools/generate_item_info_lua.py || echo "[AVISO] Falha ao gerar itemInfo.lua dinamicamente, mantendo versão existente."
    fi
fi

# 3. Aplicar patches no bundle compilado Online.js
if [ -f /opt/patch_online.js ]; then
    echo "=== [Pipeline roBrowser] Aplicando patches no Online.js ==="
    node /opt/patch_online.js /opt/roBrowserLegacy/Online.js || true
fi

# 4. Gerar Config.local.js a partir do template com variáveis de ambiente
export RO_REMOTE_CLIENT="${RO_REMOTE_CLIENT:-}"
if [ -f /opt/Config.local.template.js ]; then
    envsubst < /opt/Config.local.template.js > Config.local.js
fi

# 5. Iniciar serviços de rede
echo "=== [roBrowser] Iniciando wsproxy e http-server (Porta 8080 / WS 5999) ==="
wsproxy -a ragnarok-server:6900,ragnarok-server:6121,ragnarok-server:5121 &

exec http-server -p 8080 -a 0.0.0.0 --cors -c-1

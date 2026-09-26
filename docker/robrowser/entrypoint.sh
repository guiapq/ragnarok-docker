#!/bin/bash
set -e

echo "=== Iniciando container roBrowser ==="
cd /opt/roBrowserLegacy

# 1. Garantir link simbólico /client para compatibilidade com FileManager.getHTTP
if [ ! -L /opt/roBrowserLegacy/client ]; then
    rm -rf /opt/roBrowserLegacy/client 2>/dev/null || true
    ln -s . /opt/roBrowserLegacy/client
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

FROM node:22-bookworm-slim

WORKDIR /opt

RUN echo "options timeout:2 attempts:2" >> /etc/resolv.conf 2>/dev/null || true

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    bash \
    nano \
    curl \
    gettext-base \
    python3 \
    && rm -rf /var/lib/apt/lists/*

RUN timeout 180 npm install -g wsproxy http-server

# baixar cliente web do fork com commit travado (suporta git local LAN)
ARG ROBROWSER_REPO=https://github.com/guiapq/roBrowserLegacy.git
ARG ROBROWSER_COMMIT=1433244
RUN git config --global http.lowSpeedLimit 1000 \
    && git config --global http.lowSpeedTime 30 \
    && timeout 300 git clone ${ROBROWSER_REPO} /opt/roBrowserLegacy \
    && cd /opt/roBrowserLegacy \
    && git checkout ${ROBROWSER_COMMIT}

WORKDIR /opt/roBrowserLegacy

# evitar download de binários desktop desnecessários (Electron 120MB)
ENV ELECTRON_SKIP_BINARY_DOWNLOAD=1

# remover dependências desnecessárias de desktop (Electron) e instalar dependências do bundler web
RUN npm pkg delete devDependencies.electron devDependencies.electron-builder 2>/dev/null || true \
    && timeout 180 npm install --legacy-peer-deps

# build
RUN timeout 300 npm run build -- -O -T -H

# copiar build final
RUN cp -r dist/Web/* .

# link retrocompatibilidade para FileManager.getHTTP (/client/...)
RUN ln -sf . /opt/roBrowserLegacy/client

# copiar template, patcher e entrypoint
COPY Config.local.template.js /opt/Config.local.template.js
COPY patch_online.js /opt/patch_online.js
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8080 5999

CMD ["/entrypoint.sh"]


FROM alpine:3.19

WORKDIR /opt

RUN echo "options timeout:2 attempts:2" >> /etc/resolv.conf 2>/dev/null || true

RUN timeout 240 apk add --no-cache \
    git \
    nodejs \
    npm \
    bash \
    nano \
    curl \
    gettext

RUN timeout 180 npm install -g wsproxy http-server

# baixar cliente web do fork com commit travado (suporta git local LAN)
ARG ROBROWSER_REPO=https://github.com/guiapq/roBrowserLegacy.git
ARG ROBROWSER_COMMIT=fd9183f
RUN git config --global http.lowSpeedLimit 1000 \
    && git config --global http.lowSpeedTime 30 \
    && timeout 300 git clone ${ROBROWSER_REPO} /opt/roBrowserLegacy \
    && cd /opt/roBrowserLegacy \
    && git checkout ${ROBROWSER_COMMIT}

WORKDIR /opt/roBrowserLegacy

# instalar dependências
RUN timeout 600 npm install

# build
RUN timeout 300 npm run build -- -O -T -H

# copiar build final
RUN cp -r dist/Web/* .

# copiar template
COPY Config.local.template.js /opt/Config.local.template.js

EXPOSE 8080 5999

CMD bash -c "cd /opt/roBrowserLegacy && export RO_REMOTE_CLIENT=\"\${RO_REMOTE_CLIENT:-}\" && envsubst < /opt/Config.local.template.js > Config.local.js && wsproxy -a ragnarok-server:6900,ragnarok-server:6121,ragnarok-server:5121 & http-server -p 8080 -a 0.0.0.0 --cors -c-1"


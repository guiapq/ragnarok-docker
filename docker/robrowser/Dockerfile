FROM alpine:3.19

WORKDIR /opt

RUN apk add --no-cache \
    git \
    nodejs \
    npm \
    bash \
    nano \
    curl \
    gettext

RUN npm install -g wsproxy http-server

# baixar robrowser do fork com commit travado (suporta git local LAN)
ARG ROBROWSER_REPO=https://github.com/guiapq/roBrowserLegacy.git
ARG ROBROWSER_COMMIT=fd9183f
RUN git clone ${ROBROWSER_REPO} /opt/roBrowserLegacy \
    && cd /opt/roBrowserLegacy \
    && git checkout ${ROBROWSER_COMMIT}

WORKDIR /opt/roBrowserLegacy

# instalar dependências
RUN npm install

# build
RUN npm run build -- -O -T -H

# copiar build final
RUN cp -r dist/Web/* .

# copiar template
COPY Config.local.template.js /opt/Config.local.template.js

EXPOSE 8080 5999

CMD bash -c "cd /opt/roBrowserLegacy && export RO_REMOTE_CLIENT=\"\${RO_REMOTE_CLIENT:-}\" && envsubst < /opt/Config.local.template.js > Config.local.js && wsproxy -a ragnarok-server:6900,ragnarok-server:6121,ragnarok-server:5121 & http-server -p 8080 -a 0.0.0.0 --cors -c-1"


# ==========================================
# STAGE 1: Builder
# ==========================================
FROM debian:bookworm-slim AS builder

ARG RATHENA_REPO=https://github.com/guiapq/rathena.git
ARG RATHENA_COMMIT=ac46920e73819662811573253d9b22592e8ad985
ARG RO_PACKETVER=20151104

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    make \
    git \
    ca-certificates \
    default-libmysqlclient-dev \
    libpcre3-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

RUN git clone ${RATHENA_REPO} rathena \
    && cd rathena \
    && git checkout ${RATHENA_COMMIT}

WORKDIR /build/rathena

RUN ./configure --enable-packetver=${RO_PACKETVER} --enable-vip=no --enable-prere=no --enable-renewal=yes \
    && make clean \
    && make server

# ==========================================
# STAGE 2: Runtime
# ==========================================
FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV LANGUAGE=C.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends \
    default-mysql-client \
    libmariadb3 \
    libpcre3 \
    zlib1g \
    ca-certificates \
    python3 \
    bash \
    curl \
    iproute2 \
    procps \
    nano \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/rathena

# Copiar executáveis e diretórios essenciais do builder
COPY --from=builder /build/rathena/login-server /opt/rathena/login-server
COPY --from=builder /build/rathena/char-server /opt/rathena/char-server
COPY --from=builder /build/rathena/map-server /opt/rathena/map-server
COPY --from=builder /build/rathena/athena-start /opt/rathena/athena-start
COPY --from=builder /build/rathena/conf /opt/rathena/conf
COPY --from=builder /build/rathena/db /opt/rathena/db
COPY --from=builder /build/rathena/npc /opt/rathena/npc
COPY --from=builder /build/rathena/sql-files /opt/rathena/sql-files

# Criar pasta de logs e compatibilidade com caminhos legados (/usr/bin/rathena)
RUN mkdir -p /opt/rathena/log && \
    mkdir -p /usr/bin && \
    ln -s /opt/rathena /usr/bin/rathena

# Copiar scripts utilitários
COPY docker/rathena/start.sh /start.sh
COPY docker/rathena/casual.sh /casual.sh
COPY docker/rathena/analyzer.sh /analyzer.sh
COPY docker/rathena/cat_python.py /cat_python.py
COPY docker/rathena/build_ro_database.py /build_ro_database.py

RUN chmod +x /start.sh /casual.sh /analyzer.sh /cat_python.py /build_ro_database.py /opt/rathena/athena-start

EXPOSE 6900 6121 5121

CMD ["/start.sh"]

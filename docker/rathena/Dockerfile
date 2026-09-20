# ==========================================
# STAGE 1: Builder
# ==========================================
FROM debian:bookworm-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive

RUN echo 'Acquire::http::Timeout "15";' > /etc/apt/apt.conf.d/99timeout && \
    echo 'Acquire::ftp::Timeout "15";' >> /etc/apt/apt.conf.d/99timeout && \
    echo 'Acquire::Retries "2";' >> /etc/apt/apt.conf.d/99timeout && \
    echo "options timeout:2 attempts:2" >> /etc/resolv.conf 2>/dev/null || true

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    timeout 300 apt-get update && timeout 600 apt-get install -y --no-install-recommends \
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

ARG RATHENA_REPO=https://github.com/guiapq/rathena.git
ARG RATHENA_COMMIT=ac46920e73819662811573253d9b22592e8ad985
ARG RO_PACKETVER=20151104

WORKDIR /build

RUN git config --global http.lowSpeedLimit 1000 \
    && git config --global http.lowSpeedTime 30 \
    && timeout 300 git clone ${RATHENA_REPO} rathena \
    && cd rathena \
    && git checkout ${RATHENA_COMMIT}

WORKDIR /build/rathena

ARG BUILD_JOBS=""

RUN NPROC=${BUILD_JOBS:-$(nproc 2>/dev/null || getconf _NPROCESSORS_ONLN || echo 4)} \
    && export MAKEFLAGS="-j${NPROC}" \
    && echo "=== Compilando rAthena utilizando ${NPROC} threads ===" \
    && ./configure --enable-packetver=${RO_PACKETVER} --enable-vip=no --enable-prere=yes \
    && make clean \
    && make -j"${NPROC}" server

# ==========================================
# STAGE 2: Runtime
# ==========================================
FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV LANGUAGE=C.UTF-8

# Credenciais padrão e chaves de segurança da base (recuperação de acesso)
ENV DEFAULT_DB_ROOT_PASS="rR_SecRoot#2026_9f7b3a"
ENV DEFAULT_DB_USER="ragnarok"
ENV DEFAULT_DB_PASS="rR_SecApp#2026_8e6d2c"
ENV FIXED_ADMIN_USER="roadmin"
ENV FIXED_ADMIN_PASS="roadmin"
ENV FIXED_ADMIN_GROUP=99

RUN echo 'Acquire::http::Timeout "15";' > /etc/apt/apt.conf.d/99timeout && \
    echo 'Acquire::ftp::Timeout "15";' >> /etc/apt/apt.conf.d/99timeout && \
    echo 'Acquire::Retries "2";' >> /etc/apt/apt.conf.d/99timeout && \
    echo "options timeout:2 attempts:2" >> /etc/resolv.conf 2>/dev/null || true

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    timeout 300 apt-get update && timeout 600 apt-get install -y --no-install-recommends \
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
COPY --from=builder /build/rathena/function.sh /opt/rathena/function.sh
COPY --from=builder /build/rathena/conf /opt/rathena/conf
COPY --from=builder /build/rathena/conf /opt/rathena/conf.default
COPY --from=builder /build/rathena/db /opt/rathena/db
COPY --from=builder /build/rathena/db /opt/rathena/db.default
COPY --from=builder /build/rathena/npc /opt/rathena/npc
COPY --from=builder /build/rathena/npc /opt/rathena/npc.default
COPY --from=builder /build/rathena/sql-files /opt/rathena/sql-files

# Criar pasta de logs e compatibilidade com caminhos legados (/usr/bin/rathena e /datastoresetup)
RUN mkdir -p /opt/rathena/log && \
    mkdir -p /usr/bin && \
    ln -s /opt/rathena /usr/bin/rathena && \
    mkdir -p /datastoresetup && \
    ln -s /opt/rathena /datastoresetup/usr-bin-rathena

# Copiar scripts utilitários
COPY docker/rathena/start.sh /start.sh
COPY docker/rathena/casual.sh /casual.sh
COPY docker/rathena/seeder.sh /seeder.sh
COPY docker/rathena/analyzer.sh /analyzer.sh
COPY docker/rathena/cat_python.py /cat_python.py
COPY docker/rathena/build_ro_database.py /build_ro_database.py

RUN ln -sf /start.sh /launch-athena.sh && \
    chmod +x /start.sh /casual.sh /seeder.sh /analyzer.sh /cat_python.py /build_ro_database.py /opt/rathena/athena-start /opt/rathena/function.sh

EXPOSE 6900 6121 5121

CMD ["/start.sh"]

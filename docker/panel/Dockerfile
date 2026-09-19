FROM php:8.2-cli-alpine

# Dependências básicas do sistema
RUN echo "options timeout:2 attempts:2" >> /etc/resolv.conf 2>/dev/null || true

RUN timeout 240 apk add --no-cache \
    bash \
    curl \
    git \
    unzip \
    libzip-dev \
    icu-dev \
    libpng-dev \
    mysql-client

# Instalador de extensões PHP de alta performance
ADD --chmod=0755 https://github.com/mlocati/docker-php-extension-installer/releases/latest/download/install-php-extensions /usr/local/bin/

RUN timeout 600 install-php-extensions \
    pdo_mysql \
    bcmath \
    intl \
    zip \
    gd \
    opcache \
    pcntl

# Copiar Composer oficial
COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

WORKDIR /var/www/html

# Credenciais padrão e chaves de segurança da base (recuperação de acesso)
ENV DEFAULT_DB_ROOT_PASS="rR_SecRoot#2026_9f7b3a"
ENV DEFAULT_DB_USER="ragnarok"
ENV DEFAULT_DB_PASS="rR_SecApp#2026_8e6d2c"

COPY docker/panel/start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 8000

CMD ["/start.sh"]

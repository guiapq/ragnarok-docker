#!/bin/bash
set -e

cd /var/www/html

echo "=== Ragnarok Web Panel: Inicializando ==="

# Permissões do Laravel
mkdir -p storage/framework/{sessions,views,cache} storage/logs bootstrap/cache
chmod -R 775 storage bootstrap/cache 2>/dev/null || true

# Instalação das dependências
if [ ! -d "vendor" ]; then
    echo "Instalando dependências do Composer (Laravel + Filament)..."
    composer install --no-interaction --prefer-dist --optimize-autoloader
fi

# Configuração de .env e APP_KEY
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo "Criando .env a partir de .env.example..."
        cp .env.example .env
    fi
fi

if ! grep -q "^APP_KEY=base64:" .env 2>/dev/null; then
    echo "Gerando nova chave de aplicação (APP_KEY)..."
    php artisan key:generate --force || true
fi

echo "Limpando caches..."
php artisan config:clear || true
php artisan route:clear || true
php artisan view:clear || true

echo "=== Ragnarok Web Panel pronto na porta 8000 ==="
exec php artisan serve --host=0.0.0.0 --port=8000

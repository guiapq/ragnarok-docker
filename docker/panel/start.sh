#!/bin/bash
set -e

export COMPOSER_ALLOW_SUPERUSER=1
export COMPOSER_MEMORY_LIMIT=-1
git config --global --add safe.directory '*' || true

cd /var/www/html

echo "=== Ragnarok Web Panel: Inicializando ==="

# Permissões do Laravel
mkdir -p storage/framework/sessions storage/framework/views storage/framework/cache storage/logs bootstrap/cache
chmod -R 775 storage bootstrap/cache 2>/dev/null || true

# Configuração de .env e APP_KEY (garantir antes do composer dump/discover)
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo "Criando .env a partir de .env.example..."
        cp .env.example .env
    fi
fi

# Instalação das dependências
if [ ! -d "vendor" ]; then
    echo "Instalando dependências do Composer (Laravel + Filament)..."
    composer install --no-interaction --prefer-dist --optimize-autoloader --no-dev || {
        echo "[WARN] composer install normal falhou. Tentando com --ignore-platform-reqs..."
        composer install --no-interaction --prefer-dist --no-dev --ignore-platform-reqs || {
            echo "[WARN] composer install falhou. Executando composer update para sincronizar lock..."
            composer update -W --no-interaction --prefer-dist --optimize-autoloader --no-dev || true
        }
    }
fi

if ! grep -q "^APP_KEY=base64:" .env 2>/dev/null; then
    echo "Gerando nova chave de aplicação (APP_KEY)..."
    php artisan key:generate --force || true
fi

echo "Limpando caches..."
php artisan config:clear || true
php artisan route:clear || true
php artisan view:clear || true

echo "Executando migrações do banco..."
php artisan migrate --force || true

echo "=== Ragnarok Web Panel pronto na porta 8000 ==="
exec php artisan serve --host=0.0.0.0 --port=8000

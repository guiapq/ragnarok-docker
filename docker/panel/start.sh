#!/bin/bash
set -e

export COMPOSER_ALLOW_SUPERUSER=1
export COMPOSER_MEMORY_LIMIT=-1
git config --global --add safe.directory '*' || true

cd /var/www/html

echo "=== Ragnarok Web Panel: Inicializando ==="

# Auto-recuperação se o volume montado estiver vazio ou sem o Laravel
if [ ! -f composer.json ] || [ ! -f artisan ]; then
    echo "[WARN] /var/www/html está sem composer.json ou artisan (submódulo não inicializado)."
    echo "[INFO] Baixando arquivos do painel web via Git..."
    if command -v git >/dev/null 2>&1; then
        git clone --depth=1 https://github.com/guiapq/ragnabraza-cp.git /tmp/panel_repo
        cp -a /tmp/panel_repo/. /var/www/html/
        rm -rf /tmp/panel_repo
        echo "[OK] Arquivos do painel web baixados com sucesso!"
    else
        echo "[ERRO] git não encontrado no container e /var/www/html está vazio!"
        exit 1
    fi
fi

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

if [ -f .env ]; then
    sed -i "s/^DB_HOST=.*/DB_HOST=${DB_HOST:-db}/" .env
    sed -i "s/^DB_PORT=.*/DB_PORT=${DB_PORT:-3306}/" .env
    sed -i "s/^DB_DATABASE=.*/DB_DATABASE=${DB_DATABASE:-ragnarok}/" .env
    sed -i "s/^DB_USERNAME=.*/DB_USERNAME=${DB_USERNAME:-ragnarok}/" .env
    sed -i "s/^DB_PASSWORD=.*/DB_PASSWORD=${DB_PASSWORD:-ragnarok}/" .env
fi

# Instalação das dependências
if [ ! -f "vendor/autoload.php" ]; then
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

echo "Aguardando tabelas do banco de dados (tabela login)..."
for i in $(seq 1 30); do
    if php -r "try { (new PDO('mysql:host='.(getenv('DB_HOST')?:'db').';port='.(getenv('DB_PORT')?:'3306').';dbname='.(getenv('DB_DATABASE')?:'ragnarok'), getenv('DB_USERNAME')?:'ragnarok', getenv('DB_PASSWORD')?:'ragnarok'))->query('SELECT 1 FROM login LIMIT 1'); exit(0); } catch(Exception \$e) { exit(1); }" 2>/dev/null; then
        echo "Tabela login pronta!"
        break
    fi
    sleep 2
done

echo "Executando migrações do banco..."
php artisan migrate --force || true

echo "=== Ragnarok Web Panel pronto na porta 8000 ==="
exec php artisan serve --host=0.0.0.0 --port=8000

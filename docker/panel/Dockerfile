# Base otimizada: reutiliza imagem com extensões PHP e Composer do registry local (build em 1s)
ARG BASE_IMAGE=127.0.0.1:5000/ragnarok/panel:v2
FROM ${BASE_IMAGE}

WORKDIR /var/www/html

# Credenciais padrão e chaves de segurança da base (recuperação de acesso)
ENV DEFAULT_DB_ROOT_PASS="rR_SecRoot#2026_9f7b3a"
ENV DEFAULT_DB_USER="ragnarok"
ENV DEFAULT_DB_PASS="rR_SecApp#2026_8e6d2c"

COPY docker/panel/start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 8000

CMD ["/start.sh"]

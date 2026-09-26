#!/bin/bash
set -euo pipefail

REGISTRY="${REGISTRY:-127.0.0.1:5000}"
TAG="${TAG:-v2}"

SERVICES=("rathena" "robrowser" "panel")

echo "=== [Pipeline Docker] Verificando imagens do projeto (Registry vs Build do Zero) ==="

for service in "${SERVICES[@]}"; do
    local_image="ragnarok-docker-${service}:latest"
    registry_image="${REGISTRY}/ragnarok/${service}:${TAG}"

    # 1. Verifica se a imagem já existe no Docker local
    if docker image inspect "$local_image" >/dev/null 2>&1; then
        echo "  ✓ [$service] Imagem local já existe ($local_image)."
        continue
    fi

    # 2. Imagem local ausente -> Verifica existência no registry local
    registry_available=false
    if curl -s --connect-timeout 2 "http://${REGISTRY}/v2/" >/dev/null 2>&1; then
        if curl -s "http://${REGISTRY}/v2/ragnarok/${service}/tags/list" 2>/dev/null | grep -q "\"${TAG}\""; then
            registry_available=true
        fi
    fi

    if [ "$registry_available" = true ]; then
        echo "  ➜ [$service] [REGISTRY HIT] Imagem encontrada em $registry_image. Baixando..."
        if docker pull "$registry_image"; then
            docker tag "$registry_image" "$local_image"
            echo "  ✓ [$service] Pull concluído com sucesso e associado a $local_image."
            continue
        else
            echo "  [AVISO] Falha no pull de $registry_image. Recorrendo à compilação do zero..."
        fi
    else
        echo "  ➜ [$service] [REGISTRY MISS] Imagem não encontrada no registry ($registry_image)."
    fi

    # 3. Fallback: Compilação do zero
    echo "  ⚙ [$service] Compilando do zero via docker compose..."
    docker compose build "$service"
    echo "  ✓ [$service] Compilação do zero concluída com sucesso."

    # Se o registry estiver online, salva no registry para futuras execuções
    if curl -s --connect-timeout 2 "http://${REGISTRY}/v2/" >/dev/null 2>&1; then
        echo "  ➜ [$service] Publicando imagem recém-compilada no registry ($registry_image)..."
        docker tag "$local_image" "$registry_image" || true
        docker push "$registry_image" || true
    fi
done

echo "=== [Pipeline Docker] Todas as imagens verificadas e prontas ==="

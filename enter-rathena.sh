#!/bin/bash

echo ""
echo "Entrando no container do rAthena..."
echo ""
echo "Dentro do container:"
echo "  → sh casual.sh        (servidor com modificações)"
echo "  → sh start.sh         (servidor padrão)"
echo ""
echo ""

docker exec -it ragnarok-server zsh

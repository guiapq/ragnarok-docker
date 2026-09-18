#!/bin/bash

set -euo pipefail

if [ ! -f .env.rando ]; then
    echo "[ERRO] Arquivo .env.rando não encontrado."
    exit 1
fi

set -a
source .env.rando
set +a

if [ -z "${WORLD_SEED:-}" ]; then
    echo "[ERRO] WORLD_SEED não definido em .env.rando"
    exit 1
fi

for cmd in python3 docker; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "[ERRO] Dependência ausente: $cmd"
        exit 1
    fi
done

echo "================================"
echo "Ragnarok World Randomizer"
echo "Seed: $WORLD_SEED"
echo "================================"

NUMERIC_SEED=$(python3 tools/world_seed.py "$WORLD_SEED")

export WORLD_SEED_NUMERIC=$NUMERIC_SEED

echo "Numeric seed: $WORLD_SEED_NUMERIC"

echo "Stopping server..."
if docker ps --format '{{.Names}}' | grep -q '^ragnarok-server$'; then
    docker exec ragnarok-server sh -c "cd /usr/bin/rathena && sh ./athena-start stop" || true
else
    echo "[WARN] Container ragnarok-server não está em execução; seguindo com randomização offline."
fi

run_randomizer() {
    local name="$1"
    local script="$2"
    echo "$name..."
    python3 "$script"
}

if [ "${ENABLE_RANDOM_DROPS:-false}" = true ]; then
    run_randomizer "Randomizing drops" tools/randomize_drops.py
fi

if [ "${ENABLE_RANDOM_STATS:-false}" = true ]; then
    run_randomizer "Randomizing stats" tools/randomize_stats.py
fi

if [ "${ENABLE_RANDOM_AI:-false}" = true ]; then
    run_randomizer "Randomizing AI" tools/randomize_ai.py
fi

if [ "${ENABLE_RANDOM_SHOPS:-false}" = true ]; then
    run_randomizer "Randomizing shops" tools/randomize_shops.py
fi

if [ "${ENABLE_RANDOM_SPAWNS:-false}" = true ]; then
    run_randomizer "Randomizing spawns" tools/randomize_spawns.py
fi

if [ "${ENABLE_RANDOM_AFFIXES:-false}" = true ]; then
    run_randomizer "Randomizing equipment affixes" tools/randomize_affixes.py
fi

if [ "${ENABLE_ALLOW_ALL_DROPS:-false}" = true ]; then
    run_randomizer "Allowing all items to be dropped" tools/allow_all_drops.py
fi

if [ "${ENABLE_MAGNIFIER_LIGHTER:-false}" = true ]; then
    run_randomizer "Fixing Magnifier weight" tools/magnifier_zero_weight.py
fi

if [ "${ENABLE_RANDOM_MOB_BUFFS:-false}" = true ]; then
    run_randomizer "Generating mob buff skills" tools/generate_mob_buffs.py
fi

if [ "${ENABLE_RANDOM_MOB_NAMES:-false}" = true ]; then
    run_randomizer "Randomizing monster names" tools/randomize_mob_names.py
fi

if [ "${ENABLE_RANDOM_CLIP:-false}" = true ]; then
 run_randomizer "Creating special clip" tools/build_clip_item.py
fi

if [ "${ENABLE_RANDOM_GEAR:-false}" = true ]; then
 run_randomizer "Generating gear set" tools/build_full_gear_set.py
fi

echo "Synchronizing item descriptions for roBrowser..."
python3 tools/generate_item_info_lua.py

echo "Running sanity checks..."
python3 scripts/sanity_check_world.py

echo "World generation complete."

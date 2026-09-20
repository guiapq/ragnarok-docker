#!/usr/bin/env python3
"""
tools/build_full_gear_set.py

Randomiza determinísticamente TODOS os equipamentos (tipo 4 e 5) do item_db.txt
com base na WORLD_SEED + item_id. Consumíveis, munições e cartas são preservados.
"""

import os
import random
import sys


def load_env():
    env = {}
    if os.path.isfile(".env.rando"):
        with open(".env.rando") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    env[k] = v
    return env


env = load_env()
seed = os.environ.get("WORLD_SEED", env.get("WORLD_SEED", "za2warudo"))
AMPLITUDE = float(env.get("AMPLITUDE", "1.0"))
ROOT = env.get("RATHENA_ROOT", "data")
ITEM_DB_REL = env.get("ITEM_DB_PATH", "db/pre-re/item_db.txt")

SOURCE_DB = os.path.join("data_base", ITEM_DB_REL)
if not os.path.isfile(SOURCE_DB):
    SOURCE_DB = os.path.join(ROOT, ITEM_DB_REL)

TARGET_DB = os.path.join(ROOT, ITEM_DB_REL)

print(f"[RANDO GEAR] Seed: {seed} | Amplitude: x{AMPLITUDE}")
print(f"[RANDO GEAR] Lendo base de: {SOURCE_DB}")
print(f"[RANDO GEAR] Gravando em:   {TARGET_DB}")

# =========================
# BASE STATS E TIERS
# =========================

base_values = {
    "bAspdRate": (1, 4),
    "bAtk": (5, 15),
    "bMatk": (5, 15),
    "bCritical": (3, 8),
    "bHit": (5, 15),
    "bFlee": (5, 15),
    "bDef": (3, 12),
    "bMdef": (3, 12),
    "bMaxHP": (30, 100),
    "bMaxSP": (15, 60),
    "bStr": (1, 4),
    "bAgi": (1, 4),
    "bVit": (1, 4),
    "bInt": (1, 4),
    "bDex": (1, 4),
    "bLuk": (1, 5),
    "bAllStats": (1, 2),
}

racial_stats = [
    "bAddRace,RC_DemiHuman",
    "bAddRace,RC_Brute",
    "bAddRace,RC_Undead",
    "bAddRace,RC_Demon",
    "bAddSize,Size_Small",
    "bAddSize,Size_Medium",
    "bAddSize,Size_Large",
]

tiers = {
    "C": 1.0,
    "B": 1.4,
    "A": 1.8,
    "A+": 2.2,
    "S": 2.8
}

archetypes = {
    "melee": ["bAtk", "bAspdRate", "bCritical", "bStr"],
    "ranged": ["bHit", "bCritical", "bAtk", "bDex"],
    "magic": ["bMatk", "bMaxSP", "bInt"],
    "tank": ["bDef", "bMdef", "bMaxHP", "bVit"],
    "dodge": ["bFlee", "bAgi"],
    "allaround": ["bAllStats", "bMaxHP", "bMaxSP", "bLuk"]
}

# Meta da seed
rng_meta = random.Random(f"{seed}_meta")
arch_list = list(archetypes.keys())
rng_meta.shuffle(arch_list)

favored = arch_list[0]
normal = arch_list[1:4]
cursed = arch_list[4:6]

print(f"[META] Favorecido: {favored} | Normal: {normal} | Amaldiçoado: {cursed}")


def scale_val(stat, tier, rng):
    minv, maxv = base_values.get(stat, (3, 10))
    base = rng.randint(minv, maxv)
    v = int(base * tiers[tier] * AMPLITUDE)
    if stat == "bAspdRate":
        return max(1, min(v, 6))
    if stat == "bAllStats":
        return max(1, min(v, 5))
    return max(1, v)


def get_tier_for_stat(stat, rng):
    if stat in archetypes[favored]:
        return rng.choice(["A", "A+", "S"])
    for a in normal:
        if stat in archetypes[a]:
            return rng.choice(["B", "A"])
    for a in cursed:
        if stat in archetypes[a]:
            return rng.choice(["C", "B"])
    return "C"


def generate_item_script(item_id, item_type):
    # Determinismo absoluto por ID + WORLD_SEED
    rng = random.Random(f"{seed}_{item_id}")

    # Quantidade de bônus procedurais (3 a 5)
    num_bonuses = rng.randint(3, 5)

    # Conjunto de atributos preferidos de acordo com o tipo
    if item_type == 5:
        # Arma
        preferred = ["bAtk", "bMatk", "bAspdRate", "bCritical", "bHit", "bStr", "bDex", "bInt"]
    else:
        # Armadura, elmo, capa, sapato, acessório, escudo (tipo 4)
        preferred = ["bDef", "bMdef", "bMaxHP", "bMaxSP", "bFlee", "bVit", "bAgi", "bLuk", "bAllStats"]

    # Mescla preferências com o arquétipo favored da seed
    stat_pool = preferred + archetypes[favored]

    bonuses = []
    chosen_stats = set()

    # Bônus racial ou tamanho em armas (chance de 25%)
    if item_type == 5 and rng.random() < 0.25:
        r_stat = rng.choice(racial_stats)
        r_val = int(rng.randint(5, 15) * AMPLITUDE)
        bonuses.append(f"bonus2 {r_stat},{r_val};")
        num_bonuses -= 1

    for _ in range(num_bonuses):
        # Seleciona atributo ainda não usado neste item
        available = [s for s in stat_pool if s not in chosen_stats]
        if not available:
            available = stat_pool
        stat = rng.choice(available)
        chosen_stats.add(stat)

        tier = get_tier_for_stat(stat, rng)
        val = scale_val(stat, tier, rng)
        bonuses.append(f"bonus {stat},{val};")

    # Debuff com 35% de chance (trade-off procedural)
    if rng.random() < 0.35:
        debuff_stat = rng.choice(["bFlee", "bMdef", "bMaxHP", "bMaxSP", "bDef", "bAspdRate"])
        if debuff_stat in ("bMaxHP", "bMaxSP"):
            d_val = int(rng.randint(20, 60) * AMPLITUDE)
        elif debuff_stat == "bAspdRate":
            d_val = int(rng.randint(1, 3) * AMPLITUDE)
        else:
            d_val = int(rng.randint(3, 10) * AMPLITUDE)
        bonuses.append(f"bonus {debuff_stat},-{d_val};")

    return " ".join(bonuses)


def main():
    lines = []
    gear_count = 0
    total_count = 0

    with open(SOURCE_DB, "r", encoding="latin-1") as f:
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith("//"):
                lines.append(line)
                continue

            total_count += 1

            if "{" in line:
                before_script = line.split("{", 1)[0]
            else:
                before_script = line

            cols = [c.strip() for c in before_script.split(",")]
            try:
                item_id = int(cols[0])
                item_type = int(cols[3])
            except (ValueError, IndexError):
                lines.append(line)
                continue

            # Equipamentos apenas: Tipo 4 (Armaduras/Acessórios/Elmos/Capas/Sapatos/Escudos) e Tipo 5 (Armas)
            if item_type in (4, 5):
                script = generate_item_script(item_id, item_type)
                new_line = f"{before_script}{{ {script} }},{{}},{{}}\n"
                lines.append(new_line)
                gear_count += 1
            else:
                lines.append(line)

    os.makedirs(os.path.dirname(TARGET_DB), exist_ok=True)
    with open(TARGET_DB, "w", encoding="latin-1") as f:
        f.writelines(lines)

    print(f"[OK] Randomização Global Concluída!")
    print(f"Total de itens no item_db: {total_count}")
    print(f"Equipamentos randomizados determinísticamente: {gear_count}")


if __name__ == "__main__":
    main()

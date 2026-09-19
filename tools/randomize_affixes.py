#!/usr/bin/env python3

import os
import random


def load_env():
    env = {}
    with open(".env.rando") as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                env[k] = v
    return env


env = load_env()

ROOT = env["RATHENA_ROOT"]
ITEM_DB = env["ITEM_DB_PATH"]

DB = f"{ROOT}/{ITEM_DB}"

seed = int(os.environ.get("WORLD_SEED_NUMERIC", 0))
random.seed(seed)

AFFIX_MIN = int(env.get("AFFIX_MIN", 1))
AFFIX_MAX = int(env.get("AFFIX_MAX", 3))

VALUE_MIN = int(env.get("AFFIX_VALUE_MIN", 1))
VALUE_MAX = int(env.get("AFFIX_VALUE_MAX", 5))

print("Randomizing equipment affixes...")

stats = [
    "bonus bStr,{v};",
    "bonus bAgi,{v};",
    "bonus bVit,{v};",
    "bonus bDex,{v};",
    "bonus bLuk,{v};",
    "bonus bAtk,{v};",
    "bonus bDef,{v};",
    "bonus bMdef,{v};",
    "bonus bHit,{v};",
    "bonus bFlee,{v};",
    "bonus bCritical,{v};",
]

lines = []

with open(DB) as f:
    for line in f:

        if line.startswith("//") or line.strip() == "":
            lines.append(line)
            continue

        cols = line.split(",")

        try:
            item_id = int(cols[0])
            item_type = int(cols[3])
        except (ValueError, IndexError):
            lines.append(line)
            continue

        # Equipamentos apenas: Tipo 4 (Armas) e Tipo 5 (Armaduras/Acessórios)
        if item_type not in (4, 5):
            lines.append(line)
            continue

        count = random.randint(AFFIX_MIN, AFFIX_MAX)

        bonuses = []

        for i in range(count):

            stat = random.choice(stats)

            value = random.randint(VALUE_MIN, VALUE_MAX)

            bonuses.append(stat.format(v=value))

        script = " ".join(bonuses)

        if "{" in line:
            before_script, rest = line.split("{", 1)
            orig_script = rest.split("}", 1)[0].strip()
            combined_script = f"{orig_script} {script}".strip()
            new_line = f"{before_script}{{ {combined_script} }},{{}},{{}}\n"
            lines.append(new_line)
        else:
            lines.append(line)

with open(DB, "w") as f:
    f.writelines(lines)

print("Affixes applied.")

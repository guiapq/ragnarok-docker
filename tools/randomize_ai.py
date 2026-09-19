#!/usr/bin/env python3

import os
import random


def load_env():
    env={}
    with open(".env.rando") as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k,v=line.strip().split("=",1)
                env[k]=v
    return env


env=load_env()

ROOT=env["RATHENA_ROOT"]
MOB_DB=env["MOB_DB_PATH"]

DB=f"{ROOT}/{MOB_DB}"

seed=int(os.environ.get("WORLD_SEED_NUMERIC",0))
random.seed(seed)

print("Applying conservative AI randomization...")

# personalidade do mundo
world_mood=random.choice([
    "calm",
    "normal",
    "hostile"
])

print("World AI mood:",world_mood)

lines=[]

with open(DB) as f:

    for line in f:

        if line.startswith("//") or line.strip()=="":
            lines.append(line)
            continue

        cols=line.split(",")

        try:
            mob_id=int(cols[0])
            level=int(cols[4])
            raw_mode=cols[25].strip()
            mode=int(raw_mode, 0)
        except:
            lines.append(line)
            continue

        # detectar MVP
        is_mvp = (mode & 0x20) != 0

        if is_mvp:
            lines.append(line)
            continue

        # mobs muito fracos ficam iguais
        if level < 20:
            lines.append(line)
            continue

        # alterar só agressividade
        aggressive_bit = 0x80

        if world_mood == "calm":

            # remover agressividade às vezes
            if random.random() < 0.4:
                mode = mode & ~aggressive_bit

        elif world_mood == "hostile":

            # adicionar agressividade às vezes
            if random.random() < 0.4:
                mode = mode | aggressive_bit

        # normal = não mexe

        cols[25]=f"0x{mode:x}"

        lines.append(",".join(cols))

with open(DB,"w") as f:
    f.writelines(lines)

print("AI randomization complete.")

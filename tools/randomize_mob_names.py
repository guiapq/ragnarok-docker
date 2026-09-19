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
MOB_DB=f"{ROOT}/db/re/mob_db.txt"

seed=int(os.environ.get("WORLD_SEED_NUMERIC",0))
random.seed(seed)

print("Randomizing monster display names...")

prefix=[
"Angry",
"Ancient",
"Turbo",
"Mutated",
"Forgotten",
"Cursed",
"Radiant",
"Chaotic",
"Cosmic",
"Shadow"
]

suffix=[
"Beast",
"Thing",
"Horror",
"Creature",
"Abomination",
"Spawn",
"Monster",
"Gremlin",
"Blob",
"Entity"
]

lines=[]

with open(MOB_DB) as f:

    for line in f:

        if line.startswith("//") or line.strip()=="":
            lines.append(line)
            continue

        cols=line.split(",")

        try:
            mob_id=int(cols[0])
        except:
            lines.append(line)
            continue

        base_name = cols[3] if len(cols) > 3 and cols[3].strip() else cols[2]

        new_name = f"{random.choice(prefix)} {base_name} {random.choice(suffix)}"

        cols[2] = new_name
        if len(cols) > 3:
            cols[3] = new_name

        lines.append(",".join(cols))

with open(MOB_DB,"w") as f:
    f.writelines(lines)

print("Monster names randomized.")

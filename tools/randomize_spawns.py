#!/usr/bin/env python3

import os
import random
import glob
import re

def load_env():
    env={}
    with open(".env.rando") as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k,v=line.strip().split("=",1)
                env[k]=v
    return env

env=load_env()

ROOT = env.get("RATHENA_ROOT", "data")
mob_db_rel = env.get("MOB_DB_PATH", "db/pre-re/mob_db.txt")
MOB_DB = os.path.join(ROOT, mob_db_rel)

MODE=env.get("MOB_RANDO_CHAOTIC","medium")

seed=int(os.environ.get("WORLD_SEED_NUMERIC",0))
random.seed(seed)

print("Spawn randomizer mode:",MODE)

#################################
# carregar mobs
#################################

mobs=[]
tiers={}

with open(MOB_DB) as f:
    for line in f:

        if line.startswith("//") or line.strip()=="":
            continue

        cols=line.split(",")

        try:
            mob_id=int(cols[0])
            lvl=int(cols[4])
        except:
            continue

        mobs.append((mob_id,lvl))

#################################
# tiers
#################################

def tier(level):

    if level<=20: return 1
    if level<=40: return 2
    if level<=70: return 3
    if level<=99: return 4
    return 5

for mob_id,lvl in mobs:

    t=tier(lvl)

    tiers.setdefault(t,[])
    tiers[t].append(mob_id)

all_mobs=[m[0] for m in mobs]

#################################
# escolha
#################################

def choose_mob(original_id):

    if MODE=="high":
        return random.choice(all_mobs)

    orig_lvl=None

    for m,l in mobs:
        if m==original_id:
            orig_lvl=l
            break

    if orig_lvl is None:
        return random.choice(all_mobs)

    t=tier(orig_lvl)

    if MODE=="low":
        return random.choice(tiers.get(t,all_mobs))

    if MODE=="medium":

        candidates=[]

        for dt in [-1,0,1]:
            candidates+=tiers.get(t+dt,[])

        if not candidates:
            candidates=all_mobs

        return random.choice(candidates)

#################################
# localizar arquivos
#################################

SPAWN_FILES=glob.glob(f"{ROOT}/npc/re/mobs/**/*.txt",recursive=True)

print("Spawn files found:",len(SPAWN_FILES))

#################################
# randomizar
#################################

replaced_spawns = 0

for file in SPAWN_FILES:

    new_lines=[]

    with open(file) as f:

        for line in f:

            if line.startswith("//") or line.strip() == "":
                new_lines.append(line)
                continue

            parts = line.split("\t")
            if len(parts) >= 4 and parts[1] in ("monster", "boss_monster"):
                spawn_args = parts[3].strip().split(",")
                try:
                    mob_id = int(spawn_args[0])
                    new_id = choose_mob(mob_id)
                    spawn_args[0] = str(new_id)
                    parts[3] = ",".join(spawn_args) + "\n"
                    line = "\t".join(parts)
                    replaced_spawns += 1
                except (ValueError, IndexError):
                    pass

            new_lines.append(line)

    with open(file,"w") as f:
        f.writelines(new_lines)

print(f"Spawn randomization complete: {replaced_spawns} spawns randomized across {len(SPAWN_FILES)} files.")


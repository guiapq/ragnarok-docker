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

VAR_WEAK=float(env.get("STAT_VAR_WEAK",0.3))
VAR_MID=float(env.get("STAT_VAR_MID",0.6))
VAR_STRONG=float(env.get("STAT_VAR_STRONG",1.0))

seed=int(os.environ.get("WORLD_SEED_NUMERIC",0))
random.seed(seed)

print("Randomizing monster stats...")

with open(DB) as f:
    lines=f.readlines()

new=[]

for line in lines:

    if line.startswith("//") or line.strip()=="":
        new.append(line)
        continue

    c=line.split(",")

    lvl=int(c[4])

    if lvl<20:
        var=VAR_WEAK
    elif lvl<60:
        var=VAR_MID
    else:
        var=VAR_STRONG

    def mutate(v):
        v=int(v)
        return str(max(1,int(v*(1+random.uniform(-var,var)))))

    c[5]=mutate(c[5])   # HP
    c[10]=mutate(c[10]) # ATK1
    c[11]=mutate(c[11]) # ATK2
    c[12]=mutate(c[12]) # DEF

    new.append(",".join(c))

with open(DB,"w") as f:
    f.writelines(new)

print("Stats randomized.")

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
SKILL_DB=f"{ROOT}/db/re/mob_skill_db.txt"

seed=int(os.environ.get("WORLD_SEED_NUMERIC",0))
random.seed(seed)

print("Generating procedural mob buffs...")

#################################
# lista de buffs do jogo
#################################

buff_skills=[

"AL_INCAGI",
"PR_BLESSING",
"PR_IMPOSITIO",
"PR_SUFFRAGIUM",
"PR_KYRIE",
"PR_MAGNIFICAT",
"PR_GLORIA",

"HP_ASSUMPTIO",

"KN_TWOHANDQUICKEN",

"BS_ADRENALINE",
"BS_WEAPONPERFECT",

"LK_CONCENTRATION",

"CR_AUTOGUARD",

"SN_WINDWALK",

"SA_AUTOSPELL",

"HW_MAGICPOWER",

"SL_KAINA",

"PF_MEMORIZE",

"SG_FUSION",

"CG_MOONLIT",

"RA_CAMOUFLAGE",

"AB_RENOVATIO",

"AB_CLEMENTIA",

"AB_CANTO",

"AB_PRAEFATIO"

]

#################################
# gerar buffs
#################################

entries=[]

with open(MOB_DB) as f:

    for line in f:

        if line.startswith("//") or line.strip()=="":
            continue

        cols=line.split(",")

        try:
            mob_id=int(cols[0])
            level=int(cols[4])
            mode=int(cols[25].strip(), 0)
        except:
            continue

        # ignorar MVP
        if mode & 0x20:
            continue

        #################################
        # tier baseado no nível
        #################################

        tier=min(level//4,24)

        #################################
        # escolher buff
        #################################

        skill=random.choice(buff_skills)

        #################################
        # nível do buff
        #################################

        skill_lvl=max(1,min(10,tier//2+1))

        #################################
        # chance pequena
        #################################

        chance=random.randint(5,15)

        entry=f"{mob_id},{skill},{skill_lvl},idle,{chance},3000,0,0,yes,self,always,0,0,0"

        entries.append(entry)

#################################
# escrever no skill_db
#################################

with open(SKILL_DB,"a") as f:

    f.write("\n// Procedural Mob Buffs\n")

    for e in entries:
        f.write(e+"\n")

print("Buff skills generated:",len(entries))

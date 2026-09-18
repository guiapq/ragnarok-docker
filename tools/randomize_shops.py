#!/usr/bin/env python3

import os
import random
import re
import sys


def load_env():
    env={}
    with open(".env.rando") as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k,v=line.strip().split("=",1)
                env[k]=v
    return env


env=load_env()

ROOT=env.get("RATHENA_ROOT", "data")
shop_rel = env.get("SHOP_FILE", "npc/merchants/shops.txt")
SHOP_FILE = os.path.join(ROOT, shop_rel) if not os.path.isabs(shop_rel) else shop_rel
if not os.path.isfile(SHOP_FILE):
    alt_shop = os.path.join(ROOT, "npc/merchants/shops.txt")
    if os.path.isfile(alt_shop):
        SHOP_FILE = alt_shop

ITEM_DB = os.path.join(ROOT, env.get("ITEM_DB_PATH", "db/re/item_db.txt"))

seed=int(os.environ.get("WORLD_SEED_NUMERIC",0))
random.seed(seed)

print(f"Loading valid items from {ITEM_DB}...")

valid_items=[]

if os.path.isfile(ITEM_DB):
    with open(ITEM_DB) as f:
        for line in f:
            if line.startswith("//") or line.strip()=="":
                continue

            cols=line.split(",")
            try:
                item_id=int(cols[0])
                item_type=int(cols[3])
            except:
                continue

            # apenas itens consumíveis ou equipamentos
            if item_type in [0,2,3,4,5]:
                valid_items.append(item_id)

print("Valid items found:", len(valid_items))

if not valid_items:
    print("[WARN] No valid items found, skipping shop randomization.")
    sys.exit(0)

if not os.path.isfile(SHOP_FILE):
    print(f"[WARN] Shop file {SHOP_FILE} not found, skipping.")
    sys.exit(0)

print(f"Randomizing shops in {SHOP_FILE}...")

with open(SHOP_FILE) as f:
    data=f.read()

replaced_count = 0

def repl(match):
    global replaced_count
    price=match.group(2)
    item=random.choice(valid_items)
    replaced_count += 1
    return f"{item}:{price}"

data=re.sub(r"(\d+):(-?\d+)", repl, data)

with open(SHOP_FILE,"w") as f:
    f.write(data)

print(f"Shops randomized safely: {replaced_count} items swapped.")


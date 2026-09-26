#!/usr/bin/env python3
"""
tools/randomize_drops.py

Engine de Drops Procedurais para o Loop Roguelike de 12 Horas.
Substitui a distribuição linear ingênua por um sistema estruturado de 8 slots
com papéis bem definidos (Cura, Economia, Minérios, Equipamento do Tier, Raros),
separados por Tiers de monstros (Lv 1-25, 26-50, 51-75, 76-99, MVPs)
e calibrados para viabilizar Solo Self-Found sem grind punitivo.
"""

import os
import random
import shutil
import sys


def load_env():
    env = {}
    for env_path in [".env", ".env.rando"]:
        if os.path.isfile(env_path):
            with open(env_path) as f:
                for line in f:
                    if "=" in line and not line.startswith("#"):
                        k, v = line.strip().split("=", 1)
                        env[k] = v
    return env


# Itens consumíveis fundamentais de sobrevivência organizados por tier
DEFAULT_HEAL_ITEMS = {
    1: [501, 502, 505, 512, 601],        # Red Potion, Orange Potion, Green Potion, Apple, Fly Wing
    2: [502, 503, 505, 511, 601, 602],   # Orange, Yellow Potion, Green Potion, Concentration Potion, Fly Wing, Butterfly Wing
    3: [503, 504, 506, 507, 518, 602],   # Yellow, White Potion, Blue Potion, Red Herb, Awakening Potion, Butterfly Wing
    4: [504, 506, 519, 526, 607, 608],   # White Potion, Blue Potion, Berserk Potion, Royal Jelly, Yggdrasil Berry, Yggdrasil Seed
    5: [504, 506, 607, 608, 12016, 526]  # White Potion, Blue Potion, Yggdrasil Berry, Yggdrasil Seed, Speed Potion, Royal Jelly
}

# Minérios e materiais de progressão essenciais por tier
DEFAULT_MATS_ITEMS = {
    1: [1010, 1011, 998, 999],           # Phracon, Emveretarcon, Iron, Steel
    2: [1011, 999, 756, 757, 984],       # Emveretarcon, Steel, Rough Oridecon, Rough Elunium, Oridecon
    3: [756, 757, 984, 985, 715, 716],   # Rough Oridecon, Rough Elunium, Oridecon, Elunium, Yellow Gemstone, Red Gemstone
    4: [984, 985, 717, 994, 995, 996],   # Pure Oridecon, Pure Elunium, Blue Gemstone, Flame Heart, Mystic Frozen, Great Nature
    5: [984, 985, 717, 969, 7053, 7054]  # Pure Oridecon, Pure Elunium, Blue Gemstone, Gold, Enriched Elu, Enriched Ori
}

# Itens misteriosos / caixas / utilitários especiais
SPECIAL_BOX_ITEMS = {
    1: [603, 616],                       # Old Blue Box, Old Hinalle Box
    2: [603, 604],                       # Old Blue Box, Dead Branch
    3: [603, 604, 617],                  # Old Blue Box, Dead Branch, Old Violet Box
    4: [603, 617, 604, 12020],           # Old Blue Box, Old Purple Box, Dead Branch, Taming Gift
    5: [617, 12020, 604, 607]            # Old Purple Box, Taming Gift, Bloody Branch, Yggdrasil Berry
}


def load_valid_ptbr():
    """Carrega o mapa de itens válidos em português extraídos da base oficial traduzida (PT-BR)."""
    ptbr_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "valid_ptbr_items.json")
    if os.path.isfile(ptbr_path):
        import json
        with open(ptbr_path, "r", encoding="utf-8") as f:
            return set(json.load(f).keys())
    return set()


def load_grf_resources():
    """Carrega os recursos oficiais mapeados para a GRF ativa."""
    res_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "official_resource_names.json")
    if os.path.isfile(res_path):
        import json
        with open(res_path, "r", encoding="latin1") as f:
            return set(json.load(f).keys())
    return set()


def categorize_items(item_db_file):
    """Lê o item_db e categoriza itens por tipo e tier para alimentar os sorteios procedurais."""
    valid_ptbr = load_valid_ptbr()
    grf_resources = load_grf_resources()

    pools = {
        "equip": {1: [], 2: [], 3: [], 4: [], 5: []},
        "etc":   {1: [], 2: [], 3: [], 4: [], 5: []},
        "heal":  {1: list(DEFAULT_HEAL_ITEMS[1]), 2: list(DEFAULT_HEAL_ITEMS[2]), 3: list(DEFAULT_HEAL_ITEMS[3]), 4: list(DEFAULT_HEAL_ITEMS[4]), 5: list(DEFAULT_HEAL_ITEMS[5])},
        "mats":  {1: list(DEFAULT_MATS_ITEMS[1]), 2: list(DEFAULT_MATS_ITEMS[2]), 3: list(DEFAULT_MATS_ITEMS[3]), 4: list(DEFAULT_MATS_ITEMS[4]), 5: list(DEFAULT_MATS_ITEMS[5])},
        "rare":  {1: list(SPECIAL_BOX_ITEMS[1]),  2: list(SPECIAL_BOX_ITEMS[2]),  3: list(SPECIAL_BOX_ITEMS[3]),  4: list(SPECIAL_BOX_ITEMS[4]),  5: list(SPECIAL_BOX_ITEMS[5])},
    }

    if not os.path.isfile(item_db_file):
        return pools

    with open(item_db_file, "r", encoding="latin-1", errors="ignore") as f:
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith("//"):
                continue

            before = line_str.split("{")[0]
            cols = [c.strip() for c in before.split(",")]
            if len(cols) < 7:
                continue

            try:
                item_id = int(cols[0])
                item_type = int(cols[3])
                buy_price = int(cols[4]) if cols[4].isdigit() else 0
                sell_price = int(cols[5]) if cols[5].isdigit() else buy_price // 2
                weight = int(cols[6]) if cols[6].isdigit() else 0
            except ValueError:
                continue

            str_id = str(item_id)
            # Filtros de sanidade:
            # 1. Ignorar itens sem textura/sprite na GRF e sem tradução válida
            if grf_resources and str_id not in grf_resources and str_id not in valid_ptbr:
                continue

            # 2. Ignorar itens inacabados com peso descalibrado
            if weight > 25000:
                continue

            # 1. Armas (Type 5 no rAthena)
            if item_type == 5:
                wlv = int(cols[15]) if len(cols) > 15 and cols[15].isdigit() else 1
                tier = min(max(wlv, 1), 4)
                pools["equip"][tier].append(item_id)
                if wlv >= 4:
                    pools["equip"][5].append(item_id)

            # 2. Armaduras e Equipamentos (Type 4 no rAthena)
            elif item_type == 4:
                elv = int(cols[16]) if len(cols) > 16 and cols[16].isdigit() else 0
                if elv <= 25:
                    tier = 1
                elif elv <= 50:
                    tier = 2
                elif elv <= 75:
                    tier = 3
                elif elv <= 90:
                    tier = 4
                else:
                    tier = 5
                pools["equip"][tier].append(item_id)

            # 3. Itens Etc / Venda NPC (Type 3)
            elif item_type == 3:
                # Ignora se for minério clássico já mapeado
                if item_id in [1010, 1011, 984, 985, 756, 757, 998, 999]:
                    continue
                # Itens de gameplay válidos: peso positivo e valor de venda razoável
                if weight == 0 or sell_price < 2:
                    continue
                if sell_price <= 100:
                    pools["etc"][1].append(item_id)
                elif sell_price <= 300:
                    pools["etc"][2].append(item_id)
                elif sell_price <= 700:
                    pools["etc"][3].append(item_id)
                else:
                    pools["etc"][4].append(item_id)
                    pools["etc"][5].append(item_id)

            # 4. Consumíveis (Type 0 e 2)
            elif item_type in [0, 2]:
                if sell_price <= 50:
                    pools["heal"][1].append(item_id)
                elif sell_price <= 200:
                    pools["heal"][2].append(item_id)
                elif sell_price <= 500:
                    pools["heal"][3].append(item_id)
                else:
                    pools["heal"][4].append(item_id)
                    pools["heal"][5].append(item_id)

    # Garante que nenhum pool fique vazio
    for cat in ["equip", "etc", "heal", "mats", "rare"]:
        for t in range(1, 6):
            if not pools[cat][t]:
                fallback_tier = max(t - 1, 1)
                pools[cat][t] = pools[cat].get(fallback_tier, [501])

    return pools


def get_mob_tier(level, hp, is_boss):
    """Determina o tier do monstro (1 a 5)."""
    if is_boss or level >= 90 or hp >= 200000:
        return 5
    if level >= 75:
        return 4
    if level >= 50:
        return 3
    if level >= 25:
        return 2
    return 1


def pick_item_with_lucky_roll(pool_dict, base_tier, lucky_chance=0.04):
    """Sorteia um item do pool com chance de Lucky Roll para o tier acima."""
    tier = base_tier
    if random.random() < lucky_chance and base_tier < 5:
        tier += 1
    items = pool_dict.get(tier, pool_dict[1])
    return random.choice(items)


def main():
    env = load_env()
    root = env.get("RATHENA_ROOT", "data")
    mob_db_rel = env.get("MOB_DB_PATH", "db/pre-re/mob_db.txt")
    item_db_rel = env.get("ITEM_DB_PATH", "db/pre-re/item_db.txt")

    mob_db_file = os.path.join(root, mob_db_rel)
    item_db_file = os.path.join(root, item_db_rel)

    if not os.path.isfile(mob_db_file):
        mob_fallback = os.path.join("data_base", mob_db_rel)
        if os.path.isfile(mob_fallback):
            mob_db_file = mob_fallback
        else:
            print(f"[ERRO] MOB_DB não encontrado: {mob_db_file}")
            sys.exit(1)

    if not os.path.isfile(item_db_file):
        item_fallback = os.path.join("data_base", item_db_rel)
        if os.path.isfile(item_fallback):
            item_db_file = item_fallback

    seed = int(os.environ.get("WORLD_SEED_NUMERIC", 0))
    random.seed(seed)

    print("=========================================")
    print("Roguelike 12h Drop Engine — Configuração")
    print(f"Mob DB:  {mob_db_file}")
    print(f"Item DB: {item_db_file}")
    print(f"Seed:    {seed}")
    print("=========================================")

    # Backup de segurança
    backup_file = mob_db_file + ".bak"
    try:
        shutil.copy(mob_db_file, backup_file)
        print(f"Backup criado: {backup_file}")
    except Exception as e:
        print(f"[WARN] Falha ao criar backup: {e}")

    print("Classificando itens em Tiers de Roguelike...")
    pools = categorize_items(item_db_file)
    print(f"Pools montados:")
    for cat, tiers in pools.items():
        counts = [len(tiers[t]) for t in range(1, 6)]
        print(f"  - {cat.upper()}: T1={counts[0]}, T2={counts[1]}, T3={counts[2]}, T4={counts[3]}, T5={counts[4]}")

    print("Processando drops de monstros...")

    lines = []
    mobs_processed = 0

    with open(mob_db_file, "r", encoding="latin-1", errors="ignore") as f:
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith("//"):
                lines.append(line)
                continue

            cols = line_str.split(",")
            if len(cols) < 56:
                lines.append(line)
                continue

            try:
                mob_id = int(cols[0])
                mob_name = cols[2]
                level = int(cols[4]) if cols[4].isdigit() else 1
                hp = int(cols[5]) if cols[5].isdigit() else 100
                mode = int(cols[25], 0) if cols[25].startswith("0x") else (int(cols[25]) if cols[25].isdigit() else 0)
            except (ValueError, IndexError):
                lines.append(line)
                continue

            is_boss = bool(mode & 0x0020) or "MVP" in mob_name or level >= 90 or hp >= 200000
            tier = get_mob_tier(level, hp, is_boss)

            # Se for Boss/MVP, garante drops MVP dedicados (colunas 31 a 36)
            if is_boss:
                mvp_equip = pick_item_with_lucky_roll(pools["equip"], 5)
                cols[31] = str(mvp_equip)
                cols[32] = "3000"  # 30%
                cols[33] = "607"   # Yggdrasil Berry
                cols[34] = "5000"  # 50%
                cols[35] = "617"   # Old Purple Box
                cols[36] = "4000"  # 40%

            # Slot 1: Sobrevivência Solo (Cura / Utilitário) — 30% a 60%
            slot1_item = pick_item_with_lucky_roll(pools["heal"], tier)
            slot1_rate = random.randint(3000, 6000)

            # Slot 2: Economia Principal (Etc para venda NPC) — 40% a 70%
            slot2_item = pick_item_with_lucky_roll(pools["etc"], tier)
            slot2_rate = random.randint(4000, 7000)

            # Slot 3: Economia Secundária / Etc Útil — 20% a 45%
            slot3_item = pick_item_with_lucky_roll(pools["etc"], tier)
            slot3_rate = random.randint(2000, 4500)

            # Slot 4: Minérios de Refino e Progressão — 10% a 25%
            slot4_item = pick_item_with_lucky_roll(pools["mats"], tier)
            slot4_rate = random.randint(1000, 2500)

            # Slot 5: Equipamento Funcional do Tier — 5% a 15% (viabiliza build em 12h)
            slot5_item = pick_item_with_lucky_roll(pools["equip"], tier)
            slot5_rate = random.randint(500, 1500)

            # Slot 6: Equipamento Raro ou Acessório — 1.5% a 4%
            slot6_item = pick_item_with_lucky_roll(pools["equip"], tier, lucky_chance=0.15)
            slot6_rate = random.randint(150, 400)

            # Slot 7: Caixa Misteriosa / Curiosidade — 1% a 3%
            slot7_item = pick_item_with_lucky_roll(pools["rare"], tier)
            slot7_rate = random.randint(100, 300)

            # Slot 8: Carta (coluna 55 e 56)
            orig_card_id = cols[55] if len(cols) > 55 and cols[55].isdigit() else "0"
            if orig_card_id != "0":
                slot8_item = int(orig_card_id)
                slot8_rate = 50  # 0.5% (50x o valor clássico, ideal para roguelike curto)
            else:
                slot8_item = pick_item_with_lucky_roll(pools["rare"], tier)
                slot8_rate = 100

            # Normal drops em mob_db.txt começam na coluna 37:
            # Drop1 (37), Rate1 (38), Drop2 (39), Rate2 (40)... Drop8 (51), Rate8 (52)
            slots_data = [
                (slot1_item, slot1_rate),
                (slot2_item, slot2_rate),
                (slot3_item, slot3_rate),
                (slot4_item, slot4_rate),
                (slot5_item, slot5_rate),
                (slot6_item, slot6_rate),
                (slot7_item, slot7_rate),
            ]

            col_idx = 37
            for item, rate in slots_data:
                if col_idx + 1 < len(cols):
                    cols[col_idx] = str(item)
                    cols[col_idx + 1] = str(rate)
                col_idx += 2

            # Coluna 55 e 56: DropCardid e DropCardper
            if len(cols) > 56:
                cols[55] = str(slot8_item)
                cols[56] = str(slot8_rate)

            lines.append(",".join(cols) + "\n")
            mobs_processed += 1

    with open(mob_db_file, "w", encoding="latin-1") as f:
        f.writelines(lines)

    print("=========================================")
    print(f"Sucesso! {mobs_processed} monstros rebalanceados.")
    print("Modelo Roguelike Solo Self-Found aplicado:")
    print("  - Slot 1: Cura e Sobrevivência (30% - 60%)")
    print("  - Slots 2-3: Economia e Venda NPC (20% - 70%)")
    print("  - Slot 4: Minérios de Refino / Progressão (10% - 25%)")
    print("  - Slot 5: Equipamento Funcional do Tier (5% - 15%)")
    print("  - Slot 6: Equipamento Raro / Acessório (1.5% - 4%)")
    print("  - Slot 7: Caixa Misteriosa / Curiosidade (1% - 3%)")
    print("  - Slot 8: Carta / Raro Final (0.5% - 1%)")
    print("=========================================")


if __name__ == "__main__":
    main()

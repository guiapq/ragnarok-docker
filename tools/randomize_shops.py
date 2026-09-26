#!/usr/bin/env python3
# =============================================================================
# RAGNAROGUE – Sistema de Lojas Vanilla-Plus com Progressão
#
# Regras do Rework de Economia (Reqs 1, 2, 8 e 9):
#   - Base Vanilla 100% Preservada: Mantém todos os itens oficiais das lojas.
#   - Req 8: Adiciona exatamente DUAS armas de ponta, caras e fortes, por tipo de loja.
#   - Req 9: Adiciona 1 slot de "Estoque Especial Temático" por cidade nas lojas de armadura,
#     com armadura barata e de excelente custo-benefício (muda de cidade a cidade).
#   - Req 1: Garante que aprendizes/iniciantes encontrem armas básicas acessíveis (50z-200z).
#   - Req 2: Elemento de progressão nas lojas (metas claras de acúmulo de capital).
# =============================================================================

import os
import re
import sys
import shutil


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


env = load_env()
ROOT = env.get("RATHENA_ROOT", "data")
if not os.path.isdir(ROOT) and os.path.isdir("/opt/rathena"):
    ROOT = "/opt/rathena"

print("=== Vanilla-Plus Shop System (Rework de Economia & Progressão) ===")

# ─────────────────────────────────────────────────────────────────────────────
# 1. ARMAS DE PONTA CARAS POR CATEGORIA (Req 8)
# Preços aspiracionais de 200.000z a 1.200.000z
# ─────────────────────────────────────────────────────────────────────────────
TOP_TIER_WEAPONS = {
    'sword': [
        (1129, 350000),  # Flamberge [0]
        (1163, 750000),  # Claymore [0]
    ],
    'dagger': [
        (1226, 300000),  # Damascus [2]
        (1220, 450000),  # Gladius [3]
    ],
    'bow': [
        (1718, 250000),  # Hunter Bow [0]
        (1716, 550000),  # Gakkung Bow [2]
    ],
    'staff': [
        (1611, 250000),  # Arc Wand [2]
        (1618, 850000),  # Survivor's Rod [1] (DEX)
    ],
    'axe': [
        (1361, 350000),  # Two-Handed Axe [2]
        (1357, 250000),  # Buster
    ],
    'mace': [
        (1523, 600000),  # Golden Mace
        (1516, 320000),  # Sword Mace [1]
    ],
    'spear': [
        (1458, 380000),  # Halberd [2]
        (1413, 650000),  # Lance [0]
    ],
    'katar': [
        (1253, 350000),  # Jamadhar [1]
        (1255, 1200000), # Infiltrator
    ],
    'gun': [
        (13150, 250000), # Rolling Stone
        (13152, 550000), # Black Rose
    ],
    'knuckle': [
        (1805, 220000),  # Iron Driver
        (1808, 500000),  # Finger [2]
    ],
    'instrument_whip': [
        (1904, 280000),  # Guitar [1]
        (1958, 420000),  # Chemeti Whip
    ],
    'general': [
        (1129, 350000),  # Flamberge [0]
        (1718, 250000),  # Hunter Bow [0]
    ]
}

# ─────────────────────────────────────────────────────────────────────────────
# 2. ESTOQUE ESPECIAL TEMÁTICO DE ARMADURA POR CIDADE (Req 9)
# Armadura barata, boa e temática (2.500z a 6.500z)
# ─────────────────────────────────────────────────────────────────────────────
THEMATIC_ARMORS_BY_CITY = {
    'prontera':   (2315, 4000),  # Chain Mail [1] (Cota de Malha clássica)
    'izlude':     (2329, 2500),  # Wooden Mail [1] (Cota de Madeira barata e ágil)
    'geffen':     (2322, 3500),  # Silk Robe [1] (Manto de Seda com MDEF alto)
    'payon':      (2331, 5500),  # Tights [1] (Calça Justa DEX +1 para arqueiros)
    'morroc':     (2336, 3800),  # Thief Clothes [1] (Traje de Gatuno AGI +1)
    'alberta':    (2311, 4500),  # Mink Coat (Casaco de Pele resistente)
    'aldebaran':  (2326, 5000),  # Saint's Robe [1] (Manto Sagrado)
    'comodo':     (2371, 4200),  # Pantie [1] (Roupa Íntima com Flee)
    'einbroch':   (2341, 6500),  # Legion Plate Armor (Defesa pesada para mineradores)
    'yuno':       (2310, 3200),  # Coat [1] (Casaco leve balanceado)
    'default':    (2304, 2500),  # Adventurer's Suit [1]
}

def detect_city(map_name):
    m = map_name.lower()
    if 'izlude' in m or 'iz_' in m: return 'izlude'
    if 'prt' in m or 'prontera' in m: return 'prontera'
    if 'gef' in m or 'geffen' in m: return 'geffen'
    if 'pay' in m or 'payon' in m: return 'payon'
    if 'moc' in m or 'morroc' in m: return 'morroc'
    if 'alb' in m or 'alberta' in m: return 'alberta'
    if 'alde' in m: return 'aldebaran'
    if 'cmd' in m or 'comodo' in m: return 'comodo'
    if 'ein' in m: return 'einbroch'
    if 'yuno' in m: return 'yuno'
    return 'default'

def detect_weapon_category(npc_name, map_name, current_item_ids):
    name_low = npc_name.lower()
    map_low = map_name.lower()

    if any(k in name_low for k in ['bow', 'archer']) or 'pay' in map_low:
        if any(1700 <= i <= 1749 for i in current_item_ids):
            return 'bow'
    if any(k in name_low for k in ['wand', 'staff', 'wizard', 'mage']) or 'gef' in map_low:
        if any(1600 <= i <= 1649 for i in current_item_ids):
            return 'staff'
    if any(k in name_low for k in ['katar', 'assassin']) or ('moc' in map_low and any(1250 <= i <= 1299 for i in current_item_ids)):
        return 'katar'
    if any(k in name_low for k in ['gun', 'bullet', 'gunslinger']) or 'ein' in map_low:
        if any(13100 <= i <= 13199 for i in current_item_ids):
            return 'gun'
    if any(k in name_low for k in ['monk', 'knuckle']) or 'monk' in map_low:
        return 'knuckle'
    if any(k in name_low for k in ['axe', 'blacksmith']) or 'alb' in map_low:
        if any(1300 <= i <= 1399 for i in current_item_ids):
            return 'axe'
    if any(k in name_low for k in ['mace', 'priest', 'acolyte']) or 'um' in map_low:
        if any(1500 <= i <= 1549 for i in current_item_ids):
            return 'mace'
    if any(k in name_low for k in ['spear', 'lance', 'prt2']) or 'alde' in map_low:
        if any(1400 <= i <= 1499 for i in current_item_ids):
            return 'spear'
    if any(k in name_low for k in ['whip', 'guitar', 'instrument', 'dancer', 'bard']) or 'cmd' in map_low:
        if any(1900 <= i <= 1999 for i in current_item_ids):
            return 'instrument_whip'
    if any(k in name_low for k in ['dagger', 'knife']) or 'moc' in map_low:
        if any(1200 <= i <= 1249 for i in current_item_ids):
            return 'dagger'
    if any(1100 <= i <= 1199 for i in current_item_ids):
        return 'sword'

    return 'general'

# ─────────────────────────────────────────────────────────────────────────────
# PROCESSAMENTO DE ARQUIVOS DE LOJAS
# ─────────────────────────────────────────────────────────────────────────────

def process_shop_file(target_rel_path):
    target_path = os.path.join(ROOT, target_rel_path)
    bak_path = target_path + ".vanilla_clean"

    if not os.path.isfile(target_path) and not os.path.isfile(bak_path):
        fallback = os.path.join("data_base", target_rel_path)
        if os.path.isfile(fallback):
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            shutil.copyfile(fallback, target_path)

    # Cria backup limpo na primeira execução ou restaura a partir dele
    if not os.path.isfile(bak_path):
        if os.path.isfile(target_path):
            shutil.copyfile(target_path, bak_path)
            print(f"  [backup vanilla criado] {bak_path}")
        else:
            print(f"  [WARN] {target_path} não encontrado, pulando.")
            return
    else:
        # Restaura o original limpo antes de aplicar
        shutil.copyfile(bak_path, target_path)

    print(f"Injetando armas de ponta e armaduras temáticas: {target_path}...")

    total_weapon_shops = 0
    total_armor_shops = 0
    output_lines = []

    with open(bak_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line_clean = line.strip()
            if not line_clean or line_clean.startswith("//"):
                output_lines.append(line)
                continue

            parts = line_clean.split("\t")
            if len(parts) >= 4 and parts[1] == "shop":
                loc = parts[0]
                map_name = loc.split(",")[0]
                npc_name = parts[2]
                raw_items = parts[3].split(",")
                sprite_id = raw_items[0]
                slot_items = raw_items[1:]

                # Coletar IDs de itens já presentes na loja
                current_item_ids = []
                for s in slot_items:
                    try:
                        current_item_ids.append(int(s.split(":")[0]))
                    except ValueError:
                        pass

                name_low = npc_name.lower()
                is_tool_shop = any(k in name_low for k in ['tool', 'ferramenta', 'utilit', 'sundries', 'collector', 'material', 'chef', 'groomer'])
                is_weapon_shop = not is_tool_shop and (any(k in name_low for k in ['weapon', 'sword', 'axe', 'bow', 'wand', 'blacksmith', 'armas']) or any(1100 <= i <= 1999 for i in current_item_ids))
                is_armor_shop = not is_tool_shop and (any(k in name_low for k in ['armor', 'tailor', 'armadura']) or (any(2100 <= i <= 2799 for i in current_item_ids) and not is_weapon_shop))

                # 1. Loja de Armas: Injetar as 2 armas raras caras (Req 8)
                if is_weapon_shop:
                    category = detect_weapon_category(npc_name, map_name, current_item_ids)
                    top_weapons = TOP_TIER_WEAPONS.get(category, TOP_TIER_WEAPONS['general'])

                    for weapon_id, price in top_weapons:
                        if weapon_id not in current_item_ids:
                            slot_items.append(f"{weapon_id}:{price}")
                            current_item_ids.append(weapon_id)

                    total_weapon_shops += 1

                # 2. Loja de Armaduras: Injetar 1 estoque especial temático da cidade (Req 9)
                elif is_armor_shop:
                    city = detect_city(map_name)
                    armor_id, price = THEMATIC_ARMORS_BY_CITY.get(city, THEMATIC_ARMORS_BY_CITY['default'])

                    if armor_id not in current_item_ids:
                        slot_items.append(f"{armor_id}:{price}")
                        current_item_ids.append(armor_id)

                    total_armor_shops += 1

                new_line = f"{parts[0]}\t{parts[1]}\t{parts[2]}\t{sprite_id}," + ",".join(slot_items) + "\n"
                output_lines.append(new_line)
            else:
                output_lines.append(line)

    with open(target_path, "w", encoding="utf-8") as f:
        f.writelines(output_lines)

    print(f"  [OK] Processado com sucesso: {total_weapon_shops} lojas de armas e {total_armor_shops} lojas de armaduras.")


def main():
    process_shop_file("npc/merchants/shops.txt")
    process_shop_file("npc/pre-re/merchants/shops.txt")
    print("=== Lojas Vanilla-Plus configuradas com sucesso! ===")


if __name__ == "__main__":
    main()

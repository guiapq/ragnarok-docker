#!/usr/bin/env python3
# =============================================================================
# RAGNAROGUE – SOTN Style Shop Randomizer
# Padrão Castlevania SOTN:
#   - Loja de arma vende arma (todas as classes com opções viáveis para low level).
#   - Loja de armadura/equipamento vende armadura e equipamentos correspondentes.
#   - Loja de consumíveis vende consumíveis, ferramentas e munição.
#   - Loja de cacareco/material vende minérios, reagentes e itens de alquimia.
#   - Loja de joia vende gemas, pedras preciosas e anéis.
#   - Preços originais por slot são rigorosamente preservados.
#   - Apenas itens canônicos e limpos de Pre-Renewal (sem caixas de evento,
#     sem tokens de quest como 'Certificado de Missão', sem Unknown Items).
#   - Cidades com identidades e seleções temáticas distintas.
# =============================================================================

import os
import re
import sys
import random
import hashlib

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

# Inicializar seed
seed_str = os.environ.get("WORLD_SEED", env.get("WORLD_SEED", "zawarudo"))
seed_num = os.environ.get("WORLD_SEED_NUMERIC")
if seed_num and seed_num.isdigit():
    seed = int(seed_num)
else:
    seed = int(hashlib.md5(seed_str.encode("utf-8")).hexdigest()[:8], 16)

random.seed(seed)
print(f"=== SOTN Shop Randomizer (Seed: {seed_str} / {seed}) ===")

# Detectar caminhos de diretório
ROOT = env.get("RATHENA_ROOT", "data")
if not os.path.isdir(ROOT) and os.path.isdir("/opt/rathena"):
    ROOT = "/opt/rathena"

# ─────────────────────────────────────────────────────────────────────────────
# CURATED PRE-RE ITEM POOLS (100% canônicos, reconhecíveis e limpos)
# ─────────────────────────────────────────────────────────────────────────────

WEAPONS_STARTER = {
    'dagger': [1201, 1202, 1204, 1207],            # Knife, Cutter, Main Gauche
    'sword_1h': [1101, 1104, 1107],                # Sword, Falchion, Blade
    'sword_2h': [1113, 1151],                      # Two-Handed Sword, Broad Sword
    'bow': [1701, 1704],                           # Bow, Composite Bow
    'staff': [1601, 1604],                         # Rod, Wand
    'mace': [1501, 1504],                          # Club, Mace
    'axe': [1301, 1351],                           # Axe, Battle Axe
    'spear': [1401, 1404],                         # Javelin, Spear
    'katar': [1250, 1251],                         # Jur, Katar
    'knuckle': [1801, 1803],                       # Waghnak, Knuckle Duster
    'book': [1550],                                # Book
    'gun': [13100, 13101],                         # Six Shooter
    'instrument_whip': [1901, 1950]                # Violin, Rope
}

WEAPONS_MID = {
    'dagger': [1210, 1213, 1216, 1219, 1222],      # Dirk, Dagger, Stiletto, Gladius, Damascus
    'sword_1h': [1110, 1116, 1119, 1122, 1126],    # Lapier, Ring Pommel Saber, Haedonggum, Saber, Tsurugi
    'sword_2h': [1154, 1157, 1160, 1162],          # Bastard Sword, Claymore
    'bow': [1707, 1710, 1713, 1716, 1718],         # Great Bow, Crossbow, Arbalest, Gakkung, Hunter Bow
    'staff': [1607, 1610, 1613],                   # Staff, Arc Wand
    'mace': [1507, 1510, 1513, 1516, 1519],        # Smasher, Flail, Morning Star, Sword Mace, Chain
    'axe': [1354, 1357, 1360],                     # Hammer, Buster, Two-Handed Axe
    'spear': [1407, 1410, 1451, 1454, 1457, 1413], # Pike, Partizan, Guisarme, Trident, Halberd, Lance
    'katar': [1252, 1254],                         # Jamadhar
    'knuckle': [1805, 1807],                       # Iron Driver, Fist
    'book': [1551, 1552],                          # Bible, Tablet
    'gun': [13102, 13150, 13152],                  # Crimson Bolt, Rolling Stone, Black Rose
    'instrument_whip': [1903, 1952, 1954]          # Guitar, Whip, Wire Whip
}

ALL_STARTER_WEAPONS = [item for sublist in WEAPONS_STARTER.values() for item in sublist]
ALL_MID_WEAPONS     = [item for sublist in WEAPONS_MID.values() for item in sublist]
ALL_WEAPONS         = ALL_STARTER_WEAPONS + ALL_MID_WEAPONS

ARMORS_BY_SLOT = {
    # Loc 16: Body Armors
    'body_starter': [2301, 2302, 2303, 2305, 2307], # Cotton Shirt, Leather Jacket, Adventurer's Suit, Wooden Mail, Mantle
    'body_mid':     [2309, 2311, 2314, 2316, 2318, 2321, 2328, 2332, 2334], # Coat, Padded Armor, Chain Mail, Plate Mail, Silk Robe, Saint's Robe, Tights, Thief Clothes, Legion Plate
    # Loc 32: Shields
    'shield':       [2101, 2103, 2105, 2107],       # Guard, Buckler, Shield, Mirror Shield
    # Loc 4: Garments
    'garment':      [2501, 2503, 2505],             # Hood, Muffler, Manteau
    # Loc 64: Footwear
    'footgear':     [2401, 2403, 2405],             # Sandals, Shoes, Boots
    # Loc 256/512/etc: Headgears
    'headgear':     [2201, 2203, 2205, 2208, 2211, 2214, 2216, 2226], # Goggles, Glasses, Helm, Circlet, Biretta, Bandana, Ribbon, Hat
    # Accessories
    'accessory':    [2601, 2602, 2603, 2604, 2605, 2607, 2608] # Ring, Necklace, Glove, Brooch, Clip, Rosary, Belt
}

ALL_ARMORS = [item for sublist in ARMORS_BY_SLOT.values() for item in sublist]

CONSUMABLES = {
    'potions':   [501, 502, 503, 504, 505, 506],    # Red, Orange, Yellow, White, Blue, Green Potion
    'utility':   [601, 602, 611, 1065, 645, 656, 657, 523, 525], # Fly Wing, Bwing, Magnifier, Trap, Conc, Awak, Berserk, Holy Water, Panacea
    'food':      [512, 513, 515, 516, 517, 518, 519], # Apple, Banana, Carrot, Potato, Meat, Honey, Milk
    'ammo':      [1750, 1751, 1752, 1753, 13200]   # Arrow, Silver Arrow, Fire Arrow, Iron Arrow, Bullet
}

ALL_CONSUMABLES = [item for sublist in CONSUMABLES.values() for item in sublist]

MATERIALS_CACARECOS = {
    'ores':      [984, 985, 1010, 1011, 998, 999, 1002], # Oridecon, Elunium, Phracon, Emveretarcon, Iron, Steel, Iron Ore
    'gemstones': [715, 716, 717],                        # Yellow, Red, Blue Gemstone
    'crafting':  [713, 714, 7013, 909, 914, 938, 705]   # Empty Bottle, Empty Potion Bottle, Witch Starsand, Jellopy, Fluff, Sticky Mucus, Clover
}

JEWELS_GEMS = [
    720, 721, 722, 726, 728, 729, 730, 731, 732, 733,   # 1C/2C/3C Diamond, Ruby, Sapphire, Opal, Topaz, Zircon, Emerald, Pearl
    2601, 2602, 2603, 2604, 2605, 2607, 2608            # Rings & Jewelry
]

PET_ITEMS = [537, 643, 10013, 10014, 554, 6114, 6113, 6110, 6115, 6100, 6098, 6112, 6104, 6108, 6111]
FOOD_CHEF_ITEMS = [512, 513, 515, 516, 517, 519, 528, 579, 580, 7452, 7453, 7454, 7455, 7456, 7482]

# ─────────────────────────────────────────────────────────────────────────────
# POOLS DE ITENS RAROS / DROPS DE MVP E MONSTROS DIFÍCEIS
# (100% canônicos, validados no item_db.txt pré-RE)
# ─────────────────────────────────────────────────────────────────────────────

RARE_WEAPONS = [
    1474,   # Gae Bolg
    1163,   # Muramasa
    1166,   # Dragon Slayer
    1170,   # Executioner
    1131,   # Ice Falchion
    1132,   # Fireblend (Edge)
    1135,   # Nagan
    1137,   # Excalibur
    1224,   # Ice Pick
    1225,   # Fortune Sword
    1228,   # Moonlight Dagger
    1230,   # Dagger of Counter
    1232,   # Bazerald
    1255,   # Infiltrator
    1261,   # Loki's Nail
    1362,   # Slaughter
    1364,   # Tomahawk
    1365,   # Guillotine
    1414,   # Gungnir
    1417,   # Brionac
    1421,   # Hellfire
    1422,   # Zephyrus
    1472,   # Crescent Scythe
    1522,   # Spike
    1523,   # Golden Mace
    1528,   # Grand Cross
    1554,   # Book of the Apocalypse
    1614,   # Survivor's Rod
    1616,   # Staff of Piercing
    1617,   # Lich's Bone Wand
    1619,   # Wizardry Staff
    1720,   # Rudra Bow
    1722,   # Ballista
    1814,   # Kaiser Knuckle
    1815,   # Berserk
]

RARE_ARMORS = [
    2343,   # Glittering Jacket
    2345,   # Meteor Plate (Flame Spirits Armor)
    2353,   # Valkyrian Armor (Odin's Blessing)
    2347,   # Dragon Vest
    2341,   # Legion Plate
    2325,   # Mink Coat [1]
    2315,   # Chain Mail [1]
    2320,   # Silk Robe [1]
    2108,   # Mirror Shield [1]
    2115,   # Valkyrja's Shield
    2122,   # Platinum Shield
    2123,   # Orleans's Server
    2124,   # Thorny Buckler
    2111,   # Sacred Mission
    2510,   # Morpheus's Shawl
    2511,   # Morrigane's Manteau
    2515,   # Dragon Manteau
    2517,   # Valkyrian Manteau
    2524,   # Wool Scarf
    2411,   # Sprout Shoes
    2412,   # Grave Boots
    2421,   # Valkyrian Shoes
    2423,   # Tidal Shoes
    2425,   # Variant Shoes
    2235,   # Crown
    2236,   # Tiara
    2256,   # Majestic Goat
    2257,   # Spiky Band
    2258,   # Bone Helm
    2259,   # Corsair
    2609,   # Safety Ring
    2610,   # Ring [1]
    2611,   # Earring [1]
    2612,   # Necklace [1]
    2613,   # Glove [1]
    2614,   # Brooch [1]
    2615,   # Clip [1]
    2617,   # Rosary [1]
    2629,   # Morrigane's Belt
    2630,   # Morrigane's Pendant
    2631,   # Morpheus's Ring
]

RARE_CONSUMABLES = [
    607,    # Yggdrasil Berry
    608,    # Yggdrasil Seed
    522,    # Mastela Fruit
    526,    # Royal Jelly
    525,    # Panacea
    545,    # Aloevera
    547,    # Anodyne
    657,    # Berserk Potion
    12103,  # Authoritative Badge
    12016,  # Speed Potion
    12028,  # Abrasive
]

RARE_MATERIALS = [
    984,    # Oridecon
    985,    # Elunium
    969,    # Gold
    999,    # Steel
    722,    # 3-Carat Diamond
    732,    # Emerald
    726,    # Ruby
    728,    # Sapphire
    733,    # Pearl
    1000,   # Star Crumb
    1038,   # Dragon Scale
    1059,   # Fabric
    7013,   # Witch Starsand
]

# Preços de compra fixos para itens raros (múltiplos de 500z)
# Reflete raridade, poder e origem (drop de MVP / boss)
RARE_ITEM_PRICES = {
    # Armas
    1474: 200000, 1163: 150000, 1166: 80000, 1170: 90000,
    1131: 55000,  1132: 55000,  1135: 75000, 1137: 120000,
    1224: 85000,  1225: 70000,  1228: 65000, 1230: 75000,
    1232: 110000, 1255: 90000,  1261: 130000,1362: 75000,
    1364: 80000,  1365: 95000,  1414: 130000,1417: 100000,
    1421: 115000, 1422: 105000, 1472: 85000, 1522: 70000,
    1523: 80000,  1528: 130000, 1554: 140000,1614: 75000,
    1616: 90000,  1617: 150000, 1619: 120000,1720: 180000,
    1722: 95000,  1814: 75000,  1815: 90000,
    # Armaduras
    2343: 120000, 2345: 136000, 2353: 30000, 2347: 100000,
    2341: 110000, 2325: 95000,  2315: 55000, 2320: 50000,
    2108: 60000,  2115: 30000,  2122: 45000, 2123: 40000,
    2124: 50000,  2111: 128000, 2510: 80000, 2511: 90000,
    2515: 85000,  2517: 100000, 2524: 60000, 2411: 35000,
    2412: 40000,  2421: 65000,  2423: 55000, 2425: 70000,
    2235: 90000,  2236: 85000,  2256: 80000, 2257: 70000,
    2258: 75000,  2259: 65000,  2609: 45000, 2610: 40000,
    2611: 35000,  2612: 30000,  2613: 30000, 2614: 35000,
    2615: 35000,  2617: 40000,  2629: 55000, 2630: 60000,
    2631: 65000,
    # Consumíveis
    607: 10000,  608: 6000,   522: 8500,  526: 7000,
    525: 500,    545: 3000,   547: 2500,  657: 5000,
    12103: 3500, 12016: 2500, 12028: 2000,
    # Materiais
    984: 1100,   985: 1100,   969: 200000, 999: 500,
    722: 6000,   732: 5500,   726: 5000,   728: 4000,
    733: 4500,   1000: 5000,  1038: 10000, 1059: 2000,
    7013: 1500,
}

# Faixas de preço aleatório para os 5 slots raros (em unidades de 500z)
# [min_mult, max_mult] → price = randint(min, max) * 500
RARE_PRICE_RANGES = {
    'weapon':     (80,  500),   # 40.000z – 250.000z
    'armor':      (60,  400),   # 30.000z – 200.000z
    'consumable': (4,   60),    # 2.000z  – 30.000z
    'material':   (2,   200),   # 1.000z  – 100.000z
}

def get_rare_pool_for_shop(npc_name, map_name, orig_ids):
    """Detecta o tipo de loja e retorna (pool_name, pool_list)."""
    name_low = npc_name.lower()
    # Pet Groomer / Chef → sem raros temáticos, usar material
    if 'pet groomer' in name_low:
        return 'material', RARE_MATERIALS
    if any(k in name_low for k in ['chef', 'butcher', 'gardener', 'fruit', 'vegetable', 'milk', 'ice cream']):
        return 'consumable', RARE_CONSUMABLES
    if any(k in name_low for k in ['jewel', 'gift', 'doll', 'souvenir', 'flower']):
        return 'material', RARE_MATERIALS
    if any(k in name_low for k in ['material', 'collector', 'trader', 'ore']):
        return 'material', RARE_MATERIALS
    if any(k in name_low for k in ['weapon', 'blacksmith', 'armas', 'sword', 'axe', 'bow', 'wand']):
        return 'weapon', RARE_WEAPONS
    if any(k in name_low for k in ['armor', 'tailor', 'armadura']):
        return 'armor', RARE_ARMORS
    if any(k in name_low for k in ['tool', 'ferramenta', 'utilit', 'sundries']):
        return 'consumable', RARE_CONSUMABLES
    # Fallback: inferir pelo tipo dos itens já na loja
    weapon_ids = sum(1 for i in orig_ids if (1100 <= i <= 1999) or (13100 <= i <= 13199))
    armor_ids  = sum(1 for i in orig_ids if 2100 <= i <= 2799)
    consm_ids  = sum(1 for i in orig_ids if (500 <= i <= 699) or (1750 <= i <= 1799))
    matrl_ids  = sum(1 for i in orig_ids if (700 <= i <= 1099) or (7000 <= i <= 7999))
    best = max(weapon_ids, armor_ids, consm_ids, matrl_ids)
    if best == 0:
        return 'material', RARE_MATERIALS
    if weapon_ids == best:
        return 'weapon', RARE_WEAPONS
    if armor_ids == best:
        return 'armor', RARE_ARMORS
    if consm_ids == best:
        return 'consumable', RARE_CONSUMABLES
    return 'material', RARE_MATERIALS


def pick_rare_slots(pool_name, pool, used_ids, count=5):
    """Escolhe `count` itens únicos do pool e gera preços randomizados (múltiplos de 500z)."""
    min_m, max_m = RARE_PRICE_RANGES[pool_name]
    available = [i for i in pool if i not in used_ids]
    if len(available) < count:
        available = pool  # se não há suficientes, permite repetição
    chosen = random.sample(available, min(count, len(available)))
    slots = []
    for item_id in chosen:
        # Preço base de referência
        if item_id in RARE_ITEM_PRICES:
            base_price = RARE_ITEM_PRICES[item_id]
        else:
            base_price = random.randint(min_m, max_m) * 500
        # Tempero das lojas: preço aleatório por loja variado entre 100% e 140% do base,
        # rigorosamente arredondado para múltiplos de 500z e sempre >= base_price
        # para garantir matematicamente que revenda ao NPC nunca seja vantajosa
        factor = random.choice([1.00, 1.05, 1.10, 1.15, 1.20, 1.25, 1.30, 1.35, 1.40])
        calc_price = round((base_price * factor) / 500) * 500
        price = max(calc_price, base_price, 500)
        # Garantir múltiplo de 500
        if price % 500 != 0:
            price = ((price // 500) + 1) * 500
        slots.append(f"{item_id}:{price}")
    return slots

# ─────────────────────────────────────────────────────────────────────────────
# IDENTIFICAÇÃO DE CATEGORIA POR MAPA / CIDADE
# ─────────────────────────────────────────────────────────────────────────────
CITY_THEMES = {
    'izlude':    ['starter_all', 'sword', 'dagger', 'bow', 'mace', 'staff', 'axe', 'gun'],
    'prontera':  ['sword', 'sword_2h', 'spear', 'mace', 'heavy_armor'],
    'geffen':    ['staff', 'wand', 'dagger', 'magic_armor', 'gemstones'],
    'payon':     ['bow', 'arrows', 'dagger', 'knuckle', 'light_armor'],
    'morroc':    ['dagger', 'katar', 'knuckle', 'sword', 'thief_armor'],
    'alberta':   ['axe', 'mace', 'gun', 'bullets', 'book', 'merchant_armor'],
    'aldebaran': ['spear', 'sword', 'staff', 'alche_materials', 'armor'],
    'comodo':    ['instrument_whip', 'bow', 'dagger', 'light_armor'],
    'einbroch':  ['gun', 'bullets', 'axe', 'mace', 'heavy_armor'],
    'yuno':      ['book', 'staff', 'spear', 'magic_armor'],
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
    return 'generic'

# ─────────────────────────────────────────────────────────────────────────────
# CLASSIFICADOR SOTN DE LOJA E DE SLOT
# ─────────────────────────────────────────────────────────────────────────────

def classify_shop_and_slot(npc_name, map_name, orig_id, orig_price, slot_idx, total_slots):
    name_low = npc_name.lower()
    city = detect_city(map_name)

    # 1. Pet Groomer
    if 'pet groomer' in name_low:
        return random.choice(PET_ITEMS)

    # 2. Chef / Food / Butcher / Gardener
    if any(k in name_low for k in ['chef', 'butcher', 'gardener', 'fruit', 'vegetable', 'milk', 'ice cream']):
        return random.choice(FOOD_CHEF_ITEMS)

    # 3. Joalheria (Jeweler, Gift, Doll, Souvenir)
    if any(k in name_low for k in ['jewel', 'gift', 'doll', 'souvenir', 'flower']):
        return random.choice(JEWELS_GEMS)

    # 4. Cacareco / Materiais / Trader / Collector
    if any(k in name_low for k in ['material', 'collector', 'trader', 'ore']):
        pool = MATERIALS_CACARECOS['ores'] + MATERIALS_CACARECOS['gemstones'] + MATERIALS_CACARECOS['crafting']
        return random.choice(pool)

    # 5. Loja de Armas (Weapon Dealer, One Hand, Two Hand, Blacksmith, etc.)
    if any(k in name_low for k in ['weapon', 'blacksmith', 'armas', 'sword', 'axe', 'bow', 'wand']):
        # Garantia SotN: As primeiras vagas de lojas de armas em cidades principais
        # cobrem as classes básicas low-level para que ninguém fique sem arma!
        starter_keys = ['dagger', 'sword_1h', 'bow', 'staff', 'mace', 'axe', 'spear', 'katar', 'gun', 'book', 'knuckle', 'instrument_whip']
        
        # Se for Izlude ou primeiros slots em outras cidades:
        if city == 'izlude' or (slot_idx < len(starter_keys) and slot_idx < total_slots // 2):
            w_cat = starter_keys[slot_idx % len(starter_keys)]
            return random.choice(WEAPONS_STARTER[w_cat])
        
        # Seleção temática da cidade para mid/high slots
        if city == 'geffen':
            cat = random.choice(['staff', 'staff', 'wand', 'dagger', 'sword_1h'])
        elif city == 'payon':
            cat = random.choice(['bow', 'bow', 'dagger', 'knuckle', 'axe'])
        elif city == 'morroc':
            cat = random.choice(['dagger', 'dagger', 'katar', 'katar', 'knuckle', 'sword_1h'])
        elif city == 'alberta':
            cat = random.choice(['axe', 'axe', 'mace', 'gun', 'book', 'sword_1h'])
        elif city == 'comodo':
            cat = random.choice(['instrument_whip', 'instrument_whip', 'bow', 'dagger'])
        elif city == 'einbroch':
            cat = random.choice(['gun', 'gun', 'axe', 'mace', 'sword_2h'])
        elif city == 'prontera':
            cat = random.choice(['sword_1h', 'sword_2h', 'spear', 'mace', 'axe'])
        else:
            cat = random.choice(list(WEAPONS_MID.keys()))
        
        return random.choice(WEAPONS_MID.get(cat, ALL_MID_WEAPONS))

    # 6. Loja de Armaduras / Equipamentos (Armor Dealer)
    if any(k in name_low for k in ['armor', 'tailor', 'armadura']):
        # Preserva a variedade de slots de armadura
        # Distribui: Corpo, Escudo, Capa, Sapatos, Elmo, Acessório
        slot_mod = slot_idx % 6
        if slot_mod == 0:
            return random.choice(ARMORS_BY_SLOT['body_starter'] if slot_idx < 3 else ARMORS_BY_SLOT['body_mid'])
        elif slot_mod == 1:
            return random.choice(ARMORS_BY_SLOT['shield'])
        elif slot_mod == 2:
            return random.choice(ARMORS_BY_SLOT['garment'])
        elif slot_mod == 3:
            return random.choice(ARMORS_BY_SLOT['footgear'])
        elif slot_mod == 4:
            return random.choice(ARMORS_BY_SLOT['headgear'])
        else:
            return random.choice(ARMORS_BY_SLOT['accessory'])

    # 7. Loja de Ferramentas / Consumíveis (Tool Dealer)
    if any(k in name_low for k in ['tool', 'ferramenta', 'utilit', 'sundries']):
        # Garantir básicos nos primeiros 5 slots: Poção Vermelha, Asa de Mosca, Asa de Borboleta, Lupa, Flecha
        essentials = [501, 601, 602, 611, 1750]
        if slot_idx < len(essentials):
            return essentials[slot_idx]
        
        # Demais slots: consumíveis variados (outras poções, poções de velocidade, armadilhas, balas)
        other_consumables = [502, 503, 504, 505, 506, 645, 656, 1065, 1751, 1752, 13200, 523, 525]
        return random.choice(other_consumables)

    # Fallback inteligente se não reconhecido:
    # Se o item original era arma (ID 1100-1999 ou 13100-13199) -> arma
    if (1100 <= orig_id <= 1999) or (13100 <= orig_id <= 13199):
        return random.choice(ALL_WEAPONS)
    # Se era armadura (ID 2100-2799) -> armadura
    if 2100 <= orig_id <= 2799:
        return random.choice(ALL_ARMORS)
    # Se era consumível (ID 500-699 ou 1750-1799 ou 13200) -> consumível
    if (500 <= orig_id <= 699) or (1750 <= orig_id <= 1799) or orig_id == 13200:
        return random.choice(ALL_CONSUMABLES)

    # Default fallback: material / cacareco limpo
    return random.choice(MATERIALS_CACARECOS['ores'] + MATERIALS_CACARECOS['crafting'])

# ─────────────────────────────────────────────────────────────────────────────
# PROCESSAMENTO DE ARQUIVOS DE LOJAS
# ─────────────────────────────────────────────────────────────────────────────

def process_shop_file(target_rel_path):
    orig_rel_path = target_rel_path + ".original"
    target_path = os.path.join(ROOT, target_rel_path)
    orig_path   = os.path.join(ROOT, orig_rel_path)

    # Se .original não existe, copiar do alvo (ou baixar se for o caso)
    if not os.path.isfile(orig_path):
        if os.path.isfile(target_path):
            import shutil
            shutil.copyfile(target_path, orig_path)
            print(f"  [backup] Criado {orig_path}")
        else:
            print(f"  [WARN] Arquivo {target_path} não encontrado, pulando.")
            return

    print(f"Processando lojas SOTN: {orig_path} -> {target_path}...")

    total_shops = 0
    total_items = 0
    output_lines = []

    with open(orig_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line_clean = line.strip()
            if not line_clean or line_clean.startswith("//"):
                output_lines.append(line)
                continue

            parts = line_clean.split("\t")
            if len(parts) >= 4 and parts[1] == "shop":
                total_shops += 1
                loc = parts[0]
                map_name = loc.split(",")[0]
                npc_name = parts[2]
                raw_items = parts[3].split(",")
                sprite_id = raw_items[0]
                slot_items = raw_items[1:]

                new_slot_items = []
                used_in_shop = set()

                # Coletar IDs originais para inferência de tipo de loja
                orig_ids_for_type = []
                for s in slot_items:
                    try:
                        orig_ids_for_type.append(int(s.split(":")[0]))
                    except ValueError:
                        pass

                for idx, slot in enumerate(slot_items):
                    if ":" in slot:
                        orig_id_str, orig_price = slot.split(":", 1)
                    else:
                        orig_id_str, orig_price = slot, "-1"
                    
                    try:
                        orig_id = int(orig_id_str)
                    except ValueError:
                        orig_id = 0

                    # Tentar até 10 vezes evitar itens repetidos na mesma loja
                    new_item = orig_id
                    for _ in range(10):
                        cand = classify_shop_and_slot(npc_name, map_name, orig_id, orig_price, idx, len(slot_items))
                        if cand not in used_in_shop:
                            new_item = cand
                            break
                        new_item = cand

                    used_in_shop.add(new_item)
                    total_items += 1
                    new_slot_items.append(f"{new_item}:{orig_price}")

                # ── 5 SLOTS RAROS (drop de monstros difíceis / MVP) ──────────
                # Tipo de loja determinado pelo nome do NPC / conteúdo
                pool_name, pool = get_rare_pool_for_shop(npc_name, map_name, orig_ids_for_type)
                rare_slots = pick_rare_slots(pool_name, pool, used_in_shop, count=5)
                new_slot_items.extend(rare_slots)
                total_items += len(rare_slots)
                # ─────────────────────────────────────────────────────────────

                new_line = f"{parts[0]}\t{parts[1]}\t{parts[2]}\t{sprite_id}," + ",".join(new_slot_items) + "\n"
                output_lines.append(new_line)
            else:
                output_lines.append(line)

    with open(target_path, "w", encoding="utf-8") as f:
        f.writelines(output_lines)

    print(f"  [concluído] {total_shops} lojas randomizadas ({total_items} slots).")

# Executar nos arquivos de lojas do pre-renewal e padrão
process_shop_file("npc/merchants/shops.txt")
process_shop_file("npc/pre-re/merchants/shops.txt")

print("")
print("=== Lojas SOTN configuradas com sucesso! ===")
print("- Loja de arma vende arma (todas as classes com starter weapons)")
print("- Loja de armadura vende armaduras / escudos / capas / sapatos / acessórios")
print("- Loja de consumíveis vende poções, asas, lupas e munição")
print("- Loja de cacareco e joia vende minérios, reagentes e pedras preciosas")
print("- Preços originais por slot rigorosamente preservados")

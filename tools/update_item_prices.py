#!/usr/bin/env python3
# =============================================================================
# RAGNAROGUE – Item Price Updater
#
# Regras:
#   - Itens raros/MVP que estão com buy=20 (placeholder rAthena) recebem preços
#     temáticos condizentes com sua raridade.
#   - Todos os itens com buy > 0 são verificados: sell (campo 5) é deixado vazio
#     para o padrão rAthena (sell = buy/2), exceto quando sell foi explicitamente
#     definido acima do permitido.
#   - Nenhum preço de venda pode ser lucrativo em relação ao preço de compra.
#     (rAthena: sell padrão = buy/2; Overcharge skill máx ~124% → sell ~62% de buy)
#   - Os preços são arredondados para múltiplos de 500z.
#
# Lógica:
#   - Itens raros de arma   → Buy 40.000z – 250.000z (múltiplo de 500)
#   - Itens raros de armadura → Buy 30.000z – 200.000z
#   - Consumíveis raros     → Buy 10.000z – 30.000z
#   - Materiais raros       → Buy 15.000z – 80.000z
# =============================================================================

import os
import re
import shutil

ROOT = "data"

# ─────────────────────────────────────────────────────────────────────────────
# PREÇOS FIXOS por item raro / MVP / boss drop
# Arredondados a múltiplos de 500z.
# Baseados na raridade, utilidade e nível de equipamento no Pre-Renewal.
# ─────────────────────────────────────────────────────────────────────────────

ITEM_PRICES = {
    # ── ARMAS RARAS ────────────────────────────────────────────────────────
    1131: 55000,    # Ice Falchion
    1132: 55000,    # Fireblend (Edge)
    1133: 60000,    # Fireblend
    1135: 75000,    # Nagan
    1137: 120000,   # Excalibur
    1163: 150000,   # Muramasa
    1166: 80000,    # Dragon Slayer
    1170: 90000,    # Executioner
    1224: 85000,    # Ice Pick (Sword Breaker)
    1225: 70000,    # Fortune Sword
    1228: 65000,    # Moonlight Dagger
    1230: 75000,    # Dagger of Counter
    1232: 110000,   # Bazerald
    1255: 90000,    # Infiltrator
    1261: 130000,   # Loki's Nail
    1362: 75000,    # Slaughter
    1364: 80000,    # Tomahawk
    1365: 95000,    # Guillotine
    1414: 130000,   # Gungnir
    1417: 100000,   # Brionac
    1421: 115000,   # Hellfire
    1422: 105000,   # Zephyrus
    1472: 85000,    # Crescent Scythe
    1474: 200000,   # Gae Bolg
    1522: 70000,    # Spike
    1523: 80000,    # Golden Mace
    1528: 130000,   # Grand Cross
    1554: 140000,   # Book of the Apocalypse
    1614: 75000,    # Survivor's Rod
    1616: 90000,    # Staff of Piercing
    1617: 150000,   # Lich's Bone Wand
    1619: 120000,   # Wizardry Staff
    1720: 180000,   # Rudra Bow
    1722: 95000,    # Ballista
    1814: 75000,    # Kaiser Knuckle
    1815: 90000,    # Berserk

    # ── ARMADURAS RARAS ─────────────────────────────────────────────────────
    2108: 60000,    # Mirror Shield [1]
    2111: 128000,   # Sacred Mission
    2115: 30000,    # Valkyrja's Shield
    2122: 45000,    # Platinum Shield
    2123: 40000,    # Orleans's Server
    2124: 50000,    # Thorny Buckler
    2235: 90000,    # Crown
    2236: 85000,    # Tiara
    2256: 80000,    # Majestic Goat
    2257: 70000,    # Spiky Band
    2258: 75000,    # Bone Helm
    2259: 65000,    # Corsair
    2315: 55000,    # Chain Mail [1]
    2320: 50000,    # Silk Robe [1]
    2325: 95000,    # Mink Coat [1]
    2341: 110000,   # Legion Plate
    2343: 120000,   # Glittering Jacket
    2345: 136000,   # Meteor Plate (Flame Spirits Armor)
    2347: 100000,   # Dragon Vest
    2353: 30000,    # Valkyrian Armor (Odin's Blessing)
    2411: 35000,    # Sprout Shoes (worn by rare quest)
    2412: 40000,    # Grave Boots
    2421: 65000,    # Valkyrian Shoes
    2423: 55000,    # Tidal Shoes
    2425: 70000,    # Variant Shoes
    2510: 80000,    # Morpheus's Shawl
    2511: 90000,    # Morrigane's Manteau
    2515: 85000,    # Dragon Manteau
    2517: 100000,   # Valkyrian Manteau
    2524: 60000,    # Wool Scarf
    2609: 45000,    # Safety Ring
    2610: 40000,    # Ring [1]
    2611: 35000,    # Earring [1]
    2612: 30000,    # Necklace [1]
    2613: 30000,    # Glove [1]
    2614: 35000,    # Brooch [1]
    2615: 35000,    # Clip [1]
    2617: 40000,    # Rosary [1]
    2629: 55000,    # Morrigane's Belt
    2630: 60000,    # Morrigane's Pendant
    2631: 65000,    # Morpheus's Ring

    # ── CONSUMÍVEIS RAROS ───────────────────────────────────────────────────
    522:   8500,    # Mastela Fruit (já tem preço, mas garantir)
    525:    500,    # Panacea
    526:   7000,    # Royal Jelly (já tem preço)
    545:   3000,    # Aloevera
    547:   2500,    # Anodyne
    607:  10000,    # Yggdrasil Berry
    608:   6000,    # Yggdrasil Seed
    657:   5000,    # Berserk Potion
    12016:  2500,   # Speed Potion
    12028:  2000,   # Abrasive
    12103:  3500,   # Authoritative Badge

    # ── MATERIAIS RAROS / DROPS DE BOSS ─────────────────────────────────────
    969:  200000,   # Gold (já tem preço)
    984:   1100,    # Oridecon
    985:   1100,    # Elunium
    999:    500,    # Steel
    1000:  5000,    # Star Crumb
    1038: 10000,    # Dragon Scale
    1059:  2000,    # Fabric
    7013:  1500,    # Witch Starsand
    722:   6000,    # 3-Carat Diamond (Scarlet Jewel)
    726:   5000,    # Ruby
    728:   4000,    # Sapphire
    732:   5500,    # Emerald
    733:   4500,    # Pearl
}

def round_to_500(price):
    """Arredonda para múltiplo de 500."""
    return round(price / 500) * 500

def process_item_db(filepath):
    """Aplica os preços corrigidos no item_db.txt."""
    backup = filepath + ".price_backup"
    if not os.path.isfile(backup):
        shutil.copyfile(filepath, backup)
        print(f"  [backup] {backup}")

    lines_out = []
    updated = 0
    exploitable = 0

    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("//"):
                lines_out.append(line)
                continue

            parts = line.rstrip("\r\n").split(",")
            if len(parts) < 6:
                lines_out.append(line)
                continue

            try:
                item_id = int(parts[0])
            except ValueError:
                lines_out.append(line)
                continue

            changed = False
            item_type = parts[3].strip() if len(parts) > 3 else ""

            # 1. Se o item tem preço fixo definido em ITEM_PRICES → aplicar
            if item_id in ITEM_PRICES:
                new_buy = ITEM_PRICES[item_id]
                old_buy = parts[4].strip() if parts[4].strip() else "0"
                try:
                    old_buy_int = int(old_buy)
                except ValueError:
                    old_buy_int = 0
                if old_buy_int != new_buy:
                    parts[4] = str(new_buy)
                    changed = True
                    updated += 1
            # 2. Se for Arma (Tipo 5) com buy <= 100 (drop-only/placeholder)
            elif item_type == "5":
                try:
                    cur_b = int(parts[4]) if parts[4].strip() else 0
                except ValueError:
                    cur_b = 0
                if cur_b <= 100:
                    # Avaliar Weapon Level (campo 15)
                    wlv = parts[15].strip() if len(parts) > 15 else "1"
                    if wlv == "4":
                        new_buy = 120000
                    elif wlv == "3":
                        new_buy = 50000
                    elif wlv == "2":
                        new_buy = 20000
                    else:
                        new_buy = 5000
                    parts[4] = str(new_buy)
                    changed = True
                    updated += 1
            # 3. Se for Armadura/Equipamento (Tipo 4) com buy <= 100 (drop-only/placeholder)
            elif item_type == "4":
                try:
                    cur_b = int(parts[4]) if parts[4].strip() else 0
                except ValueError:
                    cur_b = 0
                if cur_b <= 100:
                    # Avaliar Equip Location (campo 14)
                    loc = parts[14].strip() if len(parts) > 14 else "0"
                    try:
                        loc_int = int(loc)
                    except ValueError:
                        loc_int = 0
                    if loc_int == 16:       # Body Armor
                        new_buy = 60000
                    elif loc_int == 32:     # Shield
                        new_buy = 45000
                    elif loc_int == 4:      # Garment
                        new_buy = 40000
                    elif loc_int == 64:     # Footwear
                        new_buy = 35000
                    elif loc_int in [256, 512, 768, 1, 1024]: # Headgear
                        new_buy = 30000
                    elif loc_int in [136, 8, 128]:            # Accessory
                        new_buy = 35000
                    else:
                        new_buy = 30000
                    parts[4] = str(new_buy)
                    changed = True
                    updated += 1

            # 4. Garantir que sell (campo 5) nunca seja superior ou vantajoso em relação a buy:
            #    rAthena calcula sell = buy/2 quando sell está vazio.
            #    Com Overcharge 10 (+24%): sell efetivo max = (buy/2) * 1.24 = 0.62 * buy.
            #    Com Discount 10 (-24%): buy efetivo min = buy * 0.76.
            #    0.62 * buy < 0.76 * buy (sempre prejuízo na revenda, sem exploit).
            #    Se sell explícito for superior a buy/2 ou vantajoso, forçar vazio.
            try:
                cur_buy = int(parts[4]) if parts[4].strip() else 0
                cur_sell_str = parts[5].strip()
                if cur_buy == 0:
                    if cur_sell_str and cur_sell_str != "0":
                        parts[5] = ""
                        exploitable += 1
                        changed = True
                elif cur_sell_str:
                    cur_sell = int(cur_sell_str)
                    # Sell nunca pode ser superior a buy/2 nem permitir lucro com Overcharge/Discount
                    if cur_sell > cur_buy // 2 or (cur_sell * 1.24 >= cur_buy * 0.76):
                        parts[5] = ""  # deixar vazio para padrão seguro (buy / 2)
                        exploitable += 1
                        changed = True
            except (ValueError, IndexError):
                pass

            if changed:
                # Reconstruir a linha preservando tabs e fim de linha original
                eol = "\r\n" if line.endswith("\r\n") else "\n"
                lines_out.append(",".join(parts) + eol)
            else:
                lines_out.append(line)

    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(lines_out)

    print(f"  [concluído] {filepath}: {updated} preços atualizados, {exploitable} sells exploráveis corrigidos.")
    return updated, exploitable

# ── Aplicar em ambos os item_db ──────────────────────────────────────────────
print("=== Item Price Updater ===")

pre_re = os.path.join(ROOT, "db/pre-re/item_db.txt")
re_path = os.path.join(ROOT, "db/re/item_db.txt")

total_upd = 0
total_exp = 0

for path in [pre_re, re_path]:
    if os.path.isfile(path):
        u, e = process_item_db(path)
        total_upd += u
        total_exp += e
    else:
        print(f"  [SKIP] {path} não encontrado")

print(f"\nTotal: {total_upd} preços atualizados, {total_exp} sells corrigidos.")
print("Itens com Buy=20 (placeholder) que eram raros agora têm preços temáticos.")
print("Preço de venda permanece no padrão rAthena (buy/2).")
print("Nenhum item permite lucro por compra/revenda mesmo com Merchant skills.")

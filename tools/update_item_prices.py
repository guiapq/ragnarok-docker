#!/usr/bin/env python3
# =============================================================================
# RAGNAROGUE – Item Price Updater
#
# Regras:
#   - Itens dos Deuses (God Items) têm preço fixo de 10.000.000z (~10kk).
#   - Equipamentos (Tipo 4 e 5) têm seus preços balizados pelo sistema de Tiers:
#       * Tier 1: Itens de loja / drop fácil baratos (< 25.000z)
#       * Tier 2: Intermediários (até 120.000z)
#       * Tier 3: Muito fortes com utilidades e setbacks (até 900.000z)
#       * Tier 4: Topo de linha sem setbacks (1.000.000z a 3.500.000z)
#   - Consumíveis raros e materiais têm preços temáticos de sustentação econômica.
#   - Sell (campo 5) é deixado vazio para o padrão seguro do rAthena (sell = buy/2).
#   - Proteção estrita anti-exploit de revenda (Overcharge/Discount nunca geram lucro).
# =============================================================================

import os
import re
import shutil

ROOT = "data"

GOD_ITEMS = {
    1530: 10000000,   # Mjolnir
    2383: 10000000,   # Brynhild
    2410: 10000000,   # Sleipnir
    2541: 10000000,   # Asprika
    2629: 10000000,   # Megingjard
    2630: 10000000,   # Brisingamen
}

# ─────────────────────────────────────────────────────────────────────────────
# PREÇOS FIXOS PARA CONSUMÍVEIS E MATERIAIS RAROS
# ─────────────────────────────────────────────────────────────────────────────

ITEM_PRICES = {
    # ── GOD ITEMS ──
    **GOD_ITEMS,

    # ── CONSUMÍVEIS RAROS ───────────────────────────────────────────────────
    522:   8500,    # Mastela Fruit
    525:    500,    # Panacea
    526:   7000,    # Royal Jelly
    545:   3000,    # Aloevera
    547:   2500,    # Anodyne
    607:  10000,    # Yggdrasil Berry
    608:   6000,    # Yggdrasil Seed
    657:   5000,    # Berserk Potion
    12016:  2500,   # Speed Potion
    12028:  2000,   # Abrasive
    12103:  3500,   # Authoritative Badge

    # ── MATERIAIS RAROS / DROPS DE BOSS ─────────────────────────────────────
    969:  200000,   # Gold
    984:   1100,    # Oridecon
    985:   1100,    # Elunium
    999:    500,    # Steel
    1000:  5000,    # Star Crumb
    1038: 10000,    # Dragon Scale
    1059:  2000,    # Fabric
    7013:  1500,    # Witch Starsand
    722:   6000,    # 3-Carat Diamond
    726:   5000,    # Ruby
    728:   4000,    # Sapphire
    732:   5500,    # Emerald
    733:   4500,    # Pearl

    # ── ARMAS INICIAIS ACESSÍVEIS (Req 1) ──────────────────────────────────
    1201:    50,    # Knife
    1202:    50,    # Knife [3]
    1204:   100,    # Cutter
    1205:   100,    # Cutter [3]
    1207:   200,    # Main Gauche
    1208:   200,    # Main Gauche [3]
    1101:   150,    # Sword
    1102:   150,    # Sword [3]
    1601:   100,    # Rod
    1602:   100,    # Rod [3]
    1701:   150,    # Bow
    1702:   150,    # Bow [3]
    1301:   150,    # Axe
    1302:   150,    # Axe [3]
    1501:    80,    # Club
    1502:    80,    # Club [3]
    1801:   150,    # Waghnak
    1802:   150,    # Waghnak [3]

    # ── LOOT INICIAL COM VENDA GARANTIDA (Req 1 & 3) ────────────────────────
    909:     40,    # Jellopy (vende por 20z)
    914:     40,    # Fluff (vende por 20z)
    705:     50,    # Clover (vende por 25z)
    938:     60,    # Sticky Mucus (vende por 30z)
    913:     60,    # Chrysalis (vende por 30z)
    915:     50,    # Feather (vende por 25z)
    948:     80,    # Bill of Birds (vende por 40z)

    # ── ARMAS DE PONTA CARAS POR CATEGORIA (Req 8) ─────────────────────────
    1129:  350000,  # Flamberge [0]
    1163:  750000,  # Claymore [0]
    21011: 1800000, # Lâmina Gigante (Giant Blade)
    1182: 1500000,  # Terror Violeta (Violet Fear)
    1180:  850000,  # Espada de Cromo
    1226:  300000,  # Damascus [2]
    1220:  450000,  # Gladius [3]
    1228: 1400000,  # Faca de Combate (Combat Knife)
    1225:  950000,  # Bazerald
    13098: 1100000, # Adaga de Thanos
    1718:  250000,  # Hunter Bow [0]
    1716:  550000,  # Gakkung Bow [2]
    18122: 1800000, # Arco Gigante (Gigantic Bow)
    18110: 1200000, # Besta Grande (Giant Crossbow)
    1734:  750000,  # Falken Blitz
    1611:  250000,  # Arc Wand [2]
    1618:  850000,  # Survivor's Rod [1]
    2023: 1500000,  # Cajado de Thanos de Duas Mãos
    2021: 1200000,  # Ganbantein
    1682:  900000,  # Cajado das Sombras
    1361:  350000,  # Two-Handed Axe [2]
    1357:  250000,  # Buster
    1549: 1600000,  # Pile Bunker
    1382: 1200000,  # Machado Gigante (Giant Axe)
    1356: 1100000,  # Guilhotina
    1523:  600000,  # Golden Mace
    1516:  320000,  # Sword Mace [1]
    16029: 1200000, # Martelo de Thanos
    1528:  950000,  # Grand Cross
    1536: 1100000,  # Nemesis
    1458:  380000,  # Halberd [2]
    1413:  650000,  # Lance [0]
    1484: 1800000,  # Cardo (Carled)
    1490: 1800000,  # Lança Gigante (Gigantic Lance)
    1438: 1200000,  # Lança de Thanos
    1253:  350000,  # Jamadhar [1]
    1255: 1200000,  # Infiltrator
    1280:  850000,  # Chakram
    1278: 1100000,  # Lágrimas Sangrentas
    1275:  800000,  # Katar Perfurante
    13150: 250000,  # Rolling Stone
    13152: 550000,  # Black Rose
    13170: 1200000, # Gate Keeper-DD
    1805:  220000,  # Iron Driver
    1808:  500000,  # Finger [2]
    1836: 1200000,  # Garra de Thanos
    1846:  950000,  # Luva de Batalha de Combo
    1814:  850000,  # Fúria Selvagem
    1904:  280000,  # Guitar [1]
    1958:  420000,  # Chemeti Whip
    1933: 1100000,  # Violino de Thanos
    1988: 1100000,  # Chicote de Thanos
    1940:  950000,  # Concha Musical

    # ── ARMADURAS TEMÁTICAS ESPECIAIS POR CIDADE (Req 9) ───────────────────
    2315:    4000,  # Chain Mail [1] (Prontera)
    2329:    2500,  # Wooden Mail [1] (Izlude)
    2322:    3500,  # Silk Robe [1] (Geffen)
    2331:    5500,  # Tights [1] (Payon)
    2336:    3800,  # Thief Clothes [1] (Morroc)
    2311:    4500,  # Mink Coat (Alberta)
    2326:    5000,  # Saint's Robe [1] (Al De Baran)
    2371:    4200,  # Pantie [1] (Comodo)
    2341:    6500,  # Legion Plate Armor (Einbroch)
    2310:    3200,  # Coat [1] (Yuno)
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

            # 1. Se o item tem preço fixo (God items, consumíveis, materiais)
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
            # 2. Arma com buy <= 100 (drop-only ou placeholder)
            elif item_type == "5":
                try:
                    cur_b = int(parts[4]) if parts[4].strip() else 0
                except ValueError:
                    cur_b = 0
                if cur_b <= 100:
                    wlv = parts[15].strip() if len(parts) > 15 else "1"
                    if wlv == "4":
                        new_buy = 1800000  # Tier 4 (1kk - 3.5kk)
                    elif wlv == "3":
                        new_buy = 450000   # Tier 3 (até 900k)
                    elif wlv == "2":
                        new_buy = 75000    # Tier 2 (até 120k)
                    else:
                        new_buy = 8000     # Tier 1 (< 25k)
                    parts[4] = str(new_buy)
                    changed = True
                    updated += 1
            # 3. Armadura / Equipamento com buy <= 100 (drop-only ou placeholder)
            elif item_type == "4":
                try:
                    cur_b = int(parts[4]) if parts[4].strip() else 0
                except ValueError:
                    cur_b = 0
                if cur_b <= 100:
                    elv = int(parts[16].strip()) if len(parts) > 16 and parts[16].strip().isdigit() else 0
                    def_val = int(parts[8].strip()) if len(parts) > 8 and parts[8].strip().isdigit() else 0

                    if elv >= 32 or def_val >= 8:  # Tier 4 (nível já com redução de 60%)
                        new_buy = 1500000
                    elif elv >= 20 or def_val >= 6:  # Tier 3
                        new_buy = 400000
                    elif elv >= 8 or def_val >= 3:   # Tier 2
                        new_buy = 65000
                    else:
                        new_buy = 12000
                    parts[4] = str(new_buy)
                    changed = True
                    updated += 1

            # 4. Garantir que sell (campo 5) nunca seja superior ou vantajoso em relação a buy:
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
                eol = "\r\n" if line.endswith("\r\n") else "\n"
                lines_out.append(",".join(parts) + eol)
            else:
                lines_out.append(line)

    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(lines_out)

    print(f"  [concluído] {filepath}: {updated} preços atualizados, {exploitable} sells corrigidos.")
    return updated, exploitable


def main():
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
    print("God Items fixados em 10.000.000z (~10kk).")
    print("Preços escalados por Tiers: Lv1 (<25k), Lv2 (até 120k), Lv3 (até 900k), Lv4 (1kk - 3.5kk).")
    print("Nenhum item permite lucro por compra/revenda mesmo com Merchant skills.")


if __name__ == "__main__":
    main()

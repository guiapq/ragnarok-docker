#!/usr/bin/env python3
"""
tools/build_full_gear_set.py

Randomiza determinísticamente TODOS os equipamentos (tipo 4 e 5) do item_db.txt
com base na WORLD_SEED + item_id, obedecendo às regras de balanceamento por Tiers:
- Redução de leveis requeridos em 60% para todos os itens ("all across the board").
- God Items mantêm efeitos vanilla e têm preço ~10kk.
- Bônus e resistências raciais / elementais / de tamanho NUNCA são sobrescritos.
- Tier 1: Mais fracos, sem debuffs, preços baratos de loja / drop fácil (< 25k).
- Tier 2: Mais fortes que Lv1, poucos debuffs leves, preços até 120k.
- Tier 3: Muito fortes, mantêm utilidades vanilla, com setbacks significativos, preços até 900k.
- Tier 4: Extremamente fortes, zero debuffs/setbacks, preços entre 1kk e 3.5kk.
"""

import os
import random
import re
import sys


def load_env():
    env = {}
    if os.path.isfile(".env.rando"):
        with open(".env.rando") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    env[k] = v
    return env


env = load_env()
seed = os.environ.get("WORLD_SEED", env.get("WORLD_SEED", "za2warudo"))
AMPLITUDE = float(env.get("AMPLITUDE", "1.0"))
ROOT = env.get("RATHENA_ROOT", "data")
ITEM_DB_REL = env.get("ITEM_DB_PATH", "db/pre-re/item_db.txt")

SOURCE_DB = os.path.join("data_base", ITEM_DB_REL)
if not os.path.isfile(SOURCE_DB):
    SOURCE_DB = os.path.join(ROOT, ITEM_DB_REL)

TARGET_DB = os.path.join(ROOT, ITEM_DB_REL)

print(f"[RANDO GEAR] Seed: {seed} | Amplitude: x{AMPLITUDE}")
print(f"[RANDO GEAR] Lendo base de: {SOURCE_DB}")
print(f"[RANDO GEAR] Gravando em:   {TARGET_DB}")

# =============================================================================
# CONSTANTES & PALAVRAS-CHAVE
# =============================================================================

# IDs oficiais de Itens dos Deuses (God Items) Pre-Renewal
GOD_ITEM_IDS = {
    1530,  # Mjolnir
    2383,  # Brynhild
    2410,  # Sleipnir
    2541,  # Asprika
    2629,  # Megingjard (Magingiorde)
    2630,  # Brisingamen (Brysinggamen)
}

# Palavras-chave de bônus raciais, elementais, de tamanho e de classe
# que JAMAIS devem ser sobrescritos
RACIAL_KEYWORDS = [
    "bAddRace", "bAddRace2", "bSubRace", "bSubRace2", "bMagicAddRace",
    "bCriticalAddRace", "bExpAddRace", "bSPGainRace", "bSPDrainValueRace", "bComaRace",
    "bAddEle", "bSubEle", "bAtkEle", "bDefEle",
    "bAddSize", "bSubSize", "bNoSizeFix",
    "bAddClass", "bSubClass", "bAddDamageClass", "bIgnoreDefClass", "bIgnoreDefRace",
    "bIgnoreDefRaceRate", "bIgnoreMdefClassRate", "bIgnoreMdefRaceRate", "bDefRatioAtkClass"
]

# Palavras-chave de utilidades especiais vanilla mantidas no Tier 3 e Tier 4
UTILITY_KEYWORDS = [
    "bAutoSpell", "bAutoSpellWhenHit", "autobonus", "skill \"",
    "bUnbreakable", "bNoKnockback", "bNoCastCancel", "bSpeedRate",
    "bSplashRange", "bDoubleRate", "bShortWeaponDamageReturn", "bLongWeaponDamageReturn",
    "bHPDrainRate", "bSPDrainRate", "bHealPower", "bAddMonsterDropItem",
    "bAddMonsterDropItemGroup", "bLongAtkDefRate", "bNearAtkDefRate", "bCriticalLong",
    "bEndure", "bBreakWeaponRate", "bBreakArmorRate"
]

archetypes = {
    "melee": ["bAtk", "bAspdRate", "bCritical", "bStr"],
    "ranged": ["bHit", "bCritical", "bAtk", "bDex"],
    "magic": ["bMatk", "bMaxSP", "bInt"],
    "tank": ["bDef", "bMdef", "bMaxHP", "bVit"],
    "dodge": ["bFlee", "bAgi"],
    "allaround": ["bAllStats", "bMaxHP", "bMaxSP", "bLuk"]
}

# Meta da seed para favorecer certos arquétipos
rng_meta = random.Random(f"{seed}_meta")
arch_list = list(archetypes.keys())
rng_meta.shuffle(arch_list)
favored = arch_list[0]
print(f"[META] Arquétipo favorecido na seed: {favored}")


# =============================================================================
# FUNÇÕES AUXILIARES DE PARSING
# =============================================================================

def extract_first_script(line):
    """
    Separa a linha do item_db.txt em:
    - before_script: cabeçalho CSV antes do primeiro '{'
    - vanilla_script: conteúdo interno do primeiro script (Equip Script), respeitando blocos aninhados e aspas
    - after_script: restante da linha após o fechamento do primeiro script (ex: ',{},{}')
    """
    idx = line.find("{")
    if idx == -1:
        return line.rstrip("\r\n"), "", ",{},{}"

    before_script = line[:idx]

    depth = 0
    in_quote = False
    quote_char = ""
    in_comment_c = False
    script_start = idx + 1
    script_end = -1

    i = idx
    while i < len(line):
        if not in_quote and not in_comment_c and line[i:i+2] == "/*":
            in_comment_c = True
            i += 2
            continue
        if in_comment_c:
            if line[i:i+2] == "*/":
                in_comment_c = False
                i += 2
            else:
                i += 1
            continue
        if not in_quote and line[i:i+2] == "//":
            break

        ch = line[i]
        if in_quote:
            if ch == "\\" and i + 1 < len(line):
                i += 2
                continue
            elif ch == quote_char:
                in_quote = False
            i += 1
            continue
        if ch in ("\"", "'"):
            in_quote = True
            quote_char = ch
            i += 1
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                script_end = i
                break
        i += 1

    if script_end != -1:
        vanilla_script = line[script_start:script_end].strip()
        after_script = line[script_end + 1:].rstrip("\r\n")
    else:
        vanilla_script = line[script_start:].strip()
        after_script = ",{},{}"

    return before_script, vanilla_script, after_script


def clean_script_comments(script):
    """Remove comentários C (/* ... */) e de linha (// ...) de scripts."""
    s = re.sub(r"/\*.*?\*/", " ", script, flags=re.DOTALL)
    s = re.sub(r"//[^\r\n]*", " ", s)
    return s


def split_script_statements(script):
    """Divide um script rAthena em declarações, respeitando blocos aninhados { ... } e if-else."""
    script = clean_script_comments(script)
    statements = []
    current = []
    depth = 0
    in_quote = False
    quote_char = ""
    i = 0
    while i < len(script):
        ch = script[i]
        if in_quote:
            current.append(ch)
            if ch == "\\" and i + 1 < len(script):
                i += 1
                current.append(script[i])
            elif ch == quote_char:
                in_quote = False
            i += 1
            continue
        if ch in ("\"", "'"):
            in_quote = True
            quote_char = ch
            current.append(ch)
            i += 1
            continue
        if ch == "{":
            depth += 1
            current.append(ch)
        elif ch == "}":
            depth -= 1
            current.append(ch)
            if depth == 0:
                rest_ahead = script[i + 1:].lstrip()
                if rest_ahead.startswith("else"):
                    # Não encerra o comando se houver 'else' na sequência imediata
                    pass
                else:
                    stmt = "".join(current).strip()
                    if stmt:
                        statements.append(stmt)
                    current = []
        elif ch == ";":
            if depth == 0:
                current.append(ch)
                stmt = "".join(current).strip()
                if stmt:
                    statements.append(stmt)
                current = []
            else:
                current.append(ch)
        else:
            current.append(ch)
        i += 1
    tail = "".join(current).strip()
    if tail:
        statements.append(tail)
    return statements


def extract_preserved_statements(script, tier):
    """
    Extrai do script vanilla:
    1. Efeitos raciais, elementais, tamanho e classe (SEMPRE preservados em todos os tiers).
    2. Utilidades vanilla especiais (preservadas no Tier 3 e Tier 4).
    """
    if not script:
        return [], []
    stmts = split_script_statements(script)
    racial = []
    utility = []
    for s in stmts:
        is_racial = any(k in s for k in RACIAL_KEYWORDS)
        if is_racial:
            racial.append(s)
            continue
        if tier in (3, 4):
            is_util = any(k in s for k in UTILITY_KEYWORDS)
            if is_util:
                utility.append(s)
    return racial, utility


def scale_elv(elv_str):
    """Reduz o nível requerido em 60% (fica 40% do original, mín 1)."""
    if not elv_str or not elv_str.strip():
        return elv_str
    try:
        val = int(elv_str.strip())
        if val <= 0:
            return elv_str
        new_val = max(1, int(round(val * 0.4)))
        return str(new_val)
    except ValueError:
        return elv_str


def get_item_tier(item_id, item_type, orig_buy, def_val, orig_elv, wlv):
    """Determina o Tier (1, 2, 3, 4 ou GOD) do equipamento."""
    if item_id in GOD_ITEM_IDS:
        return "GOD"
    if item_type == 5:
        # Arma: nível da arma (wLV) define o tier
        if wlv >= 4:
            return 4
        elif wlv == 3:
            return 3
        elif wlv == 2:
            return 2
        else:
            return 1
    else:
        # Armadura / Equipamento (Tipo 4)
        if orig_elv >= 80 or (orig_elv >= 70 and def_val >= 8):
            return 4
        elif orig_elv >= 50 or def_val >= 6 or orig_buy >= 40000:
            return 3
        elif orig_elv >= 20 or def_val >= 3 or orig_buy >= 10000:
            return 2
        else:
            return 1


# =============================================================================
# GERAÇÃO PROCEDURAL POR TIER
# =============================================================================

def generate_tier_stats_and_price(item_id, item_type, tier, orig_buy, vanilla_script, rng):
    """
    Gera o script e preço de acordo com as regras de acessibilidade e tiers.
    """
    # 1. GOD ITEMS: Efeitos vanilla, preço ~10kk
    if tier == "GOD":
        buy_price = 10000000
        # Preserva script vanilla intacto
        return vanilla_script, buy_price

    # Extrai efeitos raciais (obrigatórios) e utilidades vanilla (Tier 3/4)
    preserved_racial, preserved_utility = extract_preserved_statements(vanilla_script, tier)

    # Escolha de atributos preferidos
    if item_type == 5:
        pref = ["bAtk", "bMatk", "bAspdRate", "bCritical", "bHit", "bStr", "bDex", "bInt"]
    else:
        pref = ["bDef", "bMdef", "bMaxHP", "bMaxSP", "bFlee", "bVit", "bAgi", "bLuk", "bAllStats"]

    # Mescla com arquétipo favorecido
    pool = pref + archetypes[favored]

    bonuses = []
    chosen = set()

    # =========================================================================
    # TIER 1: Mais fracos, sem debuffs, preços baratos (< 25k)
    # =========================================================================
    if tier == 1:
        num_bonuses = rng.randint(2, 3)
        for _ in range(num_bonuses):
            avail = [s for s in pool if s not in chosen]
            stat = rng.choice(avail if avail else pool)
            chosen.add(stat)

            if stat in ("bStr", "bAgi", "bVit", "bInt", "bDex", "bLuk"):
                val = rng.randint(1, 3)
            elif stat == "bAllStats":
                val = 1
            elif stat in ("bAtk", "bMatk"):
                val = rng.randint(5, 15)
            elif stat in ("bDef", "bMdef"):
                val = rng.randint(1, 4)
            elif stat in ("bHit", "bFlee"):
                val = rng.randint(4, 10)
            elif stat == "bCritical":
                val = rng.randint(2, 4)
            elif stat == "bAspdRate":
                val = rng.randint(1, 3)
            elif stat == "bMaxHP":
                val = rng.randint(30, 80)
            elif stat == "bMaxSP":
                val = rng.randint(15, 40)
            else:
                val = rng.randint(2, 6)

            val = max(1, int(val * AMPLITUDE))
            bonuses.append(f"bonus {stat},{val};")

        # Sem debuffs em Tier 1!
        # Preço barato de loja / drop fácil: 2.500z a 22.000z
        base_p = 3000 + rng.randint(0, 8) * 2000
        buy_price = round(base_p / 500) * 500
        if 0 < orig_buy <= 25000:
            buy_price = min(buy_price, orig_buy)
        buy_price = max(1500, min(buy_price, 24500))

    # =========================================================================
    # TIER 2: Mais fortes que Lv1, poucos debuffs leves, até 120k
    # =========================================================================
    elif tier == 2:
        num_bonuses = rng.randint(3, 4)
        for _ in range(num_bonuses):
            avail = [s for s in pool if s not in chosen]
            stat = rng.choice(avail if avail else pool)
            chosen.add(stat)

            if stat in ("bStr", "bAgi", "bVit", "bInt", "bDex", "bLuk"):
                val = rng.randint(3, 6)
            elif stat == "bAllStats":
                val = rng.randint(1, 2)
            elif stat in ("bAtk", "bMatk"):
                val = rng.randint(15, 35)
            elif stat in ("bDef", "bMdef"):
                val = rng.randint(3, 8)
            elif stat in ("bHit", "bFlee"):
                val = rng.randint(10, 20)
            elif stat == "bCritical":
                val = rng.randint(4, 8)
            elif stat == "bAspdRate":
                val = rng.randint(3, 6)
            elif stat == "bMaxHP":
                val = rng.randint(80, 200)
            elif stat == "bMaxSP":
                val = rng.randint(40, 90)
            else:
                val = rng.randint(6, 12)

            val = max(1, int(val * AMPLITUDE))
            bonuses.append(f"bonus {stat},{val};")

        # Poucos debuffs (25% chance de 1 debuff leve)
        if rng.random() < 0.25:
            d_stat = rng.choice(["bDef", "bMdef", "bFlee", "bMaxHP", "bMaxSP"])
            if d_stat == "bMaxHP":
                d_val = int(rng.randint(30, 80) * AMPLITUDE)
            elif d_stat == "bMaxSP":
                d_val = int(rng.randint(20, 40) * AMPLITUDE)
            elif d_stat in ("bDef", "bMdef"):
                d_val = int(rng.randint(2, 5) * AMPLITUDE)
            else:
                d_val = int(rng.randint(5, 12) * AMPLITUDE)
            bonuses.append(f"bonus {d_stat},-{d_val};")

        # Preço Tier 2: 30.000z a 120.000z
        p_raw = 30000 + rng.randint(0, 18) * 5000
        buy_price = round(p_raw / 500) * 500
        buy_price = max(30000, min(buy_price, 120000))

    # =========================================================================
    # TIER 3: Muito fortes, mantêm utilidades vanilla, com SETBACKS SIGNIFICATIVOS, até 900k
    # =========================================================================
    elif tier == 3:
        num_bonuses = rng.randint(4, 5)
        for _ in range(num_bonuses):
            avail = [s for s in pool if s not in chosen]
            stat = rng.choice(avail if avail else pool)
            chosen.add(stat)

            if stat in ("bStr", "bAgi", "bVit", "bInt", "bDex", "bLuk"):
                val = rng.randint(6, 12)
            elif stat == "bAllStats":
                val = rng.randint(2, 4)
            elif stat in ("bAtk", "bMatk"):
                val = rng.randint(35, 70)
            elif stat in ("bDef", "bMdef"):
                val = rng.randint(8, 16)
            elif stat in ("bHit", "bFlee"):
                val = rng.randint(20, 35)
            elif stat == "bCritical":
                val = rng.randint(8, 14)
            elif stat == "bAspdRate":
                val = rng.randint(5, 9)
            elif stat == "bMaxHP":
                val = rng.randint(200, 500)
            elif stat == "bMaxSP":
                val = rng.randint(80, 200)
            else:
                val = rng.randint(12, 25)

            val = max(1, int(val * AMPLITUDE))
            bonuses.append(f"bonus {stat},{val};")

        # Setbacks Significativos OBRIGATÓRIOS (1 a 2 setbacks de grande impacto)
        num_setbacks = rng.randint(1, 2)
        setback_pool = ["bDef", "bMdef", "bMaxHP", "bMaxSP", "bFlee", "bHit", "bAspdRate", "bUseSPrate"]
        rng.shuffle(setback_pool)
        for d_stat in setback_pool[:num_setbacks]:
            if d_stat == "bMaxHP":
                d_val = int(rng.randint(150, 400) * AMPLITUDE)
                bonuses.append(f"bonus {d_stat},-{d_val};")
            elif d_stat == "bMaxSP":
                d_val = int(rng.randint(80, 180) * AMPLITUDE)
                bonuses.append(f"bonus {d_stat},-{d_val};")
            elif d_stat == "bDef":
                d_val = int(rng.randint(8, 18) * AMPLITUDE)
                bonuses.append(f"bonus {d_stat},-{d_val};")
            elif d_stat == "bMdef":
                d_val = int(rng.randint(8, 16) * AMPLITUDE)
                bonuses.append(f"bonus {d_stat},-{d_val};")
            elif d_stat == "bFlee":
                d_val = int(rng.randint(15, 30) * AMPLITUDE)
                bonuses.append(f"bonus {d_stat},-{d_val};")
            elif d_stat == "bHit":
                d_val = int(rng.randint(15, 25) * AMPLITUDE)
                bonuses.append(f"bonus {d_stat},-{d_val};")
            elif d_stat == "bAspdRate":
                d_val = int(rng.randint(4, 8) * AMPLITUDE)
                bonuses.append(f"bonus {d_stat},-{d_val};")
            elif d_stat == "bUseSPrate":
                d_val = int(rng.randint(15, 30) * AMPLITUDE)
                bonuses.append(f"bonus {d_stat},{d_val};")  # Aumento positivo no consumo de SP

        # Preço Tier 3: até 900k a depender da utilidade
        base_p = 250000 + rng.randint(0, 10) * 35000  # 250k - 600k
        if preserved_utility:
            base_p += 150000 + len(preserved_utility) * 50000
        buy_price = round(base_p / 500) * 500
        buy_price = max(200000, min(buy_price, 900000))

    # =========================================================================
    # TIER 4: Elite / Relíquia, ZERO SETBACKS, entre 1kk e 3.5kk
    # =========================================================================
    elif tier == 4:
        num_bonuses = rng.randint(4, 6)
        for _ in range(num_bonuses):
            avail = [s for s in pool if s not in chosen]
            stat = rng.choice(avail if avail else pool)
            chosen.add(stat)

            if stat in ("bStr", "bAgi", "bVit", "bInt", "bDex", "bLuk"):
                val = rng.randint(8, 16)
            elif stat == "bAllStats":
                val = rng.randint(3, 6)
            elif stat in ("bAtk", "bMatk"):
                val = rng.randint(50, 100)
            elif stat in ("bDef", "bMdef"):
                val = rng.randint(12, 24)
            elif stat in ("bHit", "bFlee"):
                val = rng.randint(25, 50)
            elif stat == "bCritical":
                val = rng.randint(10, 18)
            elif stat == "bAspdRate":
                val = rng.randint(7, 12)
            elif stat == "bMaxHP":
                val = rng.randint(400, 800)
            elif stat == "bMaxSP":
                val = rng.randint(150, 350)
            else:
                val = rng.randint(20, 40)

            val = max(1, int(val * AMPLITUDE))
            bonuses.append(f"bonus {stat},{val};")

        # ZERO SETBACKS em Tier 4 ("itens lv4 nao tem setbacks")!
        # Preço entre 1kk e 3.5kk (1.000.000z a 3.500.000z)
        p_raw = 1000000 + rng.randint(0, 50) * 50000
        buy_price = round(p_raw / 500) * 500
        buy_price = max(1000000, min(buy_price, 3500000))

    # Combina script vanilla/original + bônus procedurais de forma estritamente cumulativa
    if vanilla_script and vanilla_script.strip():
        final_stmts = [vanilla_script.strip()] + bonuses
    else:
        final_stmts = preserved_racial + preserved_utility + bonuses
    script_str = " ".join(final_stmts).strip()

    return script_str, buy_price


# =============================================================================
# PIPELINE PRINCIPAL
# =============================================================================

def main():
    lines = []
    gear_count = 0
    total_count = 0
    scaled_elv_count = 0
    tier_counts = {1: 0, 2: 0, 3: 0, 4: 0, "GOD": 0}

    with open(SOURCE_DB, "r", encoding="latin-1") as f:
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith("//"):
                lines.append(line)
                continue

            total_count += 1

            # Separa script e cabeçalho com parser robusto
            before_script, vanilla_script, after_script = extract_first_script(line)

            cols = [c.strip() for c in before_script.split(",")]
            try:
                item_id = int(cols[0])
                item_type = int(cols[3])
            except (ValueError, IndexError):
                lines.append(line)
                continue

            # Nível Requerido (campo 16): diminuir em 60% ("all abroad")
            orig_elv = 0
            if len(cols) > 16 and cols[16].strip():
                try:
                    orig_elv = int(cols[16].strip())
                    new_elv = scale_elv(cols[16])
                    if new_elv != cols[16]:
                        scaled_elv_count += 1
                        cols[16] = new_elv
                except ValueError:
                    pass

            # Preço original e DEF original para classificação
            orig_buy = 0
            if len(cols) > 4 and cols[4].strip():
                try:
                    orig_buy = int(cols[4].strip())
                except ValueError:
                    pass

            def_val = 0
            if len(cols) > 8 and cols[8].strip():
                try:
                    def_val = int(cols[8].strip())
                except ValueError:
                    pass

            wlv = 1
            if len(cols) > 15 and cols[15].strip():
                try:
                    wlv = int(cols[15].strip())
                except ValueError:
                    pass

            # Processa equipamentos (Tipo 4 e Tipo 5)
            if item_type in (4, 5):
                rng = random.Random(f"{seed}_{item_id}")
                tier = get_item_tier(item_id, item_type, orig_buy, def_val, orig_elv, wlv)
                tier_counts[tier] += 1

                new_script, new_buy = generate_tier_stats_and_price(
                    item_id, item_type, tier, orig_buy, vanilla_script, rng
                )

                # Atualiza Buy (campo 4) e esvazia Sell (campo 5) para sell = buy/2 seguro
                cols[4] = str(new_buy)
                if len(cols) > 5:
                    cols[5] = ""

                # Reconstrói a linha com cabeçalho atualizado e novo script
                new_before = ",".join(cols)
                script_body = f" {new_script} " if new_script else ""
                new_line = f"{new_before}{{{script_body}}}{after_script}\n"
                lines.append(new_line)
                gear_count += 1
            else:
                # Não é equipamento, mas pode ter tido eLV reduzido
                new_before = ",".join(cols)
                if new_before != before_script:
                    new_line = f"{new_before}{line[len(before_script):]}"
                    lines.append(new_line)
                else:
                    lines.append(line)

    os.makedirs(os.path.dirname(TARGET_DB), exist_ok=True)
    with open(TARGET_DB, "w", encoding="latin-1") as f:
        f.writelines(lines)

    print(f"[OK] Randomização Global Concluída!")
    print(f"Total de itens no item_db: {total_count}")
    print(f"Itens com Nível Requerido (eLV) reduzido em 60%: {scaled_elv_count}")
    print(f"Equipamentos gerados por Tier: {tier_counts}")
    print(f"Total de equipamentos balanceados: {gear_count}")


if __name__ == "__main__":
    main()

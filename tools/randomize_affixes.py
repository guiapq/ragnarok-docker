#!/usr/bin/env python3
"""
tools/randomize_affixes.py

Aplica afixos procedurais aos equipamentos com base estrita no balanceamento Pre-Renewal:
  - DEF e MDEF: Em Pre-RE, DEF é redução % direta. Armas NÃO recebem bônus de DEF (ou máx 5).
    MDEF total é rigorosamente limitado a 15 no máximo.
  - Reduções elementais balanceadas até 20% e Reduções de neutro balanceadas até 12%.
  - Comportamento temático por slot:
      * Armaduras (loc 16): Pontos defensivos (Hard DEF máx 5, Vit, MaxHP, Reduções elementais, autocast on-hit).
      * Sapatos (loc 64): Sobrevivência e ataque (MaxHP, MaxSP, Atk, Agi, AspdRate, Flee).
      * Capas (loc 4): Defensivas (Flee, Redução Neutro até 12%, Redução Elemental até 20%, MDEF).
      * Escudos (loc 32): Defesa pura (DEF máx 4, MDEF máx 6, Reduções).
      * Acessórios (loc 136, 8, 128): Habilidades ativas e pontos brutos nos atributos até +5 no limite.
      * Cabeça (loc 256, 512, 1): Status moderados (+1..+3), MDEF (+1..+5), MaxHP/SP.
      * Qualquer equipamento pode dar +allstats, limitado ao máximo de +3.
  - Autocasts: Defensivos ao receber dano (on-hit) e ofensivos ao atacar (on-attack) entre Lv 2 e Lv 5.
  - Armas: 20% das armas recebem elemento aleatório associado.
  - Curva de Bell (Gaussiana) em 4 Tiers:
      * Tier 0: Ruim / Defeituosa (~15%)
      * Tier 1: Medíocre / Comum (~50%)
      * Tier 2: Boa / Rara (~25%)
      * Tier 3: Ótima / Primorosa (~10%)
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


env = load_env()
ROOT = env.get("RATHENA_ROOT", "data")
ITEM_DB = env.get("ITEM_DB_PATH", "db/pre-re/item_db.txt")
DB = os.path.join(ROOT, ITEM_DB)

seed = int(os.environ.get("WORLD_SEED_NUMERIC", 0))
random.seed(seed)

print(f"=== Pre-RE Equipment Affixes Engine (Bell Curve | Seed: {seed}) ===")


def get_bell_curve_tier():
    """
    Curva de Gauss calibrada:
      < 32   -> Tier 0 (Ruim)      ~ 15.5%
      32..57 -> Tier 1 (Medíocre)  ~ 50.0%
      58..73 -> Tier 2 (Boa)       ~ 24.5%
      >= 74  -> Tier 3 (Ótima)     ~ 10.0%
    """
    roll = random.gauss(50, 18)
    if roll < 32:
        return 0
    elif roll < 58:
        return 1
    elif roll < 74:
        return 2
    else:
        return 3


# ─────────────────────────────────────────────────────────────────────────────
# 1. GERADOR DE ARMAS (Tipo 4)
# ─────────────────────────────────────────────────────────────────────────────
def generate_weapon_affixes(tier):
    bonuses = []

    # 20% de chance de elemento associado na arma
    has_element = random.random() < 0.20
    if has_element:
        elem = random.choices(
            ["Ele_Fire", "Ele_Water", "Ele_Wind", "Ele_Earth", "Ele_Holy", "Ele_Dark", "Ele_Ghost"],
            weights=[25, 25, 25, 20, 2, 2, 1]
        )[0]
        bonuses.append(f"bonus bAtkEle,{elem};")

    if tier == 0:
        # Ruim / Defeituosa (15%): Drawbacks ou bônus irrisórios (Sem DEF)
        flaws = [
            ["bonus bAtk,2;", "bonus bHit,-3;"],
            ["bonus bAtk,3;", "bonus bCritical,-2;"],
            ["bonus bAtk,1;"],
            ["bonus bHit,2;", "bonus bFlee,-2;"],
            ["bonus bAtk,2;", "bonus bAgi,-1;"],
            ["bonus bHit,3;", "bonus bLuk,-2;"],
            ["bonus bAtk,1;", "bonus bStr,-1;"]
        ]
        bonuses.extend(random.choice(flaws))

    elif tier == 1:
        # Medíocre / Comum (50%): Atk moderado, Hit, Atributo +1..+2
        num_affixes = random.choice([1, 2])
        pool = [
            f"bonus bAtk,{random.randint(5, 10)};",
            f"bonus bHit,{random.randint(5, 12)};",
            f"bonus bCritical,{random.randint(2, 4)};",
            f"bonus bStr,{random.randint(1, 2)};",
            f"bonus bAgi,{random.randint(1, 2)};",
            f"bonus bDex,{random.randint(1, 2)};",
            f"bonus bFlee,{random.randint(3, 6)};",
        ]
        bonuses.extend(random.sample(pool, min(num_affixes, len(pool))))

    elif tier == 2:
        # Boa / Rara (25%): Atk expressivo, AspdRate, Autocast ofensivo Lv 2..3
        num_affixes = random.choice([2, 3])
        pool = [
            f"bonus bAtk,{random.randint(14, 24)};",
            f"bonus bHit,{random.randint(12, 20)};",
            f"bonus bCritical,{random.randint(5, 8)};",
            f"bonus bStr,{random.randint(3, 5)};",
            f"bonus bAgi,{random.randint(3, 5)};",
            f"bonus bDex,{random.randint(3, 5)};",
            f"bonus bAspdRate,{random.randint(3, 5)};",
            f"bonus bFlee,{random.randint(6, 12)};",
        ]
        # 30% de chance de autocast ofensivo Lv 2..3
        if random.random() < 0.30:
            skill = random.choice(["MG_FIREBOLT", "MG_COLDBOLT", "MG_LIGHTNINGBOLT", "SM_BASH", "TF_DOUBLE"])
            slv = random.randint(2, 3)
            rate = random.randint(30, 50)  # 3% a 5%
            pool.append(f'bonus3 bAutoSpell,"{skill}",{slv},{rate};')

        bonuses.extend(random.sample(pool, min(num_affixes, len(pool))))

    else:
        # Ótima / Primorosa (10%): Tiers altos
        # Efeito Cômico / Quebra de Regra nos Tiers Altos (15% de chance)
        if random.random() < 0.15:
            comic_weapon_rolls = [
                # Casca-grossa: arma que quebra a regra e dá DEF e MDEF pesadas!
                "bonus bDef,8; bonus bMdef,8; bonus bAtk,20;",
                # Faca do Sonic: velocidade de movimento insana!
                "bonus bSpeedRate,35; bonus bAspdRate,12; bonus bAtk,25;",
                # Arma Barulhenta: grita a cada ataque!
                'bonus bAtk,38; bonus3 bAutoSpell,"MC_LOUD",1,100; bonus bStr,5;',
                # Arma Provocadora: provoca monstros continuamente!
                'bonus bAtk,28; bonus3 bAutoSpell,"SM_PROVOKE",5,80; bonus bHit,25;',
                # Apostador Insano: sorte e crítico absurdos!
                "bonus bLuk,30; bonus bCritical,25; bonus bCritAtkRate,25;",
                # Fúria Arcana: chuva de meteoros no melee!
                'bonus bMatkRate,20; bonus3 bAutoSpell,"WZ_METEOR",2,30; bonus bInt,4;',
            ]
            bonuses.append(random.choice(comic_weapon_rolls))
            return " ".join(bonuses)

        # Ótima / Primorosa padrão: Atk elevado, AllStats até +3, Dano Crítico, Autocast Lv 3..5
        num_affixes = random.choice([2, 3])
        pool = [
            f"bonus bAtk,{random.randint(26, 42)};",
            f"bonus bAllStats,{random.randint(2, 3)};",  # Limitado a no máximo +3
            f"bonus bAspdRate,{random.randint(5, 8)};",
            f"bonus bCritical,{random.randint(8, 14)};",
            f"bonus bCritAtkRate,{random.randint(10, 18)};",
            f"bonus bHit,{random.randint(20, 30)};",
            f"bonus bFlee,{random.randint(12, 20)};",
        ]
        # 50% de chance de autocast ofensivo Lv 3..5
        if random.random() < 0.50:
            skill = random.choice(["MG_FIREBOLT", "MG_COLDBOLT", "MG_LIGHTNINGBOLT", "SM_BASH", "MC_MAMMONITE", "TF_DOUBLE"])
            slv = random.randint(3, 5)
            rate = random.randint(30, 50)
            pool.append(f'bonus3 bAutoSpell,"{skill}",{slv},{rate};')

        bonuses.extend(random.sample(pool, min(num_affixes, len(pool))))

    return " ".join(bonuses)


# ─────────────────────────────────────────────────────────────────────────────
# 2. GERADOR DE ARMADURAS E EQUIPAMENTOS POR SLOT (Tipo 5)
# ─────────────────────────────────────────────────────────────────────────────
def generate_armor_affixes_by_slot(loc, tier):
    bonuses = []

    # Efeito Cômico / Quebra de Regra nos Tiers Altos (Tier 3 - 15% de chance)
    if tier == 3 and random.random() < 0.15:
        if loc & 64:  # Sapatos: Foguete de Hermes
            return "bonus bSpeedRate,40; bonus bFlee,25; bonus bDef,-6;"
        elif loc & 4:  # Capa: Gravitacional (quebra teto de 12% neutro com 25% de redução!)
            return "bonus2 bSubEle,Ele_Neutral,25; bonus bFlee,-20; bonus bDef,3;"
        elif loc & 16:  # Armadura: Escandalosa (grita histericamente a cada golpe)
            return 'bonus3 bAutoSpellWhenHit,"MC_LOUD",1,100; bonus bDef,6; bonus bMaxHP,1500;'
        elif loc & 32:  # Escudo: Espelho Arcano (quebra teto de 15 MDEF com 22!)
            return "bonus bMdef,22; bonus bDef,5; bonus2 bSubEle,Ele_Fire,25;"
        elif loc & 8 or loc & 128 or loc == 136:  # Acessório: Grandeza Cômica (AllStats +5)
            return "bonus bAllStats,5; bonus bMaxHP,600; bonus bMaxSP,120;"
        else:  # Cabeça: Capacete Provocador
            return 'bonus3 bAutoSpellWhenHit,"SM_PROVOKE",5,50; bonus bAllStats,4; bonus bMaxHP,800;'

    # ── A. ARMADURA DE CORPO (loc 16) ─────────────────────────────────────────
    # Foco: Pontos defensivos (DEF máx 5, Vit, MaxHP, Reduções elementais até 20%, Autocast on-hit)
    if loc & 16:
        if tier == 0:
            flaws = [
                ["bonus bDef,1;", "bonus bMdef,-2;"],
                ["bonus bMaxHP,50;"],
                ["bonus bVit,-1;", "bonus bDef,1;"],
                ["bonus bDef,1;"]
            ]
            bonuses = random.choice(flaws)
        elif tier == 1:
            pool = [
                f"bonus bDef,{random.randint(1, 2)};",
                f"bonus bVit,{random.randint(1, 2)};",
                f"bonus bMaxHP,{random.randint(120, 280)};",
                f"bonus bMdef,{random.randint(1, 3)};",
                f"bonus2 bSubEle,{random.choice(['Ele_Fire', 'Ele_Water', 'Ele_Wind', 'Ele_Earth'])},{random.randint(5, 8)};",
            ]
            bonuses = random.sample(pool, random.choice([1, 2]))
        elif tier == 2:
            pool = [
                f"bonus bDef,{random.randint(2, 3)};",
                f"bonus bVit,{random.randint(2, 4)};",
                f"bonus bMaxHP,{random.randint(350, 650)};",
                f"bonus bMdef,{random.randint(4, 7)};",
                f"bonus2 bSubEle,{random.choice(['Ele_Fire', 'Ele_Water', 'Ele_Wind', 'Ele_Earth'])},{random.randint(10, 15)};",
            ]
            if random.random() < 0.35:
                skill = random.choice(["AL_HEAL", "SM_ENDURE", "AL_BLESSING"])
                slv = random.randint(2, 3)
                pool.append(f'bonus3 bAutoSpellWhenHit,"{skill}",{slv},30;')
            bonuses = random.sample(pool, random.choice([2, 3]))
        else:  # Tier 3 (Ótima)
            pool = [
                f"bonus bDef,{random.randint(3, 4)};",  # Limitado a 5 no máximo
                f"bonus bVit,{random.randint(3, 5)};",
                f"bonus bMaxHP,{random.randint(700, 1200)};",
                f"bonus bMdef,{random.randint(8, 12)};", # Limitado a 15 no máximo
                f"bonus bAllStats,{random.randint(2, 3)};",
                f"bonus2 bSubEle,{random.choice(['Ele_Fire', 'Ele_Water', 'Ele_Wind', 'Ele_Earth'])},{random.randint(15, 20)};",
            ]
            if random.random() < 0.50:
                skill = random.choice(["AL_HEAL", "SM_ENDURE", "AL_BLESSING", "PR_KYRIE"])
                slv = random.randint(3, 5)
                pool.append(f'bonus3 bAutoSpellWhenHit,"{skill}",{slv},30;')
            bonuses = random.sample(pool, random.choice([2, 3]))

    # ── B. SAPATOS / CALÇADOS (loc 64) ────────────────────────────────────────
    # Foco: Sobrevivência e ataque (MaxHP, MaxSP, Atk, Agi, AspdRate, Flee)
    elif loc & 64:
        if tier == 0:
            flaws = [
                ["bonus bMaxHP,60;"],
                ["bonus bAtk,3;", "bonus bFlee,-2;"],
                ["bonus bAgi,-1;", "bonus bMaxSP,20;"],
                ["bonus bFlee,2;"]
            ]
            bonuses = random.choice(flaws)
        elif tier == 1:
            pool = [
                f"bonus bMaxHP,{random.randint(100, 220)};",
                f"bonus bMaxSP,{random.randint(20, 50)};",
                f"bonus bAtk,{random.randint(5, 8)};",
                f"bonus bAgi,{random.randint(1, 2)};",
                f"bonus bFlee,{random.randint(3, 6)};",
            ]
            bonuses = random.sample(pool, random.choice([1, 2]))
        elif tier == 2:
            pool = [
                f"bonus bMaxHP,{random.randint(280, 500)};",
                f"bonus bMaxSP,{random.randint(60, 100)};",
                f"bonus bAtk,{random.randint(10, 15)};",
                f"bonus bAgi,{random.randint(2, 3)};",
                f"bonus bFlee,{random.randint(7, 12)};",
                f"bonus bAspdRate,{random.randint(2, 4)};",
            ]
            bonuses = random.sample(pool, random.choice([2, 3]))
        else:  # Tier 3 (Ótima)
            pool = [
                f"bonus bMaxHP,{random.randint(550, 850)};",
                f"bonus bMaxSP,{random.randint(110, 180)};",
                f"bonus bAtk,{random.randint(16, 22)};",
                f"bonus bAgi,{random.randint(3, 4)};",
                f"bonus bAspdRate,{random.randint(4, 6)};",
                f"bonus bAllStats,{random.randint(2, 3)};",
                f"bonus bFlee,{random.randint(14, 20)};",
            ]
            bonuses = random.sample(pool, random.choice([2, 3]))

    # ── C. CAPAS / MANTELETES (loc 4) ─────────────────────────────────────────
    # Foco: Defensivas (Flee, Redução Neutro até 12%, Redução Elemental até 20%, MDEF)
    elif loc & 4:
        if tier == 0:
            flaws = [
                ["bonus bFlee,3;"],
                ["bonus bMdef,1;"],
                ["bonus2 bSubEle,Ele_Neutral,3;", "bonus bFlee,-3;"],
                ["bonus bFlee,2;", "bonus bDef,-1;"]
            ]
            bonuses = random.choice(flaws)
        elif tier == 1:
            pool = [
                f"bonus bFlee,{random.randint(6, 12)};",
                f"bonus bMdef,{random.randint(2, 4)};",
                f"bonus2 bSubEle,Ele_Neutral,{random.randint(4, 6)};",
                f"bonus2 bSubEle,{random.choice(['Ele_Fire', 'Ele_Water', 'Ele_Wind', 'Ele_Earth'])},{random.randint(6, 10)};",
            ]
            bonuses = random.sample(pool, random.choice([1, 2]))
        elif tier == 2:
            pool = [
                f"bonus bFlee,{random.randint(12, 18)};",
                f"bonus bMdef,{random.randint(5, 8)};",
                f"bonus2 bSubEle,Ele_Neutral,{random.randint(7, 10)};",
                f"bonus2 bSubEle,{random.choice(['Ele_Fire', 'Ele_Water', 'Ele_Wind', 'Ele_Earth'])},{random.randint(12, 16)};",
            ]
            bonuses = random.sample(pool, random.choice([2, 3]))
        else:  # Tier 3 (Ótima)
            pool = [
                f"bonus bFlee,{random.randint(18, 26)};",
                f"bonus bMdef,{random.randint(8, 14)};",  # Limitado a 15
                f"bonus2 bSubEle,Ele_Neutral,{random.randint(10, 12)};", # Capped em 12%
                f"bonus2 bSubEle,{random.choice(['Ele_Fire', 'Ele_Water', 'Ele_Wind', 'Ele_Earth'])},{random.randint(16, 20)};", # Capped em 20%
                f"bonus bAllStats,{random.randint(2, 3)};",
            ]
            bonuses = random.sample(pool, random.choice([2, 3]))

    # ── D. ESCUDOS (loc 32) ───────────────────────────────────────────────────
    # Foco: Defesa pura (DEF máx 4, MDEF máx 6, Reduções elementais até 15%)
    elif loc & 32:
        if tier == 0:
            bonuses = ["bonus bDef,1;", "bonus bMdef,-1;"] if random.random() < 0.5 else ["bonus bDef,1;"]
        elif tier == 1:
            pool = [
                f"bonus bDef,{random.randint(1, 2)};",
                f"bonus bMdef,{random.randint(2, 4)};",
                f"bonus bMaxHP,{random.randint(100, 200)};",
                f"bonus2 bSubEle,{random.choice(['Ele_Fire', 'Ele_Water', 'Ele_Wind', 'Ele_Earth'])},{random.randint(5, 8)};",
            ]
            bonuses = random.sample(pool, random.choice([1, 2]))
        elif tier == 2:
            pool = [
                f"bonus bDef,{random.randint(2, 3)};",
                f"bonus bMdef,{random.randint(4, 6)};",
                f"bonus bMaxHP,{random.randint(250, 450)};",
                f"bonus2 bSubEle,{random.choice(['Ele_Fire', 'Ele_Water', 'Ele_Wind', 'Ele_Earth'])},{random.randint(10, 15)};",
            ]
            bonuses = random.sample(pool, random.choice([2, 3]))
        else:  # Tier 3 (Ótima)
            pool = [
                f"bonus bDef,{random.randint(3, 4)};",  # Máx 5
                f"bonus bMdef,{random.randint(6, 10)};", # Capped em 15
                f"bonus bMaxHP,{random.randint(500, 750)};",
                f"bonus bAllStats,{random.randint(1, 2)};",
                f"bonus2 bSubEle,{random.choice(['Ele_Fire', 'Ele_Water', 'Ele_Wind', 'Ele_Earth'])},{random.randint(14, 18)};",
            ]
            bonuses = random.sample(pool, random.choice([2, 3]))

    # ── E. ACESSÓRIOS (loc 136, 8, 128) ───────────────────────────────────────
    # Foco: Habilidades ativas e pontos brutos nos atributos até +5 no limite
    elif loc & 8 or loc & 128 or loc == 136:
        stat_choice = random.choice(["Str", "Agi", "Vit", "Int", "Dex", "Luk"])
        if tier == 0:
            bonuses = [f"bonus b{stat_choice},1;"]
        elif tier == 1:
            pool = [
                f"bonus b{stat_choice},{random.randint(1, 2)};",
                f"bonus bMaxSP,{random.randint(20, 50)};",
                f"bonus bMaxHP,{random.randint(80, 180)};",
            ]
            bonuses = random.sample(pool, random.choice([1, 2]))
        elif tier == 2:
            pool = [
                f"bonus b{stat_choice},{random.randint(3, 4)};",
                f"bonus bMaxSP,{random.randint(50, 90)};",
                f"bonus bMaxHP,{random.randint(200, 380)};",
            ]
            # 35% de chance de conceder habilidade ativa Lv 1..2
            if random.random() < 0.35:
                active_skill = random.choice(["AL_HEAL", "AL_TELEPORT", "AL_CURE", "MG_FIREBOLT", "TF_STEAL", "TF_HIDING", "SM_MAGNUM"])
                slv = 1 if active_skill in ["AL_TELEPORT", "AL_CURE", "TF_HIDING"] else 2
                pool.append(f'skill "{active_skill}",{slv};')
            bonuses = random.sample(pool, random.choice([2, 3]))
        else:  # Tier 3 (Ótima)
            pool = [
                f"bonus b{stat_choice},{random.randint(4, 5)};",  # Limite máximo de +5
                f"bonus bAllStats,{random.randint(2, 3)};",       # Limitado a +3
                f"bonus bMaxSP,{random.randint(90, 150)};",
                f"bonus bMaxHP,{random.randint(400, 650)};",
            ]
            # 60% de chance de conceder habilidade ativa Lv 2..3
            if random.random() < 0.60:
                active_skill = random.choice(["AL_HEAL", "AL_BLESSING", "AL_INCAGI", "AL_TELEPORT", "SM_BASH", "MC_MAMMONITE", "MG_FIREBOLT"])
                slv = 1 if active_skill == "AL_TELEPORT" else random.randint(2, 3)
                pool.append(f'skill "{active_skill}",{slv};')
            bonuses = random.sample(pool, random.choice([2, 3]))

    # ── F. CABEÇA / HEADGEARS E OUTROS (loc 256, 512, 1, default) ────────────
    # Foco: Status (+1..+3), MDEF (+1..+5), MaxHP/SP, Flee
    else:
        stat_choice = random.choice(["Str", "Agi", "Vit", "Int", "Dex", "Luk"])
        if tier == 0:
            bonuses = [f"bonus b{stat_choice},1;"]
        elif tier == 1:
            pool = [
                f"bonus b{stat_choice},{random.randint(1, 2)};",
                f"bonus bMdef,{random.randint(1, 2)};",
                f"bonus bMaxSP,{random.randint(20, 40)};",
            ]
            bonuses = random.sample(pool, random.choice([1, 2]))
        elif tier == 2:
            pool = [
                f"bonus b{stat_choice},{random.randint(2, 3)};",
                f"bonus bMdef,{random.randint(2, 4)};",
                f"bonus bMaxHP,{random.randint(150, 300)};",
                f"bonus bFlee,{random.randint(4, 8)};",
            ]
            bonuses = random.sample(pool, random.choice([2, 3]))
        else:  # Tier 3 (Ótima)
            pool = [
                f"bonus b{stat_choice},{random.randint(3, 4)};",
                f"bonus bAllStats,{random.randint(1, 2)};",
                f"bonus bMdef,{random.randint(4, 6)};",
                f"bonus bMaxHP,{random.randint(300, 500)};",
                f"bonus bFlee,{random.randint(8, 14)};",
            ]
            bonuses = random.sample(pool, random.choice([2, 3]))

    return " ".join(bonuses)


def extract_first_script(line):
    idx = line.find("{")
    if idx == -1:
        return line.rstrip("\r\n"), "", ",{},{}"
    before_script = line[:idx]
    depth = 0
    in_quote = False
    quote_char = ""
    script_start = idx + 1
    script_end = -1
    i = idx
    while i < len(line):
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


def main():
    if not os.path.isfile(DB):
        fallback = os.path.join("data_base", ITEM_DB)
        if os.path.isfile(fallback):
            db_path = fallback
        else:
            print(f"[ERRO] Arquivo {DB} não encontrado.")
            sys.exit(1)
    else:
        db_path = DB

    backup_file = db_path + ".affix_orig"
    if not os.path.isfile(backup_file):
        shutil.copyfile(db_path, backup_file)
        print(f"  [Backup criado] {backup_file}")
    else:
        shutil.copyfile(backup_file, db_path)

    lines = []
    tier_counts = {0: 0, 1: 0, 2: 0, 3: 0}
    total_equips = 0
    weapons_count = 0
    armors_count = 0

    with open(db_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.startswith("//") or line.strip() == "":
                lines.append(line)
                continue

            cols = line.split(",")
            try:
                item_id = int(cols[0])
                item_type = int(cols[3])
                loc = int(cols[14]) if len(cols) > 14 and cols[14].strip().isdigit() else 0
            except (ValueError, IndexError):
                lines.append(line)
                continue

            # Equipamentos apenas: Tipo 4 (Armas) e Tipo 5 (Armaduras/Acessórios)
            if item_type not in (4, 5):
                lines.append(line)
                continue

            tier = get_bell_curve_tier()
            tier_counts[tier] += 1
            total_equips += 1

            if item_type == 4:
                script = generate_weapon_affixes(tier)
                weapons_count += 1
            else:
                script = generate_armor_affixes_by_slot(loc, tier)
                armors_count += 1

            before_script, orig_script, after_script = extract_first_script(line)
            combined_script = f"{orig_script} {script}".strip()
            body = f" {combined_script} " if combined_script else ""
            new_line = f"{before_script}{{{body}}}{after_script}\n"
            lines.append(new_line)

    with open(db_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"Afixos Pre-Renewal aplicados com sucesso em {total_equips} equipamentos ({weapons_count} armas, {armors_count} armaduras)!")
    if total_equips > 0:
        print(f"  - Ruim/Defeituosa: {tier_counts[0]} ({tier_counts[0]*100/total_equips:.1f}%)")
        print(f"  - Medíocre/Comum:  {tier_counts[1]} ({tier_counts[1]*100/total_equips:.1f}%)")
        print(f"  - Boa/Rara:        {tier_counts[2]} ({tier_counts[2]*100/total_equips:.1f}%)")
        print(f"  - Ótima/Primorosa: {tier_counts[3]} ({tier_counts[3]*100/total_equips:.1f}%)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
tools/enhance_unpopular_cards.py

Enhancer Determinístico de Cartas Não Populares / Esquecidas (RagnaRogue).
Lê a seed ativa do mundo (WORLD_SEED) e injeta pequenos buffs temáticos e de nicho
nas cartas de atributo simples, ganho de SP medíocre e resistências fracas.

Atualiza de forma transparente:
1. data/db/pre-re/item_db.txt (Mecânica do servidor rAthena)
2. data_base/db/pre-re/item_db.txt (Backup sincronizado)
3. client/System/itemInfo.lua (Descrições do cliente roBrowser/Ragnarok)
"""

import argparse
import hashlib
import os
import random
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_RANDO = os.path.join(ROOT, ".env.rando")
DATA_ITEM_DB = os.path.join(ROOT, "data", "db", "pre-re", "item_db.txt")
BASE_ITEM_DB = os.path.join(ROOT, "data_base", "db", "pre-re", "item_db.txt")
ITEM_INFO_LUA = os.path.join(ROOT, "client", "System", "itemInfo.lua")

# Catálogo Curado de Cartas Não Populares / Esquecidas e seus Arquétipos de Nicho
UNPOPULAR_CARDS = {
    # --- Atributos Simples / Básicas (Acessórios e Armaduras e Armas) ---
    4001: {"name": "Carta Poring", "slot": "Acessório", "arch": "poring"},
    4002: {"name": "Carta Fabre", "slot": "Arma", "arch": "stat_single_weapon"},
    4003: {"name": "Carta Pupa", "slot": "Armadura", "arch": "pupa"},
    4004: {"name": "Carta Drops", "slot": "Arma", "arch": "drops"},
    4006: {"name": "Carta Lunático", "slot": "Acessório", "arch": "lunatic"},
    4008: {"name": "Carta Picky", "slot": "Armadura", "arch": "picky"},
    4009: {"name": "Carta Chonchon", "slot": "Calçados", "arch": "chonchon"},
    4010: {"name": "Carta Salgueiro", "slot": "Cabeça", "arch": "willow"},
    4011: {"name": "Carta Bebê Picky", "slot": "Armadura", "arch": "stat_single_armor"},
    4012: {"name": "Carta Ovo de Besouro Ladrão", "slot": "Escudo", "arch": "stat_single_shield"},
    4014: {"name": "Carta Sapo de Roda", "slot": "Armadura", "arch": "stat_single_armor"},
    4015: {"name": "Carta Condor", "slot": "Capa", "arch": "stat_single_garment"},
    4016: {"name": "Carta Besouro Ladrão", "slot": "Arma", "arch": "stat_single_weapon"},
    4018: {"name": "Carta Larva de Andre", "slot": "Arma", "arch": "stat_single_weapon"},
    4019: {"name": "Carta Zangão", "slot": "Arma", "arch": "stat_single_weapon"},
    4021: {"name": "Carta Rocker", "slot": "Armadura", "arch": "rocker"},
    4022: {"name": "Carta Esporo", "slot": "Acessório", "arch": "stat_single_acc"},
    4023: {"name": "Carta Filhote de Lobo do Deserto", "slot": "Cabeça", "arch": "stat_single_head"},
    4026: {"name": "Carta Besouro Ladrão Fêmea", "slot": "Armadura", "arch": "stat_single_armor"},
    4027: {"name": "Carta Kukre", "slot": "Acessório", "arch": "kukre"},
    4028: {"name": "Carta Tarou", "slot": "Acessório", "arch": "tarou"},
    4029: {"name": "Carta Lobo", "slot": "Arma", "arch": "stat_single_weapon"},
    4032: {"name": "Carta Ambernite", "slot": "Escudo", "arch": "stat_single_shield"},
    4036: {"name": "Carta Muka", "slot": "Acessório", "arch": "stat_single_acc"},
    4038: {"name": "Carta Zumbi", "slot": "Calçados", "arch": "zombie"},
    4042: {"name": "Carta Chonchon de Aço", "slot": "Armadura", "arch": "stat_single_armor"},
    4044: {"name": "Carta Eclipse", "slot": "Capa", "arch": "stat_single_garment"},
    4049: {"name": "Carta Wormtail", "slot": "Acessório", "arch": "wormtail"},
    4054: {"name": "Carta Andre", "slot": "Arma", "arch": "stat_single_weapon"},
    4056: {"name": "Carta Sapo Cururu", "slot": "Escudo", "arch": "stat_single_shield"},
    4057: {"name": "Carta Salgueiro Ancião", "slot": "Cabeça", "arch": "elder_willow"},

    # --- Resistências Elementais e Raciais Isoladas (Capa / Escudo) ---
    4020: {"name": "Carta Poeira (Dustiness)", "slot": "Capa", "arch": "ele_dustiness"},
    4068: {"name": "Carta Orc Zumbi", "slot": "Capa", "arch": "ele_orczombie"},
    4073: {"name": "Carta Hode", "slot": "Capa", "arch": "ele_hode"},
    4074: {"name": "Carta Névoa (Myst)", "slot": "Capa", "arch": "ele_myst"},
    4075: {"name": "Carta Argos", "slot": "Escudo", "arch": "argos"},
    4076: {"name": "Carta Jakk", "slot": "Capa", "arch": "ele_jakk"},
    4084: {"name": "Carta Marionete", "slot": "Capa", "arch": "ele_marionette"},
    4086: {"name": "Carta Megalodon", "slot": "Escudo", "arch": "megalodon"},
    4087: {"name": "Carta Marte", "slot": "Capa", "arch": "ele_mars"},
    4151: {"name": "Carta Gaster", "slot": "Escudo", "arch": "gaster"},

    # --- Status e Autocasts com Baixa Chance em Arma ---
    4017: {"name": "Carta Bebê Selvagem", "slot": "Arma", "arch": "status_savage"},
    4024: {"name": "Carta Plankton", "slot": "Arma", "arch": "status_plankton"},
    4025: {"name": "Carta Esqueleto", "slot": "Arma", "arch": "status_skeleton"},
    4033: {"name": "Carta Poporing", "slot": "Arma", "arch": "status_poporing"},
    4037: {"name": "Carta Familiar", "slot": "Arma", "arch": "status_familiar"},
    4043: {"name": "Carta Marina", "slot": "Arma", "arch": "status_marina"},
    4062: {"name": "Carta Metaller", "slot": "Arma", "arch": "status_metaller"},
    4085: {"name": "Carta Requiem", "slot": "Arma", "arch": "status_requiem"},

    # --- Dano Racial de Nicho Esquecido em Arma ---
    4047: {"name": "Carta Caramel", "slot": "Arma", "arch": "racial_niche"},
    4060: {"name": "Carta Goblin", "slot": "Arma", "arch": "racial_niche"},
    4061: {"name": "Carta Flora", "slot": "Arma", "arch": "racial_niche"},
    4064: {"name": "Carta Escorpião", "slot": "Arma", "arch": "racial_niche"},
    4069: {"name": "Carta Esqueleto Orc", "slot": "Arma", "arch": "racial_niche"},
    4072: {"name": "Carta Strouf", "slot": "Arma", "arch": "racial_niche"},
    4088: {"name": "Carta Lobo do Deserto", "slot": "Arma", "arch": "racial_niche"},

    # --- Cartas de SP Medíocre / Drops de Baixa Relevância ---
    4118: {"name": "Carta Boneca de Miyabi", "slot": "Calçados", "arch": "sp_sustain"},
    4125: {"name": "Carta Kapha", "slot": "Calçados", "arch": "sp_sustain"},
    4133: {"name": "Carta Fungo Demoníaco", "slot": "Calçados", "arch": "sp_sustain"},
    4240: {"name": "Carta Tengu", "slot": "Acessório", "arch": "sp_sustain"},
    4272: {"name": "Carta Planta Eremita", "slot": "Acessório", "arch": "sp_sustain"},
    4302: {"name": "Carta Verme com Tromba", "slot": "Acessório", "arch": "sp_sustain"},
    4324: {"name": "Carta Iguana Verde", "slot": "Acessório", "arch": "sp_sustain"},
}


def get_world_seed():
    """Obtém a seed ativa do mundo do .env.rando."""
    if os.path.isfile(ENV_RANDO):
        with open(ENV_RANDO, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("WORLD_SEED="):
                    return line.split("=", 1)[1].strip()
    return "radiante-evil-druid-1649"


def get_card_rng(seed_str, card_id):
    """Gera um gerador pseudoaleatório determinístico por carta e seed."""
    digest = hashlib.sha256(f"{seed_str}:card_enhancer:{card_id}".encode("utf-8")).hexdigest()
    return random.Random(int(digest, 16))


def generate_enhancement(rng, card_id, meta):
    """
    Gera o bônus de nicho determinístico e equilibrado baseado no arquétipo da carta.
    Retorna (script_bonus, desc_pt_br).
    """
    arch = meta["arch"]

    # 1. Cartas com Arquétipos Específicos
    if arch == "picky":
        aspd = rng.randint(3, 5)
        hit = rng.randint(8, 14)
        return f"bonus bAspdRate,{aspd}; bonus bHit,{hit};", f"ASPD +{aspd}%, Precisão +{hit}"

    if arch == "lunatic":
        crit_dmg = rng.randint(8, 14)
        zeny = rng.randint(6, 12)
        return f"bonus bCritAtkRate,{crit_dmg}; bonus bZenyRate,{zeny};", f"Dano Crítico +{crit_dmg}%, Ganho de Zeny +{zeny}%"

    if arch == "rocker":
        weight = rng.choice([350, 450, 500, 600])
        atk = rng.randint(10, 18)
        return f"bonus bWeight,{weight}; bonus bAtk,{atk};", f"Capacidade de Carga +{weight}, ATK +{atk}"

    if arch == "wormtail":
        long_dmg = rng.randint(6, 10)
        hit = rng.randint(10, 16)
        return f"bonus bLongAtkRate,{long_dmg}; bonus bHit,{hit};", f"Dano a Distância +{long_dmg}%, Precisão +{hit}"

    if arch == "poring":
        flee2 = rng.randint(4, 7)
        zeny = rng.randint(8, 15)
        return f"bonus bFlee2,{flee2}; bonus bZenyRate,{zeny};", f"Esquiva Perfeita +{flee2}, Ganho de Zeny +{zeny}%"

    if arch == "drops":
        hit = rng.randint(15, 25)
        long_dmg = rng.randint(4, 7)
        return f"bonus bHit,{hit}; bonus bLongAtkRate,{long_dmg};", f"Precisão +{hit}, Dano a Distância +{long_dmg}%"

    if arch == "pupa":
        hp_rate = rng.randint(4, 7)
        def_bonus = rng.randint(3, 5)
        return f"bonus bMaxHPrate,{hp_rate}; bonus bDef,{def_bonus};", f"Max HP +{hp_rate}%, DEF +{def_bonus}"

    if arch == "willow":
        sp_rate = rng.randint(5, 8)
        sp_regen = rng.randint(15, 25)
        return f"bonus bMaxSPrate,{sp_rate}; bonus bSPRegenRate,{sp_regen};", f"Max SP +{sp_rate}%, Regeneração de SP +{sp_regen}%"

    if arch == "elder_willow":
        matk = rng.randint(4, 7)
        cast = rng.randint(4, 7)
        return f"bonus bMatkRate,{matk}; bonus bCastrate,-{cast};", f"MATK +{matk}%, Tempo de Conjuração -{cast}%"

    if arch == "chonchon":
        flee = rng.randint(8, 14)
        speed = rng.randint(5, 8)
        return f"bonus bFlee,{flee}; bonus bSpeedRate,{speed};", f"Esquiva +{flee}, Vel. de Movimento +{speed}%"

    if arch == "kukre":
        aspd = rng.randint(4, 7)
        flee = rng.randint(8, 12)
        return f"bonus bAspdRate,{aspd}; bonus bFlee,{flee};", f"ASPD +{aspd}%, Esquiva +{flee}"

    if arch == "tarou":
        atk = rng.randint(15, 25)
        aspd = rng.randint(3, 5)
        return f"bonus bAtk,{atk}; bonus bAspdRate,{aspd};", f"ATK +{atk}, ASPD +{aspd}%"

    if arch == "zombie":
        hp_regen = rng.randint(40, 60)
        return f"bonus bHPRegenRate,{hp_regen}; bonus2 bGetZenyNum,30,80;", f"Regeneração Natural de HP +{hp_regen}%, Pilhagem de Zeny em Monstros"

    # 2. Resistências Elementais (Capa / Escudo): Ganham bônus de dano contra o elemento oposto!
    if arch == "ele_dustiness": # Vento -> Caça Água
        dmg = rng.randint(10, 15)
        return f"bonus2 bAddEle,Ele_Water,{dmg};", f"Dano contra monstros de Água +{dmg}%"
    if arch == "ele_mars": # Água -> Caça Fogo
        dmg = rng.randint(10, 15)
        return f"bonus2 bAddEle,Ele_Fire,{dmg};", f"Dano contra monstros de Fogo +{dmg}%"
    if arch == "ele_hode": # Terra -> Caça Vento
        dmg = rng.randint(10, 15)
        return f"bonus2 bAddEle,Ele_Wind,{dmg};", f"Dano contra monstros de Vento +{dmg}%"
    if arch == "ele_jakk": # Fogo -> Caça Terra
        dmg = rng.randint(10, 15)
        return f"bonus2 bAddEle,Ele_Earth,{dmg};", f"Dano contra monstros de Terra +{dmg}%"
    if arch == "ele_myst": # Veneno -> Caça Veneno
        dmg = rng.randint(10, 15)
        return f"bonus2 bAddEle,Ele_Poison,{dmg};", f"Dano contra monstros de Veneno +{dmg}%"
    if arch == "ele_orczombie": # Maldito -> Caça Morto-Vivo
        dmg = rng.randint(10, 15)
        return f"bonus2 bAddEle,Ele_Undead,{dmg};", f"Dano contra monstros Mortos-Vivos +{dmg}%"
    if arch == "ele_marionette": # Fantasma -> Caça Fantasma
        dmg = rng.randint(10, 15)
        return f"bonus2 bAddEle,Ele_Ghost,{dmg};", f"Dano contra monstros Fantasmas +{dmg}%"
    if arch == "argos":
        return "bonus bDef,4; bonus bMdef,4; bonus2 bResEff,Eff_Stone,3000;", "DEF +4, MDEF +4, Resistência a Petrificação +30%"
    if arch == "megalodon":
        return "bonus2 bSubEle,Ele_Water,15; bonus bDef,3;", "Resistência a Água +15%, DEF +3"
    if arch == "gaster":
        return "bonus bSubEle,Ele_Neutral,5; bonus bDef,4; bonus bMdef,4;", "Resistência a Neutro +5%, DEF +4, MDEF +4"

    # 3. Status em Armas
    if arch == "status_savage":
        crit = rng.randint(8, 14)
        return f"bonus2 bAddEff,Eff_Stun,800; bonus bCritAtkRate,{crit};", f"Chance de Atordoar +8%, Dano Crítico +{crit}%"
    if arch == "status_plankton":
        atk = rng.randint(15, 25)
        return f"bonus2 bAddEff,Eff_Sleep,800; bonus bAtk,{atk};", f"Chance de Sono +8%, ATK +{atk}"
    if arch == "status_skeleton":
        hit = rng.randint(12, 18)
        return f"bonus2 bAddEff,Eff_Stun,600; bonus bHit,{hit};", f"Chance de Atordoar +6%, Precisão +{hit}"
    if arch == "status_poporing":
        atk = rng.randint(15, 25)
        return f"bonus2 bAddEff,Eff_Poison,1000; bonus bAtk,{atk};", f"Chance de Envenenar +10%, ATK +{atk}"
    if arch == "status_familiar":
        hit = rng.randint(15, 25)
        return f"bonus2 bAddEff,Eff_Blind,800; bonus bHit,{hit};", f"Chance de Cegueira +8%, Precisão +{hit}"
    if arch == "status_marina":
        dmg = rng.randint(8, 14)
        return f"bonus2 bAddEff,Eff_Freeze,800; bonus2 bAddEle,Ele_Water,{dmg};", f"Chance de Congelar +8%, Dano em Água +{dmg}%"
    if arch == "status_metaller":
        aspd = rng.randint(3, 5)
        return f"bonus2 bAddEff,Eff_Silence,800; bonus bAspdRate,{aspd};", f"Chance de Silêncio +8%, ASPD +{aspd}%"
    if arch == "status_requiem":
        flee = rng.randint(10, 16)
        return f"bonus2 bAddEff,Eff_Confusion,800; bonus bFlee,{flee};", f"Chance de Caos +8%, Esquiva +{flee}"

    # 4. Danos Raciais de Nicho
    if arch == "racial_niche":
        pool = [
            (f"bonus bCritAtkRate,{rng.randint(8, 12)};", f"Dano Crítico +{rng.randint(8, 12)}%"),
            (f"bonus bHit,{rng.randint(12, 18)};", f"Precisão +{rng.randint(12, 18)}"),
            (f"bonus bDoubleRate,{rng.randint(10, 15)};", f"Chance de Ataque Duplo +{rng.randint(10, 15)}%"),
            (f"bonus bAspdRate,{rng.randint(3, 6)};", f"ASPD +{rng.randint(3, 6)}%"),
        ]
        return rng.choice(pool)

    # 5. SP Sustain / Mediocre
    if arch == "sp_sustain":
        sp_regen = rng.randint(20, 35)
        sp_rate = rng.randint(4, 8)
        return f"bonus bSPRegenRate,{sp_regen}; bonus bMaxSPrate,{sp_rate};", f"Regeneração de SP +{sp_regen}%, Max SP +{sp_rate}%"

    # 6. Fallback Geral por Slot
    if meta["slot"] == "Arma":
        atk = rng.randint(15, 25)
        hit = rng.randint(8, 14)
        return f"bonus bAtk,{atk}; bonus bHit,{hit};", f"ATK +{atk}, Precisão +{hit}"
    elif meta["slot"] == "Armadura":
        hp = rng.randint(4, 7)
        def_b = rng.randint(2, 4)
        return f"bonus bMaxHPrate,{hp}; bonus bDef,{def_b};", f"Max HP +{hp}%, DEF +{def_b}"
    elif meta["slot"] == "Escudo":
        def_b = rng.randint(3, 5)
        mdef_b = rng.randint(3, 5)
        return f"bonus bDef,{def_b}; bonus bMdef,{mdef_b};", f"DEF +{def_b}, MDEF +{mdef_b}"
    elif meta["slot"] == "Capa":
        flee = rng.randint(10, 16)
        return f"bonus bFlee,{flee};", f"Esquiva +{flee}"
    elif meta["slot"] == "Calçados":
        speed = rng.randint(5, 8)
        return f"bonus bSpeedRate,{speed};", f"Vel. de Movimento +{speed}%"
    elif meta["slot"] == "Acessório":
        flee2 = rng.randint(3, 5)
        return f"bonus bFlee2,{flee2};", f"Esquiva Perfeita +{flee2}"
    else:
        mdef = rng.randint(3, 5)
        return f"bonus bMdef,{mdef};", f"MDEF +{mdef}"


def enhance_item_db(seed_str, apply=True):
    """Injeta os buffs nas cartas em data/db/pre-re/item_db.txt."""
    if not os.path.isfile(DATA_ITEM_DB):
        print(f"[ERRO] Arquivo não encontrado: {DATA_ITEM_DB}")
        return {}

    enhanced_map = {}
    lines = []
    with open(DATA_ITEM_DB, "r", encoding="latin-1") as f:
        for line in f:
            if line.startswith("//"):
                lines.append(line)
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 15 and parts[3] == "6" and parts[0].isdigit():
                cid = int(parts[0])
                if cid in UNPOPULAR_CARDS:
                    meta = UNPOPULAR_CARDS[cid]
                    rng = get_card_rng(seed_str, cid)
                    script_bonus, desc_pt = generate_enhancement(rng, cid, meta)
                    enhanced_map[cid] = (meta["name"], desc_pt, script_bonus)

                    # Inserir no script entre o primeiro '{' e o próximo '}'
                    # Formato rAthena: { script },{ on_equip },{ on_unequip }
                    s_idx = line.find("{")
                    if s_idx != -1:
                        close_idx = line.find("}", s_idx)
                        if close_idx != -1:
                            orig_script = line[s_idx + 1:close_idx].strip()
                            if orig_script and not orig_script.endswith(";"):
                                orig_script += ";"
                            # Evita duplicação caso já contenha o script_bonus
                            if script_bonus not in orig_script:
                                new_script = f" {orig_script} {script_bonus} " if orig_script else f" {script_bonus} "
                                line = line[:s_idx + 1] + new_script + line[close_idx:]

            lines.append(line if line.endswith("\n") else line + "\n")

    if apply:
        with open(DATA_ITEM_DB, "w", encoding="latin-1") as f:
            f.writelines(lines)
        if os.path.isfile(BASE_ITEM_DB):
            with open(BASE_ITEM_DB, "w", encoding="latin-1") as f:
                f.writelines(lines)

    return enhanced_map


def enhance_item_info_lua(enhanced_map, apply=True):
    """Atualiza as descrições no client/System/itemInfo.lua adicionando tag do Enhancer."""
    if not os.path.isfile(ITEM_INFO_LUA) or not enhanced_map:
        return 0

    with open(ITEM_INFO_LUA, "r", encoding="latin-1") as f:
        content = f.read()

    # Limpar qualquer tag anterior inserida em unidentified ou identified
    content = re.sub(r'\s*\^00AA00\[Enhancer RagnaRogue: [^\]]+\]\^000000.*?\n', '\n', content)

    updated_count = 0
    for cid, (name, desc_pt, _) in enhanced_map.items():
        pattern = rf"(\[{cid}\]\s*=\s*\{{[\s\S]*?\s+identifiedDescriptionName\s*=\s*\{{\s*\n)([\s\S]*?)(\n\s*\}})"
        match = re.search(pattern, content)
        if match:
            head = match.group(1)
            body = match.group(2)
            tail = match.group(3)

            tag = f'            "^00AA00[Enhancer: {desc_pt}]^000000",'

            # Insere a nova tag no bloco de efeitos ou logo antes de "Tipo:"
            if "Tipo:" in body:
                body = body.replace('            "Tipo:', tag + '\n            "Tipo:', 1)
            else:
                body = tag + "\n" + body

            content = content[:match.start()] + head + body + tail + content[match.end():]
            updated_count += 1

    if apply and updated_count > 0:
        with open(ITEM_INFO_LUA, "w", encoding="latin-1") as f:
            f.write(content)

    return updated_count


def main():
    parser = argparse.ArgumentParser(description="Enhancer Determinístico de Cartas Não Populares")
    parser.add_argument("--seed", help="Seed do mundo para geração determinística (padrão: de .env.rando)")
    parser.add_argument("--dry-run", action="store_true", help="Apenas exibe os aprimoramentos gerados")
    args = parser.parse_args()

    seed_str = args.seed if args.seed else get_world_seed()
    print("==================================================")
    print("Enhancer de Cartas Não Populares (RagnaRogue)")
    print(f"Seed Ativa: {seed_str}")
    print("==================================================")

    apply_changes = not args.dry_run
    enhanced_map = enhance_item_db(seed_str, apply=apply_changes)

    print(f"\nTotal de cartas aprimoradas: {len(enhanced_map)}")
    print("-" * 75)
    print(f"{'ID':<6} {'Nome':<28} {'Slot':<12} {'Aprimoramento Nichado'}")
    print("-" * 75)
    for cid, (name, desc_pt, _) in sorted(enhanced_map.items()):
        slot = UNPOPULAR_CARDS[cid]["slot"]
        print(f"{cid:<6} {name:<28} {slot:<12} {desc_pt}")

    if apply_changes:
        lua_count = enhance_item_info_lua(enhanced_map, apply=True)
        print("-" * 75)
        print(f"[OK] data/db/pre-re/item_db.txt atualizado.")
        print(f"[OK] data_base/db/pre-re/item_db.txt sincronizado.")
        print(f"[OK] client/System/itemInfo.lua atualizado ({lua_count} descrições).")
    else:
        print("\n[DRY RUN] Nenhuma alteração gravada em disco.")


if __name__ == "__main__":
    main()

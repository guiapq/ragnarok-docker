#!/usr/bin/env python3
# =============================================================================
# RAGNAROGUE – Renewal / WoE TE & bRO 2024 Rebalance Applicator
#
# Aplica integralmente o rebalanceamento oficial de Transclasses e Ninjas
# ("Road to Ragnarök: A Caminho das Classes 4 - Parte 4" / bRO 2024 & kRO):
#   1. size_fix.txt: Modificadores de tamanho por arma (Knuckles 100/100/75, etc.)
#   2. import/skill_cast_db.txt: Castings, Delays e Cooldowns oficiais dos cards 2024
#   3. pre-re/skill_db.txt: Propriedades, hits, tipos de alvo (Huuma -> oponente, etc.)
#   4. pre-re/skill_require_db.txt: Requisitos de SP, catalisadores e esferas (Sem gema azul, 1 esfera Combo, etc.)
#   5. skill_damage_db.txt: Escalonamento de dano balanceado para WoE TE e PvM
#   6. conf/battle/battle.conf e skill.conf: Configurações de batalha fluidas
# =============================================================================

import os
import shutil

ROOT = "data"

# ─────────────────────────────────────────────────────────────────────────────
# 1. ATUALIZAÇÃO DO SIZE_FIX.TXT (Modificadores de tamanho por arma)
# ─────────────────────────────────────────────────────────────────────────────
def update_size_fix():
    path = os.path.join(ROOT, "db/size_fix.txt")
    backup = path + ".original"
    if not os.path.isfile(backup) and os.path.isfile(path):
        shutil.copyfile(path, backup)
        print(f"  [backup] {backup}")

    content = """// Size Fix Tables - Renewal / WoE TE Standard
// Columns - Weapon type
// Rows    - Target size
//Unarmed, Knife, 1H Sword, 2H Sword, 1H Spear, 2H Spears, 1H Axe, 2H Axe, Mace, 2H Mace, Staff, Bow, Knuckle, Musical Instrument, Whip, Book, Katar, Revolver, Rifle, Shotgun, Gatling Gun, Grenade Launcher, Fuuma Shuriken, 2H Staff
100,100, 75, 75, 75, 75, 50, 50, 75,100,100,100,100, 75, 75,100, 75,100,100,100,100,100,100,100	// Size: Small
100, 75,100, 75, 75, 75, 75, 75,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100	// Size: Medium
100, 50, 75,100,100,100,100,100,100,100,100, 75, 75, 75, 50, 75, 75,100,100,100,100,100,100,100	// Size: Large
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("  [size_fix.txt] Atualizado: Knuckles 100/100/75, Books 100/100/75, Guns 100/100/100.")

# ─────────────────────────────────────────────────────────────────────────────
# 2. GERAÇÃO DO IMPORT/SKILL_CAST_DB.TXT (bRO 2024 & Renewal Cast/Delay/Cooldown)
# ─────────────────────────────────────────────────────────────────────────────
def update_skill_cast():
    re_path = os.path.join(ROOT, "db/re/skill_cast_db.txt")
    target_path = os.path.join(ROOT, "db/import/skill_cast_db.txt")
    
    # Nomes limpos de skill
    snames = {}
    db_path = os.path.join(ROOT, "db/re/skill_db.txt")
    if os.path.isfile(db_path):
        with open(db_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("//"): continue
                parts = line.split(",")
                if len(parts) >= 17:
                    try:
                        snames[int(parts[0])] = parts[16].strip()
                    except ValueError: pass

    # Carregar dados padrão do re/skill_cast_db.txt (7 colunas)
    re_skills = {}
    with open(re_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line_s = line.strip()
            if not line_s or line_s.startswith("//"): continue
            parts = line_s.split(",")
            if len(parts) >= 7:
                try:
                    sid = int(parts[0])
                    re_skills[sid] = ",".join(parts[:7])
                except ValueError: pass

    # SOBRESCRITAS EXATAS DOS CARDS DE MARÇO DE 2024 (Road to Ragnarök - Transclasses e Ninjas)
    # Formato: SkillID,CastingTime,AfterCastActDelay,AfterCastWalkDelay,Duration1,Duration2,Cool Down
    bro_2024_overrides = {
        # --- LORDES ---
        # LK_SPIRALPIERCE (397): Fixo 0.3s (300ms) + Var 0.25s (250ms) = 550ms total cast, Delay 1s (1000ms), Cooldown 0
        397: "397,550,1000,0,1000,0,0",
        # LK_AURABLADE (355): Buff com duração
        355: "355,0,0,0,100000:100000:100000:100000:100000,0,0",
        # LK_CONCENTRATION (356): Duração ampliada (60s..120s)
        356: "356,0,0,0,60000:75000:90000:105000:120000,0,0",

        # --- PALADINOS ---
        # PA_SHIELDCHAIN (366): Cast 1s, Delay 1s
        366: "366,1000,1000,0,0,0,0",
        # PA_PRESSURE (367): Var 1s (1000ms), Delay 1s (1000ms), Cooldown 500ms
        367: "367,1000,1000,0,0,0,500",

        # --- MESTRES-FERREIROS ---
        # WS_OVERTHRUSTMAX (385): Duração de buff
        385: "385,0,0,0,180000,0,0",

        # --- PROFESSORES ---
        # PF_MEMORIZE (403): Cast fixo 2.5s (2500ms)
        403: "403,2500,0,0,0,0,0",
        # PF_HPCONVERSION (405): Delay 0.5s (500ms)
        405: "405,0,500,0,0,0,0",

        # --- ARQUIMAGOS ---
        # HW_GRAVITATION (484): Fixo 1s + Var 5s = 6000ms, Delay 1s (1000ms), Cooldown 5s (5000ms)
        484: "484,6000,1000,0,5000:6000:7000:8000:9000,0,5000",
        # HW_NAPALMVULCAN (378): Delay 0.5s (500ms), Cooldown 1s (1000ms)
        378: "378,1000,500,0,0,0,1000",

        # --- SUMO SACERDOTES ---
        # HP_BASILICA (363): Fixo 1s + Var 3s = 4000ms, Delay 1s (1000ms), Cooldown 30s (30000ms)
        363: "363,4000,1000,0,20000:25000:30000:35000:40000,0,30000",
        # HP_ASSUMPTIO (361): Delay 0.5s (500ms)
        361: "361,1000,500,0,20000:40000:60000:80000:100000,0,0",

        # --- MESTRES ---
        # CH_SOULCOLLECT (376 - Zen): Fixo 1s (1000ms)
        376: "376,1000,500,0,0,0,0",
        # CH_PALMSTRIKE (375): Delay 0.3s, Cooldown 0.3s
        375: "375,0,300,0,0,0,300",
        # CH_TIGERFIST (271): Delay 0.2s
        271: "271,0,200,0,0,0,0",
        # CH_CHAINCRUSH (372): Delay 0.2s, Cooldown 1s
        372: "372,0,200,0,0,0,1000",

        # --- ATIRADORES DE ELITE ---
        # SN_SHARPSHOOTING (381): Fixo 0.5s + Var 1.0s = 1500ms, Delay 0.5s (500ms)
        381: "381,1500,500,0,0,0,0",
        # SN_FALCONASSAULT (383): Delay 0.5s (500ms)
        383: "383,1000,500,0,0,0,0",

        # --- ALGOZES ---
        # ASC_METEORASSAULT (379): Delay 0s (0ms), Cooldown 0.5s (500ms)
        379: "379,500,0,0,0,0,500",
        # ASC_EDP (380): Delay 0s (0ms), Cooldown 2.0s (2000ms), Duração 60s (60000ms)
        380: "380,0,0,0,60000,0,2000",

        # --- MENESTRÉIS ---
        # CG_ARROWVULCAN (384): Fixo 0.5s + Var 1.5s = 2000ms, Delay 0.5s (500ms), Cooldown 1.5s (1500ms), WalkDelay 0
        384: "384,2000,500,0,0,0,1500",

        # --- NINJAS ---
        # NJ_KUNAI (524): Delay 0s (0ms), Cooldown 0.2s (200ms)
        524: "524,0,0,0,0,0,200",
        # NJ_KASUMIKIRI (528): Delay 0s (0ms), Cooldown 0.5s (500ms)
        528: "528,0,0,0,0,0,500",
        # NJ_KIRIKAGE (530 - Shadow Slash): Delay 0s (0ms)
        530: "530,0,0,0,0,0,0",
        # NJ_RAIGEKISAI (541): Fixo 0.3s + Var 1.7s = 2000ms, Delay 0.5s
        541: "541,2000,500,0,0,0,0",
        # NJ_HUUJIN (540 - Lâmina de Vento): Delay 0s (0ms)
        540: "540,1000,0,0,0,0,0",
        # NJ_KAMAITACHI (542 - Brisa Cortante): Fixo 0.3s + Var 1.2s = 1500ms, Delay 0.5s
        542: "542,1500,500,0,0,0,0",
        # NJ_HUUMA (525): Fixo 0.5s + Var 1.0s = 1500ms, Delay 0.5s
        525: "525,1500,500,0,0,0,0",
        # NJ_BAKUENRYU (536): Fixo 0.8s + Var 2.0s = 2800ms, Delay 0.5s, Cooldown 0.3s (300ms)
        536: "536,2800,500,0,0,0,300",
        # NJ_HYOUSYOURAKU (539): Fixo 0.8s + Var 2.5s = 3300ms, Delay 0.5s, Cooldown 0.3s (300ms)
        539: "539,3300,500,0,0,0,300",
        # NJ_SYURIKEN (523): Cast 0, Delay 0
        523: "523,0,0,0,0,0,0",
    }

    for sid, line in bro_2024_overrides.items():
        re_skills[sid] = line

    prefixes = {
        "Crusader & Paladin (2-2 & Trans)": ["CR_", "PA_"],
        "Monk & Champion (2-2 & Trans)": ["MO_", "CH_"],
        "Sage & Professor (2-2 & Trans)": ["SA_", "PF_"],
        "Rogue & Stalker (2-2 & Trans)": ["RG_", "ST_"],
        "Alchemist & Creator (2-2 & Trans)": ["AM_", "CR_"],
        "Bard, Dancer, Clown & Gypsy (2-2 & Trans)": ["BA_", "DC_", "BD_", "CG_"],
        "Knight & Lord Knight (2-1 & Trans)": ["KN_", "LK_"],
        "Wizard & High Wizard (2-1 & Trans)": ["WZ_", "HW_"],
        "Hunter & Sniper (2-1 & Trans)": ["HT_", "SN_"],
        "Assassin & Assassin Cross (2-1 & Trans)": ["AS_", "ASC_"],
        "Blacksmith & Whitesmith (2-1 & Trans)": ["BS_", "WS_"],
        "Priest & High Priest (2-1 & Trans)": ["PR_", "HP_"],
        "Gunslinger (Expanded)": ["GS_"],
        "Ninja (Expanded)": ["NJ_"],
        "Taekwon, Star Gladiator & Soul Linker (Expanded)": ["TK_", "SG_", "SL_"],
        "1st Classes (Swordsman, Mage, Archer, Acolyte, Merchant, Thief)": ["SM_", "MG_", "AC_", "AL_", "MC_", "TF_"]
    }

    output_lines = [
        "// ============================================================================\n",
        "// RAGNAROGUE – WoE TE & bRO 2024 Rebalance Skill Times (Cast, Delay, Cooldown)\n",
        "// Estrutura: SkillID,CastingTime,AfterCastActDelay,AfterCastWalkDelay,Duration1,Duration2,Cool Down\n",
        "// ============================================================================\n\n"
    ]

    total_count = 0
    used_sids = set()

    for group_name, prefs in prefixes.items():
        group_lines = []
        for sid, name in snames.items():
            if sid in used_sids: continue
            if any(name.startswith(p) for p in prefs) and sid in re_skills:
                used_sids.add(sid)
                tag = " [bRO 2024]" if sid in bro_2024_overrides else ""
                group_lines.append(f"//-- {name} (ID {sid}){tag}\n")
                group_lines.append(f"{re_skills[sid]}\n")
                total_count += 1
        if group_lines:
            output_lines.append(f"// ===== {group_name} =====\n")
            output_lines.extend(group_lines)
            output_lines.append("\n")

    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        f.writelines(output_lines)

    print(f"  [skill_cast_db.txt] Gerado com {total_count} habilidades (incluindo as 31 do bRO 2024).")

# ─────────────────────────────────────────────────────────────────────────────
# 3. ATUALIZAÇÃO DO PRE-RE/SKILL_DB.TXT (Flags, propriedades, hit count, alvos)
# ─────────────────────────────────────────────────────────────────────────────
def update_skill_db():
    target_path = os.path.join(ROOT, "db/pre-re/skill_db.txt")
    backup      = target_path + ".original"

    if not os.path.isfile(backup) and os.path.isfile(target_path):
        shutil.copyfile(target_path, backup)
        print(f"  [backup] {backup}")

    lines_out = []
    updated = 0

    with open(backup, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("//"):
                lines_out.append(line)
                continue

            parts = line.rstrip("\r\n").split(",")
            if len(parts) >= 17:
                try:
                    sid = int(parts[0])
                except ValueError:
                    lines_out.append(line)
                    continue

                # 1. PA_SHIELDCHAIN (366): Alcance aumentado de 4 para 11
                if sid == 366:
                    parts[1] = "11"  # range
                    updated += 1

                # 2. PA_PRESSURE (367): Sagrado (6) e tipo Magic
                elif sid == 367:
                    parts[4] = "6"      # element Holy
                    parts[13] = "magic" # skill_type
                    updated += 1

                # 3. HW_NAPALMVULCAN (378): Remove split de dano (remover 0x04 de nk)
                elif sid == 378:
                    parts[5] = "0x2"    # apenas splash, sem split (0x04)
                    updated += 1

                # 4. CG_ARROWVULCAN (384): Remove walk lock / delay de animação
                elif sid == 384:
                    parts[9] = "no"     # castcancel
                    parts[11] = "0x40000" # inf2 sem lock
                    updated += 1

                # 5. NJ_HUUMA (525): Alvo oponente (inf = 1), Splash 5x5 (splash = 2), nk = 0x2
                elif sid == 525:
                    parts[3] = "1"      # inf: 1 = enemy
                    parts[5] = "0x2"    # nk: splash
                    parts[6] = "2"      # splash: 2 = 5x5 cells
                    updated += 1

                # 6. NJ_KASUMIKIRI (528): Exibição de 2 golpes visuais
                elif sid == 528:
                    parts[2] = "2"      # hit count
                    updated += 1

                # 7. NJ_KIRIKAGE (530 - Shadow Slash): Exibição de 3 golpes visuais
                elif sid == 530:
                    parts[2] = "3"      # hit count
                    updated += 1

                # 8. NJ_RAIGEKISAI (541): Exibição de 3 golpes visuais
                elif sid == 541:
                    parts[2] = "3"      # hit count
                    updated += 1

                # 9. NJ_KAMAITACHI (542): Exibição de 5 golpes visuais
                elif sid == 542:
                    parts[2] = "5"      # hit count
                    updated += 1

                eol = "\r\n" if line.endswith("\r\n") else "\n"
                lines_out.append(",".join(parts) + eol)
                continue

            lines_out.append(line)

    with open(target_path, "w", encoding="utf-8") as f:
        f.writelines(lines_out)

    print(f"  [pre-re/skill_db.txt] Atualizado com {updated} habilidades modificadas para o padrão bRO 2024.")

# ─────────────────────────────────────────────────────────────────────────────
# 4. ATUALIZAÇÃO DO PRE-RE/SKILL_REQUIRE_DB.TXT (Requisitos SP e catalisadores)
# ─────────────────────────────────────────────────────────────────────────────
def update_skill_require_db():
    target_path = os.path.join(ROOT, "db/pre-re/skill_require_db.txt")
    backup      = target_path + ".original"

    if not os.path.isfile(backup) and os.path.isfile(target_path):
        shutil.copyfile(target_path, backup)
        print(f"  [backup] {backup}")

    lines_out = []
    updated = 0

    with open(backup, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("//"):
                lines_out.append(line)
                continue

            parts = line.rstrip("\r\n").split(",")
            if len(parts) >= 15:
                try:
                    sid = int(parts[0])
                except ValueError:
                    lines_out.append(line)
                    continue

                # 1. HW_GRAVITATION (484): Remove Gema Azul (717 -> 0) e ajusta SP (60..100)
                if sid == 484:
                    parts[3] = "60:70:80:90:100"  # SPCost
                    parts[13] = "0"               # RequiredItemID1 (remover Gema Azul)
                    parts[14] = "0"               # RequiredItemAmount1
                    updated += 1

                # 2. CH_CHAINCRUSH (372): Consumo de Esferas fixado em 1
                elif sid == 372:
                    parts[12] = "1"               # SpiritSphereCost = 1
                    updated += 1

                # 3. NJ_KUNAI (524): Custo de SP fixado em 10
                elif sid == 524:
                    parts[3] = "10"               # SPCost = 10
                    updated += 1

                # 4. NJ_KASUMIKIRI (528): Custo de SP fixado em 8
                elif sid == 528:
                    parts[3] = "8"                # SPCost = 8
                    updated += 1

                # 5. NJ_SYURIKEN (523): Custo de SP aumentado para 5
                elif sid == 523:
                    parts[3] = "5"                # SPCost = 5
                    updated += 1

                # 6. NJ_HUUMA (525): Custo de SP reduzido para 15..35
                elif sid == 525:
                    parts[3] = "15:20:25:30:35"   # SPCost reduzido
                    updated += 1

                eol = "\r\n" if line.endswith("\r\n") else "\n"
                lines_out.append(",".join(parts) + eol)
                continue

            lines_out.append(line)

    with open(target_path, "w", encoding="utf-8") as f:
        f.writelines(lines_out)

    print(f"  [pre-re/skill_require_db.txt] Atualizado com {updated} requisitos de SP, catalisadores e esferas bRO 2024.")

# ─────────────────────────────────────────────────────────────────────────────
# 5. ATUALIZAÇÃO DO SKILL_DAMAGE_DB.TXT (Escalonamento balanceado WoE TE / PvM)
# ─────────────────────────────────────────────────────────────────────────────
def update_skill_damage():
    path = os.path.join(ROOT, "db/skill_damage_db.txt")
    content = """// ============================================================================
// RAGNAROGUE – WoE TE & bRO 2024 Skill Damage Adjustments
// Estrutura: SkillName,Caster,Map,Damage against Players{,Damage against Mobs{,Damage against Bosses{,Damage against Other}}}
// Caster: BL_PC = 1
// Map: 1 = Normal, 2 = PVP, 4 = GVG/WoE, 8 = BG
// ============================================================================

// --- Lord Knight ---
// LK_SPIRALPIERCE: +25% contra monstros (simula novo cálculo de tamanho e BaseLevel)
LK_SPIRALPIERCE,1,1,0,25,20,0

// --- Crusader / Paladin ---
// PA_SHIELDCHAIN: +25% contra monstros (fórmula 300+200*lv e BaseLevel)
PA_SHIELDCHAIN,1,1,0,25,20,0
// PA_PRESSURE: +30% contra monstros (conversão para dano mágico sagrado potente)
PA_PRESSURE,1,1,0,30,25,0
// CR_GRANDCROSS: +20% contra monstros em mapas normais
CR_GRANDCROSS,1,1,0,20,15,0
// CR_HOLYCROSS: +15% contra monstros
CR_HOLYCROSS,1,1,0,15,10,0

// --- High Wizard ---
// HW_GRAVITATION: +30% contra monstros (novo dano mágico neutro por pulso)
HW_GRAVITATION,1,1,0,30,25,0
// HW_NAPALMVULCAN: +25% contra monstros (dano em área sem divisão entre alvos)
HW_NAPALMVULCAN,1,1,0,25,20,0

// --- Champion ---
// CH_PALMSTRIKE: +25% contra monstros (escala por FOR e BaseLevel)
CH_PALMSTRIKE,1,1,0,25,20,0
// CH_TIGERFIST: +20% contra monstros
CH_TIGERFIST,1,1,0,20,15,0
// CH_CHAINCRUSH: +25% contra monstros (custo de 1 esfera)
CH_CHAINCRUSH,1,1,0,25,20,0

// --- Sniper ---
// SN_SHARPSHOOTING: +25% contra monstros (crítico aprimorado e BaseLevel)
SN_SHARPSHOOTING,1,1,0,25,20,0
// SN_FALCONASSAULT: +20% contra monstros (fórmula aprimorada)
SN_FALCONASSAULT,1,1,0,20,15,0

// --- Assassin Cross ---
// ASC_METEORASSAULT: +30% contra monstros (escala por FOR e BaseLevel sem delay)
ASC_METEORASSAULT,1,1,0,30,25,0
// ASC_BREAKER: +15% contra monstros
ASC_BREAKER,1,1,0,15,10,0

// --- Minstrel / Clown ---
// CG_ARROWVULCAN: +30% contra monstros (combate dinâmico de Menestrel)
CG_ARROWVULCAN,1,1,0,30,25,0

// --- Ninja ---
// NJ_KUNAI: +25% contra monstros (dano escalado com nível da skill)
NJ_KUNAI,1,1,0,25,20,0
// NJ_KASUMIKIRI: +20% contra monstros
NJ_KASUMIKIRI,1,1,0,20,15,0
// NJ_KIRIKAGE: +20% contra monstros
NJ_KIRIKAGE,1,1,0,20,15,0
// NJ_RAIGEKISAI: +25% contra monstros
NJ_RAIGEKISAI,1,1,0,25,20,0
// NJ_HUUMA: +25% contra monstros (área 5x5 no oponente)
NJ_HUUMA,1,1,0,25,20,0
// NJ_BAKUENRYU: +20% contra monstros
NJ_BAKUENRYU,1,1,0,20,15,0
// NJ_HYOUSYOURAKU: +20% contra monstros
NJ_HYOUSYOURAKU,1,1,0,20,15,0
// NJ_SYURIKEN: +25% contra monstros
NJ_SYURIKEN,1,1,0,25,20,0

// --- Gunslinger ---
// GS_DESPERADO: +20% contra monstros para permitir leveling consistente
GS_DESPERADO,1,1,0,20,15,0
// GS_RAPIDSHOWER: +20% contra monstros
GS_RAPIDSHOWER,1,1,0,20,15,0
// GS_TRACKING: +25% contra monstros
GS_TRACKING,1,1,0,25,20,0

// --- Taekwon / Star Gladiator ---
// TK_DOWNKICK / TK_STORMKICK / TK_TURNKICK: +15% contra monstros
TK_DOWNKICK,1,1,0,15,10,0
TK_STORMKICK,1,1,0,15,10,0
TK_TURNKICK,1,1,0,15,10,0
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("  [skill_damage_db.txt] Ajustes de dano balanceados aplicados para PvM e WoE TE.")

# ─────────────────────────────────────────────────────────────────────────────
# 6. ATUALIZAÇÃO DO BATTLE.CONF e SKILL.CONF
# ─────────────────────────────────────────────────────────────────────────────
def update_battle_confs():
    # 1. battle.conf: enable_baseatk_renewal
    bconf_path = os.path.join(ROOT, "conf/battle/battle.conf")
    if os.path.isfile(bconf_path):
        with open(bconf_path, "r", encoding="utf-8") as f:
            content = f.read()
        content = content.replace("enable_baseatk: 0x9", "enable_baseatk: 0x29F")
        with open(bconf_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("  [battle.conf] Base ATK configurado para padrão suave de combate.")

    # 2. skill.conf
    sconf_path = os.path.join(ROOT, "conf/battle/skill.conf")
    if os.path.isfile(sconf_path):
        with open(sconf_path, "r", encoding="utf-8") as f:
            content = f.read()
        content = content.replace("skillrange_by_distance: 14", "skillrange_by_distance: 0")
        with open(sconf_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("  [skill.conf] Configurações de alcance e delay atualizadas.")

if __name__ == "__main__":
    print("=== Aplicando Rebalanceamento Oficial Transclasses & Ninjas (bRO 2024 / WoE TE) ===")
    update_size_fix()
    update_skill_cast()
    update_skill_db()
    update_skill_require_db()
    update_skill_damage()
    update_battle_confs()
    print("=== Rebalanceamento Concluído com Sucesso! ===")

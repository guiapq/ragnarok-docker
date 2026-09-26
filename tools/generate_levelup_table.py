#!/usr/bin/env python3
"""
RagnaRogue - Gerador Procedural da Tabela de Level Up (Pufs & Buffs)
Determinístico por Seed (WORLD_SEED / WORLD_SEED_NUMERIC).

Garante:
1. Pufs visuais únicos, sem sons em loop permanente ou ruídos irritantes.
2. Buffs discretos e equilibrados (níveis 2 a 4, não necessariamente nível máximo).
3. Remoção total de buffs restritivos (sem Defender/fiiieee, sem Corpo-Fechado, sem Frenesi, sem lentidão).
4. Determinismo estrito por nível baseado na seed do mundo.
"""

import os
import random
import sys

def load_numeric_seed():
    seed_str = os.environ.get("WORLD_SEED_NUMERIC")
    if seed_str and seed_str.strip().isdigit():
        return int(seed_str.strip())
    
    # Tenta ler do .env.rando
    env_file = ".env.rando"
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("WORLD_SEED="):
                    val = line.split("=", 1)[1].strip()
                    import hashlib
                    h = hashlib.sha256(val.encode()).hexdigest()
                    return int(h[:16], 16)
    return 1337

def main():
    seed = load_numeric_seed()
    random.seed(seed)
    print(f"Generating deterministic Level Up Table with seed: {seed}...")

    # Pool de 65 Efeitos Visuais ("Pufs") one-shot, limpos e sem loops de som
    PUFF_EFFECTS = [
        "EF_SMOKE",         # Puf clássico de fumaça
        "EF_PEONG",         # Estouro cômico / pop
        "EF_BANJJAKII",     # Brilho dourado cintilante
        "EF_ENHANCE",       # Anel de luz ascendente
        "EF_COIN",          # Moedinhas reluzentes
        "EF_BUBBLE",        # Bolhas mágicas
        "EF_FIREFLY",       # Vaga-lumes
        "EF_FLOWERLEAF",    # Pétalas esvoaçantes
        "EF_SANDWIND",      # Redemoinho suave
        "EF_HEALSP",        # Esfera azul serena
        "EF_AQUA",          # Gotículas límpidas
        "EF_SIGHT",         # Faísca orbital
        "EF_FORESTLIGHT",   # Luzes da floresta
        "EF_TORCH",         # Clarão de fogo
        "EF_SPRAYPOND",     # Respingos aquáticos
        "EF_RUWACH",        # Esfera sagrada
        "EF_FIRSTAID",      # Cruz de cura
        "EF_COLORPAPER",    # Chuva de confetes
        "EF_INCAGILITY",    # Penas velozes
        "EF_BLESSING",      # Cruz dourada
        "EF_ANGELUS",       # Círculo sagrado
        "EF_SIGNUM",        # Sinal divino
        "EF_GLORIA",        # Canto angélico
        "EF_MAGNIFICAT",    # Sino suave
        "EF_IMPOSITIO",     # Martelo da forja
        "EF_SUFFRAGIUM",    # Anéis de oração
        "EF_KYRIE",         # Asas protetoras
        "EF_SAINTWING",     # Asas celestiais
        "EF_CARTREVOLUTION",# Giro dinâmico
        "EF_TWOHANDQUICKEN",# Clarão de lâmina
        "EF_CONCENTRATION", # Foco radiante
        "EF_OVERTHRUST",    # Impacto de força
        "EF_PERFECTION",    # Engrenagem dourada
        "EF_MAXPOWER",      # Pulso de energia
        "EF_GUARD",         # Escudo prateado
        "EF_RAINBOW",       # Arco-íris mágico
        "EF_EARTHSPIKE",    # Cristais de terra
        "EF_FROSTDIVER",    # Estilhaços de gelo
        "EF_LIGHTBOLT",     # Relâmpago
        "EF_FIREBALL",      # Centelha de fogo
        "EF_SOULSTRIKE",    # Lâminas espirituais
        "EF_MAGNUMBREAK",   # Anel ígneo
        "EF_CRASHEARTH",    # Impacto telúrico
        "EF_BOWLINGBASH",   # Impacto sônico
        "EF_TURNUNDEAD",    # Feixe celestial
        "EF_JOBLVUP50",     # Coluna dourada
        "EF_HEARTCASTING",  # Corações mágicos
        "EF_VALLENTINE",    # Fitas festivas
        "EF_MINI_TETRIS",   # Blocos retrô caindo
        "EF_GHOST",         # Espírito etéreo
        "EF_BAT",           # Morcegos rápidos
        "EF_SPHEREWIND",    # Vórtice de ar
        "EF_LIGHTSPHERE",   # Supernova brilhante
        "EF_DRAGONSMOKE",   # Fumaça mística
        "EF_BABY",          # Chocalho alegre
        "EF_POTIONPILLAR",  # Pilar alquímico
        "EF_AURABLADE",     # Lâmina de energia
        "EF_LKCONCENTRATION", # Brilho do guerreiro
        "EF_PRESSURE",      # Cruz luminosa
        "EF_ASSUMPTIO",     # Bolha sagrada
        "EF_TRUESIGHT",     # Olho dourado
        "EF_MELTDOWN",      # Centelha da forja
        "EF_SOULLINK",      # Aura espiritual
        "EF_MEMORIZE",      # Runas antigas
        "EF_SANCTUARY",     # Coluna de luz pura
        "EF_STORMGUST",     # Nevasca cristalina
        "EF_LORD",          # Cúpula de relâmpagos
        "EF_METEORSTORM",   # Meteoro estelar
        "EF_GRANDCROSS",    # Cruz de luz
        "EF_HOLYCROSS",     # Cruz dupla
        "EF_PROVIDENCE",    # Escudo radiante
        "EF_DEVOTION",      # Vínculo dourado
        "EF_SOULBREAKER",   # Anéis cósmicos
        "EF_MAGICCRASHER",  # Prisma mágico
        "EF_ACIDDEMON",     # Frasco de essência
        "EF_FALCONASSAULT", # Rasante do falcão
        "EF_ELECTRIC",      # Arco voltaico
        "EF_DEVIL",         # Asas noturnas
        "EF_RO2YEAR",       # Brasão comemorativo
        "EF_TWILIGHT1",     # Brilho do entardecer
        "EF_POK_LOVE",      # Rojão coração
        "EF_TOPRANK",       # Emblema da vitória
        "EF_POK_CHRISTMAS", # Rojão cintilante
        "EF_POK_BIRTH",     # Rojão comemorativo
        "EF_POKJUK",        # Rojão festivo
    ]

    # Pool de 25 Buffs Discretos, Versáteis e Sem Sons em Loop
    BUFFS = [
        ("SC_BLESSING", 180000, 4, "Bênção Serena", "+4 FOR, +4 INT e +4 DES"),
        ("SC_INCREASEAGI", 180000, 4, "Passo Ágil", "+4 AGI e leve aceleração"),
        ("SC_GLORIA", 120000, 3, "Sorte Arcana", "+18 SOR (Crítico e Esquiva Perfeita)"),
        ("SC_MAGNIFICAT", 180000, 3, "Chama Espiritual", "Recuperação de HP e SP acelerada"),
        ("SC_IMPOSITIO", 180000, 3, "Forja Sagrada", "+15 de Ataque físico"),
        ("SC_ASSUMPTIO", 120000, 2, "Manto Assumptio", "Reduz o dano recebido em 25%"),
        ("SC_WINDWALK", 180000, 4, "Brisa dos Ventos", "+8% velocidade e +3 esquiva"),
        ("SC_CONCENTRATION", 180000, 4, "Foco do Atirador", "+5% AGI e DES"),
        ("SC_TRUESIGHT", 120000, 3, "Olhar Iluminado", "+2 Todos os atributos e +5% dano"),
        ("SC_WEAPONPERFECTION", 180000, 3, "Manejo Firme", "Dano total contra qualquer tamanho"),
        ("SC_OVERTHRUST", 180000, 3, "Golpe Pesado", "+15% de dano da arma"),
        ("SC_MAXIMIZEPOWER", 120000, 1, "Poder Estável", "Dano físico sempre no pico"),
        ("SC_ENDURE", 90000, 4, "Vontade Firme", "+4 Defesa Mágica e resistência a recuo"),
        ("SC_AURABLADE", 120000, 3, "Lâmina Cintilante", "+40 de dano puro por golpe"),
        ("SC_PROVIDENCE", 180000, 3, "Proteção Serena", "+15% resistência a Demônios e Mortos-Vivos"),
        ("SC_KAUPE", 120000, 1, "Esquiva Ilusória", "Esquiva 100% do próximo golpe físico"),
        ("SC_KAIZEL", 180000, 3, "Dádiva da Fênix", "Ressuscita com 30% de HP se abatido"),
        ("SC_MEMORIZE", 120000, 1, "Mente Rápida", "Reduz o tempo de conjuração das magias"),
        ("SC_L_LIFEPOTION", 180000, 0, "Sopro Vital", "Regeneração constante de HP a cada 5s"),
        ("SC_FOOD_STR_CASH", 180000, 4, "Alimento de Força", "+4 FOR"),
        ("SC_FOOD_AGI_CASH", 180000, 4, "Alimento de Agilidade", "+4 AGI"),
        ("SC_FOOD_VIT_CASH", 180000, 4, "Alimento de Vitalidade", "+4 VIT"),
        ("SC_FOOD_INT_CASH", 180000, 4, "Alimento de Inteligência", "+4 INT"),
        ("SC_FOOD_DEX_CASH", 180000, 4, "Alimento de Destreza", "+4 DES"),
        ("SC_FOOD_LUK_CASH", 180000, 4, "Alimento de Sorte", "+4 SOR"),
    ]

    MILESTONES = {10, 20, 30, 40, 50, 60, 70, 80, 90, 99}

    # Gera determinação nível a nível de 2 a 98 (99 é final)
    level_pufs = {}
    level_buffs = {}

    last_puf = None
    last_buff = None

    for lvl in range(2, 99):
        if lvl in MILESTONES:
            # Marcos têm efeitos especiais dedicados
            if lvl == 10:
                puf = "EF_POKJUK"
            elif lvl == 20:
                puf = "EF_COLORPAPER"
            elif lvl == 30:
                puf = "EF_SAINTWING"
            elif lvl == 40:
                puf = "EF_RAINBOW"
            elif lvl == 50:
                puf = "EF_JOBLVUP50"
            elif lvl == 60:
                puf = "EF_POTIONPILLAR"
            elif lvl == 70:
                puf = "EF_SANCTUARY"
            elif lvl == 80:
                puf = "EF_LORD"
            elif lvl == 90:
                puf = "EF_TOPRANK"
            level_pufs[lvl] = puf
            level_buffs[lvl] = -1 # Especial de marco
            last_puf = puf
            continue

        # Nível regular: sorteia puf diferente do anterior
        avail_pufs = [p for p in PUFF_EFFECTS if p != last_puf]
        puf = random.choice(avail_pufs)
        level_pufs[lvl] = puf
        last_puf = puf

        # Sorteia buff diferente do anterior
        avail_buffs = [i for i in range(len(BUFFS)) if i != last_buff]
        buff_idx = random.choice(avail_buffs)
        level_buffs[lvl] = buff_idx
        last_buff = buff_idx

    level_pufs[99] = "EF_MVP"
    level_buffs[99] = -1

    # Monta o arquivo NPC rAthena
    lines = []
    lines.append("//==============================================================================")
    lines.append("// RagnaRogue - Sistema Procedural de Efeitos & Buffs por Level Up")
    lines.append(f"// Gerado deterministicamente para WORLD_SEED_NUMERIC: {seed}")
    lines.append("//==============================================================================")
    lines.append("")
    lines.append("-	script	LevelUpPuffBuff	-1,{")
    lines.append("OnInit:")
    lines.append("\t// Tabela de Efeitos Visuais (Pufs) por Nível de Base")

    # Divide em chunks legíveis de setarray
    for start_lvl in range(2, 100, 10):
        end_lvl = min(start_lvl + 9, 99)
        chunk = [level_pufs[l] for l in range(start_lvl, end_lvl + 1)]
        lines.append(f"\tsetarray .puf_effects[{start_lvl}], {', '.join(chunk)};")

    lines.append("")
    lines.append("\t// Tabela de Buffs Determinísticos por Nível de Base (-1 = Marco Especial)")
    for start_lvl in range(2, 100, 10):
        end_lvl = min(start_lvl + 9, 99)
        chunk = [str(level_buffs[l]) for l in range(start_lvl, end_lvl + 1)]
        lines.append(f"\tsetarray .level_buffs[{start_lvl}], {', '.join(chunk)};")

    lines.append("")
    lines.append("\t// Catálogo de Buffs Discretos")
    lines.append(f"\t.total_buffs = {len(BUFFS)};")
    for i, (sc, dur, val, name, desc) in enumerate(BUFFS):
        lines.append(f"\t.buff_sc[{i}] = {sc}; .buff_dur[{i}] = {dur}; .buff_val[{i}] = {val};")
        lines.append(f"\t.buff_names$[{i}] = \"{name}\"; .buff_descs$[{i}] = \"{desc}\";")

    lines.append("\tend;")
    lines.append("")
    lines.append("OnPCBaseLvUpEvent:")
    lines.append("\t// Restaura 100% de HP e SP imediatamente ao subir de nível")
    lines.append("\tpercentheal 100, 100;")
    lines.append("")
    lines.append("\t// 1. Executa o efeito visual 'Puf' único e determinístico do nível")
    lines.append("\t.@puf = .puf_effects[BaseLevel];")
    lines.append("\tif (.@puf > 0) specialeffect2 .@puf;")
    lines.append("")
    lines.append("\t// 2. Marcos de Nível Especiais (Combos Festivos Discretos)")
    lines.append("\tif (BaseLevel == 10) {")
    lines.append("\t\tsc_start SC_BLESSING, 180000, 4;")
    lines.append("\t\tsc_start SC_INCREASEAGI, 180000, 4;")
    lines.append("\t\tdispbottom \"[Marco Nível 10!] *Puf Festivo!* Bênção Serena & Passo Ágil concedidos!\", 0x00FF88;")
    lines.append("\t\tend;")
    lines.append("\t}")
    lines.append("\tif (BaseLevel == 20) {")
    lines.append("\t\tsc_start SC_GLORIA, 180000, 3;")
    lines.append("\t\tsc_start SC_MAGNIFICAT, 180000, 3;")
    lines.append("\t\tdispbottom \"[Marco Nível 20!] *Puf Triunfal!* Sorte Arcana & Chama Espiritual concedidas!\", 0x00FF88;")
    lines.append("\t\tend;")
    lines.append("\t}")
    lines.append("\tif (BaseLevel == 30) {")
    lines.append("\t\tsc_start SC_IMPOSITIO, 180000, 3;")
    lines.append("\t\tsc_start SC_WINDWALK, 180000, 4;")
    lines.append("\t\tdispbottom \"[Marco Nível 30!] *Puf Celestial!* Forja Sagrada & Brisa dos Ventos concedidas!\", 0x00FF88;")
    lines.append("\t\tend;")
    lines.append("\t}")
    lines.append("\tif (BaseLevel == 40) {")
    lines.append("\t\tsc_start SC_ASSUMPTIO, 120000, 2;")
    lines.append("\t\tsc_start SC_CONCENTRATION, 180000, 4;")
    lines.append("\t\tdispbottom \"[Marco Nível 40!] *Puf do Arco-Íris!* Manto Assumptio & Foco do Atirador concedidos!\", 0x00FF88;")
    lines.append("\t\tend;")
    lines.append("\t}")
    lines.append("\tif (BaseLevel == 50) {")
    lines.append("\t\tsc_start SC_TRUESIGHT, 180000, 3;")
    lines.append("\t\tsc_start SC_AURABLADE, 180000, 3;")
    lines.append("\t\tdispbottom \"[Marco Nível 50 - Metade da Jornada!] *Puf Ascendente!* Olhar Iluminado & Lâmina Cintilante!\", 0x00FF88;")
    lines.append("\t\tend;")
    lines.append("\t}")
    lines.append("\tif (BaseLevel == 60) {")
    lines.append("\t\tsc_start SC_WEAPONPERFECTION, 180000, 3;")
    lines.append("\t\tsc_start SC_OVERTHRUST, 180000, 3;")
    lines.append("\t\tdispbottom \"[Marco Nível 60!] *Puf da Forja!* Manejo Firme & Golpe Pesado concedidos!\", 0x00FF88;")
    lines.append("\t\tend;")
    lines.append("\t}")
    lines.append("\tif (BaseLevel == 70) {")
    lines.append("\t\tsc_start SC_KAUPE, 180000, 1;")
    lines.append("\t\tsc_start SC_KAIZEL, 180000, 3;")
    lines.append("\t\tdispbottom \"[Marco Nível 70!] *Puf Protetor!* Esquiva Ilusória & Dádiva da Fênix concedidas!\", 0x00FF88;")
    lines.append("\t\tend;")
    lines.append("\t}")
    lines.append("\tif (BaseLevel == 80) {")
    lines.append("\t\tsc_start SC_FOOD_STR_CASH, 180000, 4;")
    lines.append("\t\tsc_start SC_FOOD_AGI_CASH, 180000, 4;")
    lines.append("\t\tsc_start SC_FOOD_VIT_CASH, 180000, 4;")
    lines.append("\t\tsc_start SC_FOOD_INT_CASH, 180000, 4;")
    lines.append("\t\tsc_start SC_FOOD_DEX_CASH, 180000, 4;")
    lines.append("\t\tsc_start SC_FOOD_LUK_CASH, 180000, 4;")
    lines.append("\t\tdispbottom \"[Marco Nível 80!] *Puf dos Titãs!* Banquete Completo de Atributos (+4 Todos Atributos)!\", 0x00FF88;")
    lines.append("\t\tend;")
    lines.append("\t}")
    lines.append("\tif (BaseLevel == 90) {")
    lines.append("\t\tsc_start SC_ASSUMPTIO, 180000, 2;")
    lines.append("\t\tsc_start SC_TRUESIGHT, 180000, 3;")
    lines.append("\t\tsc_start SC_BLESSING, 180000, 4;")
    lines.append("\t\tsc_start SC_INCREASEAGI, 180000, 4;")
    lines.append("\t\tdispbottom \"[Marco Nível 90 - Quase uma Lenda!] *Puf Campeão!* Bênçãos Sagradas ativadas!\", 0x00FF88;")
    lines.append("\t\tend;")
    lines.append("\t}")
    lines.append("\tif (BaseLevel >= 99) {")
    lines.append("\t\tspecialeffect2 EF_LEVEL99_5;")
    lines.append("\t\tspecialeffect2 EF_RAINBOW;")
    lines.append("\t\tsc_start SC_ASSUMPTIO, 300000, 3;")
    lines.append("\t\tsc_start SC_TRUESIGHT, 300000, 4;")
    lines.append("\t\tsc_start SC_BLESSING, 300000, 5;")
    lines.append("\t\tsc_start SC_INCREASEAGI, 300000, 5;")
    lines.append("\t\tsc_start SC_GLORIA, 300000, 3;")
    lines.append("\t\tsc_start SC_MAGNIFICAT, 300000, 3;")
    lines.append("\t\tsc_start SC_AURABLADE, 300000, 3;")
    lines.append("\t\tsc_start SC_KAIZEL, 300000, 3;")
    lines.append("\t\tannounce \"[LENDA ASCENDIDA] \" + strcharinfo(0) + \" alcançou o nível supremo 99!\", bc_all, 0xFFD700;")
    lines.append("\t\tdispbottom \"[NÍVEL 99 MÁXIMO!] *PUF SUPREMO!* Bênçãos da Transcendência ativadas por 5 minutos!\", 0x00FF88;")
    lines.append("\t\tend;")
    lines.append("\t}")
    lines.append("")
    lines.append("\t// 3. Nível Regular: Aplica o buff determinístico pré-computado para este nível")
    lines.append("\t.@idx = .level_buffs[BaseLevel];")
    lines.append("\tif (.@idx >= 0 && .@idx < .total_buffs) {")
    lines.append("\t\tsc_start .buff_sc[.@idx], .buff_dur[.@idx], .buff_val[.@idx];")
    lines.append("\t\tdispbottom \"[Level Up!] Nível \" + BaseLevel + \" alcançado! *Puf!* Você recebeu: \" + .buff_names$[.@idx] + \" (\" + .buff_descs$[.@idx] + \")!\", 0x00FF88;")
    lines.append("\t}")
    lines.append("\tend;")
    lines.append("")
    lines.append("OnPCJobLvUpEvent:")
    lines.append("\tspecialeffect2 EF_BANJJAKII;")
    lines.append("\tdispbottom \"[Classe Up!] Nível de Classe \" + JobLevel + \" alcançado!\", 0xFFDD00;")
    lines.append("\tend;")
    lines.append("}")
    lines.append("")

    content = "\n".join(lines)

    target_files = [
        "data/npc/custom/levelup_effects.txt",
        "data_base/npc/custom/levelup_effects.txt"
    ]

    for tf in target_files:
        os.makedirs(os.path.dirname(tf), exist_ok=True)
        with open(tf, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Generated: {tf}")

if __name__ == "__main__":
    main()

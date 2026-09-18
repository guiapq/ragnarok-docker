#!/usr/bin/env python3
"""
tools/generate_item_info_lua.py

Gera System/itemInfo.lua compatível com o roBrowser a partir do item_db.txt
do rAthena, traduzindo bônus procedurais e atributos gerados pela seed
para descrições legíveis e ricas em cores no client web.
"""

import os
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


# Dicionário de tradução de bônus do rAthena para descrições formatadas em cores do Ragnarok
BONUS_TRANSLATIONS = {
    # Atributos Principais
    r"bonus\s+bStr,([-\d]+);": ("^008800Força {val}^000000", "+"),
    r"bonus\s+bAgi,([-\d]+);": ("^008800Agilidade {val}^000000", "+"),
    r"bonus\s+bVit,([-\d]+);": ("^008800Vitalidade {val}^000000", "+"),
    r"bonus\s+bInt,([-\d]+);": ("^008800Inteligência {val}^000000", "+"),
    r"bonus\s+bDex,([-\d]+);": ("^008800Destreza {val}^000000", "+"),
    r"bonus\s+bLuk,([-\d]+);": ("^008800Sorte {val}^000000", "+"),
    r"bonus\s+bAllStats,([-\d]+);": ("^008800Todos os Atributos {val}^000000", "+"),

    # Combate
    r"bonus\s+bAtk,([-\d]+);": ("^0000FFATQ {val}^000000", "+"),
    r"bonus\s+bMatk,([-\d]+);": ("^9900FFATQM {val}^000000", "+"),
    r"bonus\s+bDef,([-\d]+);": ("^000088DEF {val}^000000", "+"),
    r"bonus\s+bMdef,([-\d]+);": ("^9900FFDEFM {val}^000000", "+"),
    r"bonus\s+bHit,([-\d]+);": ("^0000FFPrecisão {val}^000000", "+"),
    r"bonus\s+bFlee,([-\d]+);": ("^008800Esquiva {val}^000000", "+"),
    r"bonus\s+bCritical,([-\d]+);": ("^FF0000Crítico {val}^000000", "+"),
    r"bonus\s+bAspdRate,([-\d]+);": ("^FF8800Velocidade de Ataque {val}%^000000", "+"),

    # Pontos de Vida / Mana
    r"bonus\s+bMaxHP,([-\d]+);": ("^FF0000HP Máximo {val}^000000", "+"),
    r"bonus\s+bMaxSP,([-\d]+);": ("^0000FFSP Máximo {val}^000000", "+"),
    r"bonus\s+bMaxHPrate,([-\d]+);": ("^FF0000HP Máximo {val}%^000000", "+"),
    r"bonus\s+bMaxSPrate,([-\d]+);": ("^0000FFSP Máximo {val}%^000000", "+"),
    r"bonus\s+bUseSPrate,([-\d]+);": ("^CC0000Consumo de SP {val}%^000000", "+"),

    # Raças e Tamanhos
    r"bonus2\s+bAddRace,RC_DemiHuman,([-\d]+);": ("^FF4400Dano contra Humanoides {val}%^000000", "+"),
    r"bonus2\s+bAddRace,RC_Brute,([-\d]+);": ("^FF4400Dano contra Brutos {val}%^000000", "+"),
    r"bonus2\s+bAddRace,RC_Undead,([-\d]+);": ("^FF4400Dano contra Mortos-Vivos {val}%^000000", "+"),
    r"bonus2\s+bAddRace,RC_Demon,([-\d]+);": ("^FF4400Dano contra Demônios {val}%^000000", "+"),
    r"bonus2\s+bAddSize,Size_Small,([-\d]+);": ("^FF4400Dano contra monstros Pequenos {val}%^000000", "+"),
    r"bonus2\s+bAddSize,Size_Medium,([-\d]+);": ("^FF4400Dano contra monstros Médios {val}%^000000", "+"),
    r"bonus2\s+bAddSize,Size_Large,([-\d]+);": ("^FF4400Dano contra monstros Grandes {val}%^000000", "+"),
}

# Mapeamento de sprites conhecidos comuns para itens que costumam ser modificados ou injetados
RESOURCE_NAME_MAP = {
    2214: "토끼귀머리띠",   # Bunny Band
    2501: "머플러",        # Muffler
    2401: "슈즈",          # Shoes
    2828: "클립",          # Upg Clip
    2829: "클립",          # Greed Clip
    29000: "메달",         # Medal
}

# Tipos de equipamento por bitmask ou Type
ITEM_TYPES = {
    0: "Consumível",
    2: "Consumível",
    3: "Item Etc",
    4: "Arma",
    5: "Armadura / Equipamento",
    6: "Carta",
    7: "Ovo de Mascote",
    8: "Equipamento de Mascote",
    10: "Munição",
}


def parse_script_bonuses(script):
    """Extrai os bônus do script rAthena e retorna linhas descritivas formatadas."""
    if not script or not script.strip():
        return []

    lines = []
    for pattern, (template, sign) in BONUS_TRANSLATIONS.items():
        for match in re.finditer(pattern, script):
            raw_val = match.group(1)
            try:
                num = int(raw_val)
                if num > 0:
                    val_str = f"+{num}"
                else:
                    val_str = str(num)
                lines.append(template.format(val=val_str))
            except ValueError:
                lines.append(template.format(val=raw_val))
    return lines


def escape_lua_string(s):
    """Escapa strings para Lua."""
    return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')


def main():
    env = load_env()
    seed = env.get("WORLD_SEED", "default")
    root = env.get("RATHENA_ROOT", "data")
    item_db_rel = env.get("ITEM_DB_PATH", "db/re/item_db.txt")

    db_path = os.path.join(root, item_db_rel)
    if not os.path.isfile(db_path):
        # Tenta data_base se data/ não estiver populado
        fallback = os.path.join("data_base", item_db_rel)
        if os.path.isfile(fallback):
            db_path = fallback
        else:
            print(f"[ERRO] Base de itens não encontrada em {db_path} nem em {fallback}")
            sys.exit(1)

    output_dir = os.path.join(root, "System")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "itemInfo.lua")

    print(f"Lendo base de itens de: {db_path}")
    print(f"Gerando itemInfo.lua em: {output_file}")
    print(f"Seed ativa: {seed}")

    processed_count = 0
    customized_count = 0

    lua_entries = []

    with open(db_path, "r", encoding="latin-1", errors="ignore") as f:
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith("//"):
                continue

            # rAthena item_db CSV: ID,AegisName,Name,Type,Buy,Sell,Weight,ATK,DEF,Range,Slots,Job,Upper,Gender,Loc,wLV,eLV,Refineable,View,{ Script }
            if "{" in line_str:
                before_script, rest = line_str.split("{", 1)
                script = rest.split("}", 1)[0].strip()
            else:
                before_script = line_str
                script = ""

            cols = [c.strip() for c in before_script.split(",")]
            if len(cols) < 4:
                continue

            try:
                item_id = int(cols[0])
            except ValueError:
                continue

            aegis_name = cols[1] if len(cols) > 1 else f"Item_{item_id}"
            display_name = cols[2] if len(cols) > 2 else aegis_name
            try:
                item_type = int(cols[3])
            except (ValueError, IndexError):
                item_type = 3

            weight = int(cols[6]) / 10.0 if len(cols) > 6 and cols[6].isdigit() else 0.0
            atk = cols[7] if len(cols) > 7 and cols[7] else "0"
            defense = cols[8] if len(cols) > 8 and cols[8] else "0"
            slots = int(cols[10]) if len(cols) > 10 and cols[10].isdigit() else 0
            wlv = cols[15] if len(cols) > 15 and cols[15] else "0"
            elv = cols[16] if len(cols) > 16 and cols[16] else "0"
            view = int(cols[18]) if len(cols) > 18 and cols[18].isdigit() else 0

            # Nome do recurso (sprite/ícone)
            resource_name = RESOURCE_NAME_MAP.get(item_id, aegis_name)

            # Analisa bônus procedurais
            bonus_lines = parse_script_bonuses(script)

            is_procedural = (len(bonus_lines) > 0) or (item_id in [2214, 2501, 2401, 2828, 2829, 29000])

            desc_lines = []
            if is_procedural:
                customized_count += 1
                desc_lines.append(f"^FF8000[Item Procedural — Seed: {seed}]^000000")
                desc_lines.append("Forjado com energias anômalas desta rodada.")
                desc_lines.append("^777777----------------------------------------^000000")
                if bonus_lines:
                    desc_lines.append("^0000CDPropriedades Especiais:^000000")
                    for b in bonus_lines:
                        desc_lines.append(f"  {b}")
                    desc_lines.append("^777777----------------------------------------^000000")

            # Metadados de combate e uso
            type_name = ITEM_TYPES.get(item_type, "Outro")
            desc_lines.append(f"Tipo: ^000088{type_name}^000000")

            if atk != "0" and item_type == 4:
                desc_lines.append(f"Ataque: ^000088{atk}^000000")
            if defense != "0" and item_type == 5:
                desc_lines.append(f"Defesa: ^000088{defense}^000000")
            if weight > 0:
                desc_lines.append(f"Peso: ^000088{weight:g}^000000")
            if wlv != "0" and item_type == 4:
                desc_lines.append(f"Nível da Arma: ^000088{wlv}^000000")
            if elv != "0":
                desc_lines.append(f"Nível Necessário: ^000088{elv}^000000")

            # Montagem do bloco Lua para o item
            desc_entries = ",\n".join([f'            "{escape_lua_string(d)}"' for d in desc_lines])

            display_name_formatted = display_name
            if slots > 0 and not f"[{slots}]" in display_name:
                display_name_formatted = f"{display_name} [{slots}]"

            if is_procedural:
                display_name_formatted = f"^0000CD{display_name_formatted}^000000"

            lua_entry = f"""    [{item_id}] = {{
        unidentifiedDisplayName = "{escape_lua_string(display_name)}",
        unidentifiedResourceName = "{escape_lua_string(resource_name)}",
        identifiedDisplayName = "{escape_lua_string(display_name_formatted)}",
        identifiedResourceName = "{escape_lua_string(resource_name)}",
        slotCount = {slots},
        ClassNum = {view},
        unidentifiedDescriptionName = {{
            "Um item não identificado.",
            "Utilize uma Lupa para inspecionar suas propriedades."
        }},
        identifiedDescriptionName = {{
{desc_entries}
        }}
    }}"""
            lua_entries.append(lua_entry)
            processed_count += 1

    # Escreve o arquivo Lua final
    with open(output_file, "w", encoding="utf-8") as out:
        out.write("--[[ \n")
        out.write(f"  System/itemInfo.lua gerado dinamicamente para roBrowser\n")
        out.write(f"  Seed: {seed} | Total itens: {processed_count} | Procedurais: {customized_count}\n")
        out.write("--]]\n\n")
        out.write("tbl = tbl or {}\n\n")
        out.write("local procedural_items = {\n")
        out.write(",\n".join(lua_entries))
        out.write("\n}\n\n")
        out.write("-- Mescla os itens procedurais na tabela principal de itens\n")
        out.write("for k, v in pairs(procedural_items) do\n")
        out.write("    tbl[k] = v\n")
        out.write("end\n\n")
        out.write("function main()\n")
        out.write("    return true\n")
        out.write("end\n")

    print("=================================")
    print(f"Sucesso! {output_file} gerado.")
    print(f"Total de itens catalogados: {processed_count}")
    print(f"Itens procedurais com bônus destacados: {customized_count}")
    print("=================================")


if __name__ == "__main__":
    main()

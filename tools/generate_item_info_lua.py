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

# Tipos de equipamento no rAthena (mmo.hpp)
ITEM_TYPES = {
    0: "Consumível",
    2: "Consumível",
    3: "Item Etc",
    4: "Armadura / Equipamento",
    5: "Arma",
    6: "Carta",
    7: "Ovo de Mascote",
    8: "Equipamento de Mascote",
    10: "Munição",
    11: "Consumível",
    12: "Equipamento Sombrio",
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


def get_official_item_ids():
    """Lê os IDs já presentes no itemInfo.lub compilado oficial."""
    lub_paths = ["client/System/itemInfo.lub", "System/itemInfo.lub"]
    for lp in lub_paths:
        if os.path.isfile(lp):
            import struct
            ids = set()
            with open(lp, "rb") as f:
                data = f.read()
            p = 0
            while p < len(data) - 9:
                if data[p] == 3:
                    val = struct.unpack("<d", data[p+1:p+9])[0]
                    if 0 < val < 50000 and val == int(val):
                        ids.add(int(val))
                p += 1
            return ids
    return set()


def main():
    env = load_env()
    seed = env.get("WORLD_SEED", "default")
    root = env.get("RATHENA_ROOT", "data")
    item_db_rel = env.get("ITEM_DB_PATH", "db/re/item_db.txt")

    db_path = os.path.join(root, item_db_rel)
    if not os.path.isfile(db_path):
        fallback = os.path.join("data_base", item_db_rel)
        if os.path.isfile(fallback):
            db_path = fallback
        else:
            fallback_prere = os.path.join(root, "db/pre-re/item_db.txt")
            if os.path.isfile(fallback_prere):
                db_path = fallback_prere
            else:
                print(f"[ERRO] Base de itens não encontrada em {db_path}")
                sys.exit(1)

    output_files = [
        os.path.join(root, "System", "itemInfo.lua"),
        os.path.join("client", "System", "itemInfo.lua")
    ]

    official_ids = get_official_item_ids()
    print(f"Lendo base de itens de: {db_path}")
    print(f"Itens oficiais conhecidos no lub: {len(official_ids)}")
    print(f"Seed ativa: {seed}")

    processed_count = 0
    customized_count = 0
    missing_count = 0

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
            if item_id in RESOURCE_NAME_MAP:
                resource_name = RESOURCE_NAME_MAP[item_id]
            elif item_type == 6:
                resource_name = "카드"
            else:
                resource_name = aegis_name

            # Carrega blacklist de itens coreanos/quebrados
            try:
                import json
                if not hasattr(main, '_korean_bl'):
                    bl_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "korean_blacklisted_items.json")
                    with open(bl_path) as blf:
                        main._korean_bl = set(json.load(blf))
                if item_id in main._korean_bl:
                    continue
            except Exception:
                pass

            CUSTOM_ITEMS = {2214, 2501, 2401, 2828, 2829, 29000}
            is_procedural = item_id in CUSTOM_ITEMS
            is_missing = item_id not in official_ids

            if not is_procedural and not is_missing:
                continue

            bonus_lines = parse_script_bonuses(script)
            desc_lines = []

            if is_procedural:
                customized_count += 1
                desc_lines.extend([
                    f"^FF8000[Item Procedural - Seed: {seed}]^000000",
                    "Forjado com energias anomalas desta rodada.",
                    "^777777----------------------------------------^000000"
                ])
                if bonus_lines:
                    desc_lines.append("^0000CDPropriedades Especiais:^000000")
                    for b in bonus_lines:
                        desc_lines.append(f"  {b}")
                    desc_lines.append("^777777----------------------------------------^000000")
            else:
                missing_count += 1
                if bonus_lines:
                    desc_lines.append("^0000CDPropriedades:^000000")
                    for b in bonus_lines:
                        desc_lines.append(f"  {b}")
                    desc_lines.append("^777777----------------------------------------^000000")

            # Metadados de combate e uso
            type_name = ITEM_TYPES.get(item_type, "Outro")
            desc_lines.append(f"Tipo: ^000088{type_name}^000000")

            if atk != "0" and item_type == 5:
                desc_lines.append(f"Ataque: ^000088{atk}^000000")
            if defense != "0" and item_type == 4:
                desc_lines.append(f"Defesa: ^000088{defense}^000000")
            if weight > 0:
                desc_lines.append(f"Peso: ^000088{weight:g}^000000")
            if wlv != "0" and item_type == 5:
                desc_lines.append(f"Nível da Arma: ^000088{wlv}^000000")
            if elv != "0":
                desc_lines.append(f"Nível Necessário: ^000088{elv}^000000")

            # Montagem do bloco Lua para o item
            desc_entries = ",\n".join([f'            "{escape_lua_string(d)}"' for d in desc_lines])

            # Nome sem códigos de cor — roBrowser exibe o identifiedDisplayName como texto puro
            # no header do tooltip e janela de equipamentos; cor deve ficar só na description
            display_name_formatted = display_name
            if slots > 0 and not f"[{slots}]" in display_name:
                display_name_formatted = f"{display_name} [{slots}]"

            lua_entry = f"""    [{item_id}] = {{
        unidentifiedDisplayName = "{escape_lua_string(display_name)}",
        unidentifiedResourceName = "{escape_lua_string(resource_name)}",
        identifiedDisplayName = "{escape_lua_string(display_name_formatted)}",
        identifiedResourceName = "{escape_lua_string(resource_name)}",
        slotCount = {slots},
        ClassNum = {view},
        unidentifiedDescriptionName = {{
            "Item não identificado.",
            "Utilize uma Lupa para inspecionar suas propriedades."
        }},
        identifiedDescriptionName = {{
{desc_entries}
        }}
    }}"""
            lua_entries.append(lua_entry)
            processed_count += 1

    content = "--[[ \n"
    content += f"  System/itemInfo.lua gerado dinamicamente para roBrowser\n"
    content += f"  Seed: {seed} | Total itens: {processed_count} | Procedurais: {customized_count} | Adicionais: {missing_count}\n"
    content += "--]]\n\n"
    content += "tbl = tbl or {}\n\n"
    content += "local procedural_items = {\n"
    content += ",\n".join(lua_entries)
    content += "\n}\n\n"
    content += "-- Mescla os itens procedurais/adicionais na tabela principal\n"
    content += "for k, v in pairs(procedural_items) do\n"
    content += "    tbl[k] = v\n"
    content += "    if _processedItems then\n"
    content += "        _processedItems[k] = nil\n"
    content += "    end\n"
    content += "end\n\n"
    content += "function main()\n"
    content += "    return true\n"
    content += "end\n"

    for out_path in output_files:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        # Salvar em UTF-8 sem BOM; wasmoon passa strings Lua como JS strings direto para AddItem,
        # portanto o encoding do arquivo .lua nao importa para as strings processadas — apenas
        # precisa ser UTF-8 valido para o parser Lua.
        with open(out_path, "w", encoding="utf-8") as out:
            out.write(content)
        print(f"Sucesso! {out_path} gerado (utf-8).")

    print("=================================")
    print(f"Total de itens catalogados: {processed_count}")
    print(f"Itens procedurais: {customized_count}")
    print(f"Itens adicionais do item_db: {missing_count}")
    print("=================================")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
tools/generate_item_info_lua.py

Gera System/itemInfo.lua compatível com o roBrowser a partir do item_db.txt
do rAthena e do mapeamento de recursos oficiais, traduzindo bônus procedurais
e atributos gerados pela seed para descrições ricas, sem mojibake, e com
sprites devidamente mapeados para o GRF.
"""

import json
import os
import re
import sys
import unicodedata


def load_env():
    env = {}
    if os.path.isfile(".env.rando"):
        with open(".env.rando") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    env[k] = v
    return env


def strip_accents(s):
    """Remove acentos para garantir renderização limpa e sem mojibake no client."""
    if not s:
        return ""
    s = s.replace("ç", "c").replace("Ç", "C")
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


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


# Dicionário de tradução de bônus do rAthena para descrições formatadas em cores do Ragnarok
BONUS_TRANSLATIONS = {
    # Atributos Principais
    r"bonus\s+bStr,([-\d]+);": ("^008800Forca {val}^000000", "+"),
    r"bonus\s+bAgi,([-\d]+);": ("^008800Agilidade {val}^000000", "+"),
    r"bonus\s+bVit,([-\d]+);": ("^008800Vitalidade {val}^000000", "+"),
    r"bonus\s+bInt,([-\d]+);": ("^008800Inteligencia {val}^000000", "+"),
    r"bonus\s+bDex,([-\d]+);": ("^008800Destreza {val}^000000", "+"),
    r"bonus\s+bLuk,([-\d]+);": ("^008800Sorte {val}^000000", "+"),
    r"bonus\s+bAllStats,([-\d]+);": ("^008800Todos os Atributos {val}^000000", "+"),

    # Combate
    r"bonus\s+bAtk,([-\d]+);": ("^0000FFATQ {val}^000000", "+"),
    r"bonus\s+bMatk,([-\d]+);": ("^9900FFATQM {val}^000000", "+"),
    r"bonus\s+bDef,([-\d]+);": ("^000088DEF {val}^000000", "+"),
    r"bonus\s+bMdef,([-\d]+);": ("^9900FFDEFM {val}^000000", "+"),
    r"bonus\s+bHit,([-\d]+);": ("^0000FFPrecisao {val}^000000", "+"),
    r"bonus\s+bFlee,([-\d]+);": ("^008800Esquiva {val}^000000", "+"),
    r"bonus\s+bCritical,([-\d]+);": ("^FF0000Critico {val}^000000", "+"),
    r"bonus\s+bAspdRate,([-\d]+);": ("^FF8800Velocidade de Ataque {val}%^000000", "+"),
    r"bonus\s+bMatkRate,([-\d]+);": ("^9900FFATQM {val}%^000000", "+"),

    # Pontos de Vida / Mana / Custo
    r"bonus\s+bMaxHP,([-\d]+);": ("^FF0000HP Maximo {val}^000000", "+"),
    r"bonus\s+bMaxSP,([-\d]+);": ("^0000FFSP Maximo {val}^000000", "+"),
    r"bonus\s+bMaxHPrate,([-\d]+);": ("^FF0000HP Maximo {val}%^000000", "+"),
    r"bonus\s+bMaxSPrate,([-\d]+);": ("^0000FFSP Maximo {val}%^000000", "+"),
    r"bonus\s+bUseSPrate,([-\d]+);": ("^CC0000Consumo de SP {val}%^000000", "+"),

    # Racas e Tamanhos (Dano)
    r"bonus2\s+bAddRace,RC_DemiHuman,([-\d]+);": ("^FF4400Dano contra Humanoides {val}%^000000", "+"),
    r"bonus2\s+bAddRace,RC_Player,([-\d]+);": ("^FF4400Dano contra Jogadores {val}%^000000", "+"),
    r"bonus2\s+bAddRace,RC_Brute,([-\d]+);": ("^FF4400Dano contra Brutos {val}%^000000", "+"),
    r"bonus2\s+bAddRace,RC_Undead,([-\d]+);": ("^FF4400Dano contra Mortos-Vivos {val}%^000000", "+"),
    r"bonus2\s+bAddRace,RC_Demon,([-\d]+);": ("^FF4400Dano contra Demonios {val}%^000000", "+"),
    r"bonus2\s+bAddRace,RC_Insect,([-\d]+);": ("^FF4400Dano contra Insetos {val}%^000000", "+"),
    r"bonus2\s+bAddRace,RC_Fish,([-\d]+);": ("^FF4400Dano contra Peixes {val}%^000000", "+"),
    r"bonus2\s+bAddRace,RC_Dragon,([-\d]+);": ("^FF4400Dano contra Dragoes {val}%^000000", "+"),
    r"bonus2\s+bAddRace,RC_Plant,([-\d]+);": ("^FF4400Dano contra Plantas {val}%^000000", "+"),
    r"bonus2\s+bAddRace,RC_Formless,([-\d]+);": ("^FF4400Dano contra Amorfo {val}%^000000", "+"),
    r"bonus2\s+bAddRace,RC_Angel,([-\d]+);": ("^FF4400Dano contra Anjos {val}%^000000", "+"),
    r"bonus2\s+bMagicAddRace,RC_DemiHuman,([-\d]+);": ("^FF4400Dano Magico contra Humanoides {val}%^000000", "+"),
    r"bonus2\s+bMagicAddRace,RC_Player,([-\d]+);": ("^FF4400Dano Magico contra Jogadores {val}%^000000", "+"),

    # Resistencia a Racas
    r"bonus2\s+bSubRace,RC_DemiHuman,([-\d]+);": ("^008800Resistencia a Humanoides {val}%^000000", "+"),
    r"bonus2\s+bSubRace,RC_Player,([-\d]+);": ("^008800Resistencia a Jogadores {val}%^000000", "+"),
    r"bonus2\s+bSubRace,RC_Brute,([-\d]+);": ("^008800Resistencia a Brutos {val}%^000000", "+"),
    r"bonus2\s+bSubRace,RC_Undead,([-\d]+);": ("^008800Resistencia a Mortos-Vivos {val}%^000000", "+"),
    r"bonus2\s+bSubRace,RC_Demon,([-\d]+);": ("^008800Resistencia a Demonios {val}%^000000", "+"),
    r"bonus2\s+bSubRace,RC_Angel,([-\d]+);": ("^008800Resistencia a Anjos {val}%^000000", "+"),

    # Tamanhos
    r"bonus2\s+bAddSize,Size_Small,([-\d]+);": ("^FF4400Dano contra monstros Pequenos {val}%^000000", "+"),
    r"bonus2\s+bAddSize,Size_Medium,([-\d]+);": ("^FF4400Dano contra monstros Medios {val}%^000000", "+"),
    r"bonus2\s+bAddSize,Size_Large,([-\d]+);": ("^FF4400Dano contra monstros Grandes {val}%^000000", "+"),
    r"bonus2\s+bSubSize,Size_Small,([-\d]+);": ("^008800Resistencia a Pequenos {val}%^000000", "+"),
    r"bonus2\s+bSubSize,Size_Medium,([-\d]+);": ("^008800Resistencia a Medios {val}%^000000", "+"),
    r"bonus2\s+bSubSize,Size_Large,([-\d]+);": ("^008800Resistencia a Grandes {val}%^000000", "+"),
    r"bonus\s+bNoSizeFix;": ("^0000FFAnula penalidade de tamanho da arma^000000", ""),

    # Propriedade Elemental da Arma
    r"bonus\s+bAtkEle,Ele_Water;": ("^0000FFArma com Propriedade Agua^000000", ""),
    r"bonus\s+bAtkEle,Ele_Earth;": ("^008800Arma com Propriedade Terra^000000", ""),
    r"bonus\s+bAtkEle,Ele_Fire;": ("^FF0000Arma com Propriedade Fogo^000000", ""),
    r"bonus\s+bAtkEle,Ele_Wind;": ("^008800Arma com Propriedade Vento^000000", ""),
    r"bonus\s+bAtkEle,Ele_Poison;": ("^9900FFArma com Propriedade Veneno^000000", ""),
    r"bonus\s+bAtkEle,Ele_Holy;": ("^FFD700Arma com Propriedade Sagrado^000000", ""),
    r"bonus\s+bAtkEle,Ele_Dark;": ("^660066Arma com Propriedade Sombrio^000000", ""),
    r"bonus\s+bAtkEle,Ele_Ghost;": ("^6666CCArma com Propriedade Fantasma^000000", ""),
    r"bonus\s+bAtkEle,Ele_Undead;": ("^880000Arma com Propriedade Maldito^000000", ""),

    # Resistencia Elemental
    r"bonus\d*\s+bSubEle,Ele_Neutral,([-\d]+)[^;]*;": ("^008800Resistencia a Neutro {val}%^000000", "+"),
    r"bonus\d*\s+bSubEle,Ele_Water,([-\d]+)[^;]*;": ("^008800Resistencia a Agua {val}%^000000", "+"),
    r"bonus\d*\s+bSubEle,Ele_Earth,([-\d]+)[^;]*;": ("^008800Resistencia a Terra {val}%^000000", "+"),
    r"bonus\d*\s+bSubEle,Ele_Fire,([-\d]+)[^;]*;": ("^008800Resistencia a Fogo {val}%^000000", "+"),
    r"bonus\d*\s+bSubEle,Ele_Wind,([-\d]+)[^;]*;": ("^008800Resistencia a Vento {val}%^000000", "+"),
    r"bonus\d*\s+bSubEle,Ele_Poison,([-\d]+)[^;]*;": ("^008800Resistencia a Veneno {val}%^000000", "+"),
    r"bonus\d*\s+bSubEle,Ele_Holy,([-\d]+)[^;]*;": ("^008800Resistencia a Sagrado {val}%^000000", "+"),
    r"bonus\d*\s+bSubEle,Ele_Dark,([-\d]+)[^;]*;": ("^008800Resistencia a Sombrio {val}%^000000", "+"),
    r"bonus\d*\s+bSubEle,Ele_Ghost,([-\d]+)[^;]*;": ("^008800Resistencia a Fantasma {val}%^000000", "+"),
    r"bonus\d*\s+bSubEle,Ele_Undead,([-\d]+)[^;]*;": ("^008800Resistencia a Maldito {val}%^000000", "+"),

    # Utilidades e Efeitos Especiais
    r"bonus\s+bUnbreakableWeapon;": ("^008800Arma Indestrutivel em batalha^000000", ""),
    r"bonus\s+bUnbreakableArmor;": ("^008800Armadura Indestrutivel em batalha^000000", ""),
    r"bonus\s+bUnbreakableGarment;": ("^008800Capa Indestrutivel em batalha^000000", ""),
    r"bonus\s+bNoKnockback;": ("^008800Imune a empurrao (Knockback)^000000", ""),
    r"bonus\s+bNoCastCancel;": ("^008800Conjuracao ininterrupta^000000", ""),
    r"bonus\s+bSpeedRate,([-\d]+);": ("^008800Velocidade de Movimento {val}%^000000", "+"),
    r"bonus\s+bDoubleRate,([-\d]+);": ("^FF0000Chance de Ataque Duplo {val}%^000000", "+"),
    r"bonus\s+bSplashRange,([-\d]+);": ("^FF0000Ataque em Area (Splash)^000000", ""),
    r"bonus\s+bHealPower,([-\d]+);": ("^008800Eficacia de Cura {val}%^000000", "+"),
    r"bonus2\s+bAddClass,Class_All,([-\d]+);": ("^FF4400Dano fisico contra todos os alvos {val}%^000000", "+"),
}

# Tipos de equipamento no rAthena (mmo.hpp)
ITEM_TYPES = {
    0: "Consumivel",
    2: "Consumivel",
    3: "Item Etc",
    4: "Armadura / Equipamento",
    5: "Arma",
    6: "Carta",
    7: "Ovo de Mascote",
    8: "Equipamento de Mascote",
    10: "Municao",
    11: "Consumivel",
    12: "Equipamento Sombrio",
}


def parse_script_bonuses(script):
    """Extrai os bônus do script rAthena e retorna linhas descritivas formatadas."""
    if not script or not script.strip():
        return []

    lines = []
    for pattern, (template, sign) in BONUS_TRANSLATIONS.items():
        for match in re.finditer(pattern, script):
            if match.groups():
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
            else:
                lines.append(template)
    return lines


def escape_lua_string(s):
    """Escapa strings para Lua."""
    return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')


def format_resource_name(raw_res):
    """Retorna a string Lua para o resourceName correspondente ao índice do GRF.
    Os nomes de arquivos no GRF estão indexados na codificação coreana legada (CP949/Windows-1252).
    Emitindo diretamente os bytes Latin-1 sem double-encoding UTF-8, o roBrowser
    localiza a textura (.bmp) diretamente no data.grf em memória, sem erro 404.
    """
    if not raw_res:
        return '""'
    raw_bytes = raw_res.encode('latin1')
    escaped = "".join(f"\\{b:03d}" for b in raw_bytes)
    return f'"{escaped}"'



def load_raw_official_resource_names():
    """Carrega official_resource_names.json preservando os bytes brutos latin1."""
    res_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "official_resource_names.json")
    if not os.path.isfile(res_path):
        return {}
    with open(res_path, "r", encoding="latin1") as f:
        return json.load(f)


def load_ptbr_names():
    ptbr_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "valid_ptbr_items.json")
    if os.path.isfile(ptbr_path):
        with open(ptbr_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def main():
    env = load_env()
    seed = os.environ.get("WORLD_SEED") or env.get("WORLD_SEED", "zawarudo")
    root = os.environ.get("RATHENA_ROOT") or env.get("RATHENA_ROOT", "data")
    item_db_rel = os.environ.get("ITEM_DB_PATH") or env.get("ITEM_DB_PATH", "db/pre-re/item_db.txt")

    db_path = os.path.join(root, item_db_rel)
    if not os.path.isfile(db_path):
        fallback = os.path.join("data_base", item_db_rel)
        if os.path.isfile(fallback):
            db_path = fallback
        else:
            print(f"[ERRO] Base de itens não encontrada em {db_path}")
            sys.exit(1)

    output_files = [
        os.path.join(root, "System", "itemInfo.lua"),
        os.path.join("client", "System", "itemInfo.lua")
    ]
    if os.environ.get("OUTPUT_ITEM_INFO"):
        output_files.append(os.environ["OUTPUT_ITEM_INFO"])

    raw_res_map = load_raw_official_resource_names()
    ptbr_names = load_ptbr_names()

    print(f"Lendo base de itens de: {db_path}")
    print(f"Recursos oficiais mapeados: {len(raw_res_map)}")
    print(f"Nomes em Portugues carregados: {len(ptbr_names)}")
    print(f"Seed ativa: {seed}")

    procedural_entries = []
    normal_entries = []

    with open(db_path, "r", encoding="latin-1", errors="ignore") as f:
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith("//"):
                continue

            before_script, script, _ = extract_first_script(line_str)

            cols = [c.strip() for c in before_script.split(",")]
            if len(cols) < 4:
                continue

            try:
                item_id = int(cols[0])
            except ValueError:
                continue

            aegis_name = cols[1] if len(cols) > 1 else f"Item_{item_id}"
            csv_display_name = cols[2] if len(cols) > 2 else aegis_name
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

            str_id = str(item_id)

            # Nome limpo sem acentos para garantir zero mojibake
            raw_display = ptbr_names.get(str_id, csv_display_name)
            # Remove qualquer sufixo [X] existente no nome para não duplicar, pois roBrowser já adiciona
            raw_display = re.sub(r"\s*\[\d+\]\s*$", "", raw_display)
            clean_display_name = strip_accents(raw_display)

            # Mapeamento do sprite no GRF
            raw_resource = raw_res_map.get(str_id)
            if raw_resource:
                res_literal = format_resource_name(raw_resource)
            elif item_type == 6:
                # Carta genérica
                res_literal = format_resource_name("\xc4\xab\xb5\xe5")
            else:
                res_literal = f'"{escape_lua_string(aegis_name)}"'

            type_name = ITEM_TYPES.get(item_type, "Outro")
            bonus_lines = parse_script_bonuses(script)
            is_gear = item_type in (4, 5)

            try:
                buy_price = int(cols[4]) if len(cols) > 4 and cols[4].isdigit() else 0
            except ValueError:
                buy_price = 0

            desc_lines = []
            if is_gear:
                if item_id in (1530, 2383, 2410, 2541, 2629, 2630):
                    desc_lines.extend([
                        "^FFD700[Artefato Divino Lendario]^000000",
                        "Forjado com os poderes dos deuses no inicio das eras.",
                        "^777777----------------------------------------^000000"
                    ])
                elif buy_price >= 1000000:
                    desc_lines.extend([
                        "^9900FF[Tier 4 - Reliquia Sagrada]^000000",
                        "Obra-prima impecavel. Maximo poder sem debuffs.",
                        "^777777----------------------------------------^000000"
                    ])
                elif buy_price >= 200000:
                    desc_lines.extend([
                        "^FF4500[Tier 3 - Poder Proibido]^000000",
                        "Poder extraordinario equilibrado por penalidades severas.",
                        "^777777----------------------------------------^000000"
                    ])
                elif buy_price >= 30000:
                    desc_lines.extend([
                        "^0088FF[Tier 2 - Aprimorado]^000000",
                        "Equipamento avancado para aventureiros experientes.",
                        "^777777----------------------------------------^000000"
                    ])
                else:
                    desc_lines.extend([
                        "^00AA00[Tier 1 - Basico]^000000",
                        "Equipamento inicial confiavel e acessivel.",
                        "^777777----------------------------------------^000000"
                    ])
                if bonus_lines:
                    desc_lines.append("^0000CDPropriedades Especiais:^000000")
                    for b in bonus_lines:
                        desc_lines.append(f"  {b}")
                    desc_lines.append("^777777----------------------------------------^000000")

                desc_lines.append(f"Tipo: ^000088{type_name}^000000")
                if atk != "0" and item_type == 5:
                    desc_lines.append(f"Ataque: ^000088{atk}^000000")
                if defense != "0" and item_type == 4:
                    desc_lines.append(f"Defesa: ^000088{defense}^000000")
                if weight > 0:
                    desc_lines.append(f"Peso: ^000088{weight:g}^000000")
                if wlv != "0" and item_type == 5:
                    desc_lines.append(f"Nivel da Arma: ^000088{wlv}^000000")
                if elv != "0":
                    desc_lines.append(f"Nivel Necessario: ^000088{elv}^000000")
            else:
                desc_lines.append("Item oficial do Ragnarok Online.")
                if bonus_lines:
                    desc_lines.append("^777777----------------------------------------^000000")
                    desc_lines.append("^0000CDEfeitos:^000000")
                    for b in bonus_lines:
                        desc_lines.append(f"  {b}")
                desc_lines.append("^777777----------------------------------------^000000")
                desc_lines.append(f"Tipo: ^000088{type_name}^000000")
                if weight > 0:
                    desc_lines.append(f"Peso: ^000088{weight:g}^000000")

            desc_entries = ",\n".join([f'            "{escape_lua_string(d)}"' for d in desc_lines])

            entry = f"""    [{item_id}] = {{
        unidentifiedDisplayName = "{escape_lua_string(clean_display_name)}",
        unidentifiedResourceName = {res_literal},
        identifiedDisplayName = "{escape_lua_string(clean_display_name)}",
        identifiedResourceName = {res_literal},
        slotCount = {slots},
        ClassNum = {view},
        unidentifiedDescriptionName = {{
            "Item nao identificado.",
            "Utilize uma Lupa para inspecionar suas propriedades."
        }},
        identifiedDescriptionName = {{
{desc_entries}
        }}
    }}"""
            if is_gear:
                procedural_entries.append(entry)
            else:
                normal_entries.append(entry)

    print(f"Total de itens gerados do item_db:")
    print(f" - Equipamentos procedurais: {len(procedural_entries)}")
    print(f" - Itens normais / consumiveis: {len(normal_entries)}")

    content = "--[[ \n"
    content += f"  System/itemInfo.lua gerado dinamicamente para roBrowser\n"
    content += f"  Seed: {seed} | Procedurais: {len(procedural_entries)} | Normais: {len(normal_entries)}\n"
    content += "  Este arquivo e auto-suficiente.\n"
    content += "--]]\n\n"
    content += "tbl = tbl or {}\n\n"

    # Itens normais do item_db
    if normal_entries:
        content += "-- Itens normais\n"
        content += "local normal_items = {\n"
        content += ",\n".join(normal_entries)
        content += "\n}\n"
        content += "for k, v in pairs(normal_items) do\n"
        content += "    tbl[k] = v\n"
        content += "end\n\n"

    # Itens procedurais
    if procedural_entries:
        content += "-- Itens procedurais\n"
        content += "local procedural_items = {\n"
        content += ",\n".join(procedural_entries)
        content += "\n}\n"
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
        with open(out_path, "w", encoding="utf-8") as out:
            out.write(content)
        print(f"Sucesso! {out_path} gerado (utf-8).")


if __name__ == "__main__":
    main()

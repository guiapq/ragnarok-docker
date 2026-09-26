#!/usr/bin/env python3
"""
tools/import_renewal_gears.py

Importa cumulativamente todos os equipamentos e armas da Renovação (re/item_db.txt)
suportados pela GRF ativa (mapeados em official_resource_names.json) para a base Pre-RE:
- Itens de 3rd viram equipáveis pelas classes 2-1 e 2-2 correspondentes (Class |= 3).
- Requisito de nível base superior a 99 vira 90 (eLV > 99 -> eLV = 90).
- Preserva todos os efeitos, slots, scripts e propriedades originais.
"""

import json
import os
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


def extract_first_script(line):
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


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    res_path = os.path.join(root, "tools", "official_resource_names.json")
    if not os.path.isfile(res_path):
        print(f"[ERRO] {res_path} não encontrado!")
        sys.exit(1)

    with open(res_path, "r", encoding="latin1") as f:
        grf_resources = set(json.load(f).keys())

    pre_re_db = os.path.join(root, "data_base", "db", "pre-re", "item_db.txt")
    target_data_db = os.path.join(root, "data", "db", "pre-re", "item_db.txt")
    re_db = os.path.join(root, "data_base", "db", "re", "item_db.txt")

    if not os.path.isfile(pre_re_db) or not os.path.isfile(re_db):
        print("[ERRO] Arquivos de item_db não encontrados!")
        sys.exit(1)

    # Backup vanilla original da base
    bak_base = pre_re_db + ".vanilla_pre_re"
    if not os.path.isfile(bak_base):
        shutil.copyfile(pre_re_db, bak_base)
        print(f"  [Backup criado] {bak_base}")
    source_pre_re = bak_base

    pre_re_lines = []
    pre_re_ids = set()

    with open(source_pre_re, "r", encoding="latin-1", errors="ignore") as f:
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith("//"):
                pre_re_lines.append(line)
                continue

            before_script, script, after_script = extract_first_script(line_str)
            cols = [c.strip() for c in before_script.split(",")]
            if len(cols) >= 17 and cols[0].isdigit():
                iid = int(cols[0])
                pre_re_ids.add(iid)

                # Ajuste de eLV > 99 -> 90 para itens vanilla que porventura excedessem
                try:
                    elv = int(cols[16]) if cols[16].isdigit() else 0
                    if elv > 99:
                        cols[16] = "90"
                except (ValueError, IndexError):
                    pass

                # Se for equipamento de 3rd existente, libera para 2-1 e 2-2
                try:
                    class_val = int(cols[12])
                    if class_val in (8, 16, 24, 32, 40, 48, 56):
                        cols[12] = str(class_val | 3)
                except (ValueError, IndexError):
                    pass

                new_before = ",".join(cols)
                script_body = f" {script} " if script else ""
                pre_re_lines.append(f"{new_before}{{{script_body}}}{after_script}\n")
            else:
                pre_re_lines.append(line)

    print(f"Itens Pre-RE base originais: {len(pre_re_ids)}")

    imported_weapons = 0
    imported_armors = 0
    new_lines = []

    with open(re_db, "r", encoding="latin-1", errors="ignore") as f:
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith("//"):
                continue

            before_script, script, after_script = extract_first_script(line_str)
            cols = [c.strip() for c in before_script.split(",")]
            if len(cols) < 17 or not cols[0].isdigit():
                continue

            iid = int(cols[0])
            if iid in pre_re_ids:
                continue

            try:
                itype = int(cols[3])
            except ValueError:
                continue

            # Apenas Armaduras/Equipamentos (4) e Armas (5)
            if itype not in (4, 5):
                continue

            # Suportado pelo GRF?
            if str(iid) not in grf_resources:
                continue

            # 1. Ajuste de 3rd -> Equipável por 2-1 e 2-2 correspondente (Class |= 3)
            try:
                class_val = int(cols[12])
                cols[12] = str(class_val | 3)
            except (ValueError, IndexError):
                pass

            # 2. Ajuste de Nível > 99 -> 90
            try:
                elv = int(cols[16]) if cols[16].isdigit() else 0
                if elv > 99:
                    cols[16] = "90"
            except (ValueError, IndexError):
                pass

            if itype == 5:
                imported_weapons += 1
            else:
                imported_armors += 1

            new_before = ",".join(cols)
            script_body = f" {script} " if script else ""
            new_lines.append(f"{new_before}{{{script_body}}}{after_script}\n")

    print(f"Armas da Renovação importadas:       {imported_weapons}")
    print(f"Equipamentos da Renovação importados: {imported_armors}")
    print(f"Total de novos equipamentos:         {imported_weapons + imported_armors}")

    all_lines = pre_re_lines + [
        "\n// =============================================================================\n",
        "// RENEWAL EXPANSION WEAPONS & EQUIPMENTS (GRF SUPPORTED - REWORK)\n",
        "// =============================================================================\n"
    ] + new_lines

    # Salva na base de dados
    with open(pre_re_db, "w", encoding="latin-1") as f:
        f.writelines(all_lines)
    print(f"  ✓ Salvo em {pre_re_db}")

    # Salva no data/db ativo
    os.makedirs(os.path.dirname(target_data_db), exist_ok=True)
    with open(target_data_db, "w", encoding="latin-1") as f:
        f.writelines(all_lines)
    print(f"  ✓ Salvo em {target_data_db}")

    # Sincroniza arquivos de backup/originais para os outros scripts
    for extra_file in [target_data_db + ".affix_orig", target_data_db + ".price_backup"]:
        with open(extra_file, "w", encoding="latin-1") as f:
            f.writelines(all_lines)
        print(f"  ✓ Atualizado {extra_file}")

    print("Importação cumulativa concluída com sucesso!")


if __name__ == "__main__":
    main()

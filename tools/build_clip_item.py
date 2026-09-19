#!/usr/bin/env python3

import subprocess
import os
import sys


def load_env():
    env = {}
    with open(".env.rando") as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                env[k] = v
    return env


def count_blocks(line):
    return line.count("{")


def main():
    env = load_env()

    ROOT = env["RATHENA_ROOT"]
    ITEM_DB = env["ITEM_DB_PATH"]

    DB = f"{ROOT}/{ITEM_DB}"

    TARGET_ID = "2607"  # Clip [1] (Pré-Renewal)

    if not os.path.isfile(DB):
        print(f"[ERRO] DB não encontrado: {DB}")
        sys.exit(1)

    # gera script random
    try:
        script = subprocess.check_output(
            ["python3", "tools/generate_medal.py"]
        ).decode().strip()
    except Exception as e:
        print("[ERRO] Falha ao gerar script:", e)
        sys.exit(1)

    lines = []
    found = False

    with open(DB) as f:
        for line in f:

            # mantém comentários
            if line.startswith("//") or line.strip() == "":
                lines.append(line)
                continue

            if line.startswith(f"{TARGET_ID},"):
                found = True

                try:
                    before, rest = line.split("{", 1)
                    # Mantém o bônus nativo do Clip (bonus bMaxSP,10;) e anexa o bônus da seed
                    base_script = "bonus bMaxSP,10;"
                    combined = f"{base_script} {script}".strip()

                    new_line = f"{before}{{ {combined} }},{{}},{{}}\n"

                except Exception:
                    print("[WARN] Falha ao parsear linha, sobrescrevendo script...")
                    before = line.split("{", 1)[0]
                    new_line = f"{before}{{ {script} }},{{}},{{}}\n"

                # validação de segurança
                if count_blocks(new_line) < 3:
                    print("[ERRO] Linha gerada inválida:")
                    print(new_line)
                    sys.exit(1)

                lines.append(new_line)

            else:
                lines.append(line)

    if not found:
        print(f"[ERRO] Item {TARGET_ID} não encontrado no DB!")
        sys.exit(1)

    with open(DB, "w") as f:
        f.writelines(lines)

    print("=================================")
    print("Presilha [1] modificada com sucesso!")
    print(f"Item ID: {TARGET_ID}")
    print("Script aplicado:")
    print(script)
    print("=================================")


if __name__ == "__main__":
    main()

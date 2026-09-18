#!/usr/bin/env python3
"""Validação básica pós-randomização."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent

def find_db_file(base_dir, name):
    for ext in [".txt", ".yml"]:
        p = base_dir / f"{name}{ext}"
        if p.exists() and p.stat().st_size > 0:
            return p
    return None


def fail(msg: str) -> None:
    print(f"[SANITY][ERRO] {msg}")
    sys.exit(1)


def main() -> None:
    print("[SANITY] Iniciando validações de mundo...")

    re_dir = ROOT / "data" / "db" / "re"
    item_file = find_db_file(re_dir, "item_db")
    if not item_file:
        fail(f"item_db (.txt ou .yml) ausente ou vazio em {re_dir}")

    mob_file = find_db_file(re_dir, "mob_db")
    if not mob_file:
        fail(f"mob_db (.txt ou .yml) ausente ou vazio em {re_dir}")

    scripts_conf = ROOT / "data" / "npc" / "scripts_athena.conf"
    if not scripts_conf.exists() or scripts_conf.stat().st_size == 0:
        fail(f"scripts_athena.conf ausente ou vazio em {scripts_conf}")

    item_info_lua = ROOT / "data" / "System" / "itemInfo.lua"
    if not item_info_lua.exists() or item_info_lua.stat().st_size == 0:
        fail(f"itemInfo.lua ausente ou vazio em {item_info_lua}")

    print(f"[SANITY] item_db validado: {item_file.name}")
    print(f"[SANITY] mob_db validado: {mob_file.name}")
    print(f"[SANITY] itemInfo.lua validado: {item_info_lua.name}")
    print("[SANITY] OK - todas as validações de mundo concluídas com sucesso.")


if __name__ == "__main__":
    main()

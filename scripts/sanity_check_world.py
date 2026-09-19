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

    telemetry_file = ROOT / "data" / "npc" / "custom" / "event_telemetry.txt"
    if not telemetry_file.exists() or telemetry_file.stat().st_size == 0:
        fail(f"event_telemetry.txt ausente ou vazio em {telemetry_file}")

    # Valida que o ATK das armas não foi corrompido ou zerado
    if item_file.suffix == ".txt":
        with open(item_file, "r", encoding="latin-1", errors="ignore") as f:
            for line in f:
                if line.startswith("1101,"):
                    cols = line.split(",")
                    if len(cols) > 7 and cols[7] in ("0", ""):
                        fail("ATK da espada básica (1101) está zerado em item_db.txt!")
                    break

    print(f"[SANITY] item_db validado: {item_file.name}")
    print(f"[SANITY] mob_db validado: {mob_file.name}")
    print(f"[SANITY] itemInfo.lua validado: {item_info_lua.name}")
    print(f"[SANITY] event_telemetry.txt validado: {telemetry_file.name}")
    print("[SANITY] OK - todas as validações de mundo concluídas com sucesso.")


if __name__ == "__main__":
    main()

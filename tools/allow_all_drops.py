#!/usr/bin/env python3
"""
tools/allow_all_drops.py

Permite que todos os itens possam ser:
1. Derrubados no chão / jogados fora (Drop) -> remove bit 1 da TradeMask
2. Vendidos em lojas de NPCs -> remove bit 8 da TradeMask
Aplica tanto em db/pre-re/item_trade.txt quanto db/re/item_trade.txt.
"""

import os
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


def process_trade_file(filepath):
    if not os.path.isfile(filepath):
        return 0

    lines = []
    modified_count = 0

    with open(filepath, "r", encoding="latin-1", errors="ignore") as f:
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith("//"):
                lines.append(line)
                continue

            # Formato: ItemID,TradeMask,GroupOverride // Comment
            parts = line_str.split("//", 1)
            comment = f" //{parts[1]}" if len(parts) > 1 else ""
            data_part = parts[0].strip()

            cols = [c.strip() for c in data_part.split(",")]
            if len(cols) >= 2:
                try:
                    trade_mask = int(cols[1])
                    # Bit 1 = item não pode ser derrubado (1 - item can't be dropped)
                    # Bit 8 = item não pode ser vendido a NPCs (8 - item can't be sold to npcs)
                    if (trade_mask & 1) or (trade_mask & 8):
                        trade_mask &= ~(1 | 8)  # Remove drop e sell restrictions
                        cols[1] = str(trade_mask)
                        modified_count += 1
                        line = f"{','.join(cols)}{comment}\n"
                except ValueError:
                    pass

            lines.append(line if line.endswith("\n") else line + "\n")

    with open(filepath, "w", encoding="latin-1") as f:
        f.writelines(lines)

    return modified_count


def main():
    env = load_env()
    root = env.get("RATHENA_ROOT", "data_base")

    targets = [
        f"{root}/db/pre-re/item_trade.txt",
        f"{root}/db/re/item_trade.txt",
        "data_base/db/pre-re/item_trade.txt",
        "data_base/db/re/item_trade.txt",
        "data/db/pre-re/item_trade.txt",
        "data/db/re/item_trade.txt",
    ]

    seen = set()
    total_modified = 0

    print("Removendo restrições de drop no chão (bit 1) e venda em NPCs (bit 8) em item_trade.txt...")

    for path in targets:
        real_path = os.path.realpath(path) if os.path.exists(path) else path
        if os.path.isfile(path) and real_path not in seen:
            seen.add(real_path)
            mod = process_trade_file(path)
            total_modified += mod
            print(f"  [item_trade] {path}: {mod} itens liberados para drop e venda.")

    print(f"Sucesso: {total_modified} itens liberados no total.")


if __name__ == "__main__":
    main()


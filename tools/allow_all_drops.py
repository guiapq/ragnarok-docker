#!/usr/bin/env python3
"""
tools/allow_all_drops.py

Permite que todos os itens possam ser derrubados no chão (Drop)
removendo a restrição de drop (bit 1 da TradeMask) em db/re/item_trade.txt.
NÃO altera item_db.txt para evitar corrupção do valor de Ataque (ATK).
"""

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


def main():
    env = load_env()
    root = env.get("RATHENA_ROOT", "data")
    trade_db_path = f"{root}/db/re/item_trade.txt"

    if not os.path.isfile(trade_db_path):
        fallback = "data_base/db/re/item_trade.txt"
        if os.path.isfile(fallback):
            trade_db_path = fallback
        else:
            print(f"[WARN] item_trade.txt não encontrado em {trade_db_path}. Pulando.")
            return

    print("Removendo restrições de drop em item_trade.txt...")

    lines = []
    modified_count = 0

    with open(trade_db_path, "r", encoding="latin-1", errors="ignore") as f:
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
                    if trade_mask & 1:
                        trade_mask &= ~1  # Remove a restrição de drop
                        cols[1] = str(trade_mask)
                        modified_count += 1
                        line = f"{','.join(cols)}{comment}\n"
                except ValueError:
                    pass

            lines.append(line if line.endswith("\n") else line + "\n")

    with open(trade_db_path, "w", encoding="latin-1") as f:
        f.writelines(lines)

    print(f"Sucesso: {modified_count} itens tiveram sua restrição de drop removida.")


if __name__ == "__main__":
    main()

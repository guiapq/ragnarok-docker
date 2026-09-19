#!/usr/bin/env python3
"""
tools/adjust_starter_weights.py

Ajusta o peso dos itens consumíveis de sobrevivência e starter items em db/pre-re/item_db.txt
para que o Aprendiz não nasça com sobrepeso (overweight penalty) e possa regenerar HP/SP livremente.
"""

import os
import sys

def load_env():
    env = {}
    for env_file in [".env", ".env.rando"]:
        if os.path.isfile(env_file):
            with open(env_file) as f:
                for line in f:
                    if "=" in line and not line.startswith("#"):
                        k, v = line.strip().split("=", 1)
                        env[k] = v
    return env

# Pesos otimizados para roguelike (em décimos de peso rAthena: 10 = 1.0 de peso no client)
LIGHT_WEIGHTS = {
    501: 10,   # Poção Vermelha (Red Potion) - original: 70 (7.0) -> novo: 10 (1.0)
    502: 10,   # Poção Laranja (Orange Potion) - original: 100 -> novo: 10
    503: 15,   # Poção Amarela (Yellow Potion) - original: 130 -> novo: 15
    504: 20,   # Poção Branca (White Potion) - original: 150 (15.0) -> novo: 20 (2.0)
    505: 20,   # Poção Azul (Blue Potion) - original: 150 (15.0) -> novo: 20 (2.0)
    601: 5,    # Asa de Mosca (Fly Wing) - original: 50 (5.0) -> novo: 5 (0.5)
    602: 5,    # Asa de Borboleta (Butterfly Wing) - original: 50 (5.0) -> novo: 5 (0.5)
    611: 0,    # Lupa (Magnifier) - original: 40 (4.0) -> novo: 0 (peso zero)
    969: 10,   # Ouro (Gold) - original: 200 (20.0) -> novo: 10 (1.0)
    603: 20,   # Caixa Velha Azul (Old Blue Box) - original: 200 -> novo: 20 (2.0)
    616: 10,   # Álbum Velho de Cartas (Old Card Album) - original: 50 -> novo: 10 (1.0)
}

def adjust_weights_in_db(path):
    if not os.path.isfile(path):
        return 0

    lines = []
    updated = 0

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if not line.strip() or line.strip().startswith("//"):
                lines.append(line)
                continue

            parts = line.split(",")
            if len(parts) >= 7:
                try:
                    item_id = int(parts[0].strip())
                    if item_id in LIGHT_WEIGHTS:
                        new_w = str(LIGHT_WEIGHTS[item_id])
                        if parts[6].strip() != new_w:
                            parts[6] = new_w
                            line = ",".join(parts)
                            updated += 1
                except ValueError:
                    pass

            lines.append(line)

    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    return updated

def main():
    env = load_env()
    root = env.get("RATHENA_ROOT", "data")

    paths = [
        os.path.join(root, "db/pre-re/item_db.txt"),
        os.path.join(root, "db/re/item_db.txt"),
    ]

    total_updated = 0
    for p in paths:
        count = adjust_weights_in_db(p)
        if count > 0:
            print(f"  [{os.path.basename(p)}] {count} itens tiveram pesos aliviados para o Aprendiz.")
            total_updated += count

    print(f"Ajuste de pesos concluído: consumíveis essenciais tornados ultraleves ({total_updated} modificações).")

if __name__ == "__main__":
    main()

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

# Pesos otimizados para roguelike (peso zero para itens iniciais do Aprendiz não pesarem nada)
LIGHT_WEIGHTS = {
    501: 0,    # Poção Vermelha (Red Potion) - peso ZERO
    502: 0,    # Poção Laranja (Orange Potion) - peso ZERO
    503: 0,    # Poção Amarela (Yellow Potion) - peso ZERO
    504: 0,    # Poção Branca (White Potion) - peso ZERO
    505: 0,    # Poção Azul (Blue Potion) - peso ZERO
    601: 0,    # Asa de Mosca (Fly Wing) - peso ZERO
    602: 0,    # Asa de Borboleta (Butterfly Wing) - peso ZERO
    611: 0,    # Lupa (Magnifier) - peso ZERO
    706: 0,    # Trevo de Quatro Folhas (Four Leaf Clover) - peso ZERO
    944: 0,    # Ferradura (Horseshoe) - peso ZERO
    969: 0,    # Ouro (Gold) - peso ZERO
    1202: 0,   # Faca [4] (Knife [4]) - peso ZERO
    1602: 0,   # Rod [4] (Vara [4]) - peso ZERO
    1702: 0,   # Bow [4] (Arco [4]) - peso ZERO
    2102: 0,   # Vembrassa [1] (Guard [1]) - peso ZERO
    2607: 0,   # Presilha [1] (Clip [1]) - peso ZERO
    2647: 0,   # Flor do Nilo [1] (Rosa do Nilo [1]) - peso ZERO
    4002: 0,   # Carta Fabre - peso ZERO
    4003: 0,   # Carta Pupa - peso ZERO
    4012: 0,   # Carta Ovo de Besouro-Ladrão - peso ZERO
    603: 0,    # Caixa Velha Azul (Old Blue Box) - peso ZERO
    616: 0,    # Álbum Velho de Cartas (Old Card Album) - peso ZERO
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

#!/usr/bin/env python3
"""
tools/generate_map_spawns.py

Gera a tabela e dataset determinístico `world_map_spawns`:
- Cidades: leva diretamente para o "meio da cidade" (coordenadas clássicas do @go / warper).
- Campos, calabouços e outros mapas: leva para perto de um portal de entrada oficial (landing coordinates).
Elimina teleportes randômicos incômodos no @warp quando o jogador não passa coordenadas (x=0, y=0).
"""

import os
import sys
import re
import subprocess
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 1. Cidades clássicas e seus centros ("meio da cidade")
TOWNS = {
    'prontera': (156, 191, 'Prontera Centro'),
    'morocc': (156, 93, 'Morroc Centro'),
    'geffen': (119, 59, 'Geffen Centro'),
    'payon': (162, 233, 'Payon Centro'),
    'alberta': (192, 147, 'Alberta Centro'),
    'izlude': (128, 114, 'Izlude Centro'),
    'aldebaran': (140, 131, 'Al De Baran Centro'),
    'lutie': (147, 134, 'Lutie Centro'),
    'xmas': (147, 134, 'Lutie Centro'),
    'comodo': (209, 143, 'Comodo Centro'),
    'yuno': (157, 51, 'Yuno Centro'),
    'amatsu': (198, 84, 'Amatsu Centro'),
    'gonryun': (160, 120, 'Gonryun Centro'),
    'umbala': (89, 157, 'Umbala Centro'),
    'niflheim': (21, 153, 'Niflheim Centro'),
    'louyang': (217, 100, 'Louyang Centro'),
    'jawaii': (249, 127, 'Jawaii Centro'),
    'ayothaya': (151, 117, 'Ayothaya Centro'),
    'einbroch': (64, 200, 'Einbroch Centro'),
    'lighthalzen': (158, 92, 'Lighthalzen Centro'),
    'einbech': (70, 95, 'Einbech Centro'),
    'hugel': (96, 145, 'Hugel Centro'),
    'rachel': (130, 110, 'Rachel Centro'),
    'veins': (216, 123, 'Veins Centro'),
    'moscovia': (223, 184, 'Moscovia Centro'),
    'mid_camp': (210, 288, 'Acampamento Centro'),
    'manuk': (282, 138, 'Manuk Centro'),
    'splendide': (201, 147, 'Splendide Centro'),
    'brasilis': (182, 239, 'Brasilis Centro'),
    'dicastes01': (198, 187, 'El Dicastes Centro'),
    'mora': (44, 151, 'Mora Centro'),
    'dewata': (200, 180, 'Dewata Centro'),
    'malangdo': (140, 114, 'Malangdo Centro'),
    'malaya': (242, 211, 'Porto Malaya Centro'),
    'eclage': (110, 39, 'Eclage Centro'),
    'lasagna': (193, 182, 'Lasagna Centro'),
}


def load_warp_landings_and_departures():
    scan_dirs = [
        os.path.join(ROOT, "data_base/npc/warps"),
        os.path.join(ROOT, "data_base/npc/pre-re/warps"),
        os.path.join(ROOT, "data/npc/warps"),
    ]

    landings = defaultdict(list)
    departures = defaultdict(list)

    for base in scan_dirs:
        if not os.path.isdir(base):
            continue
        for root, _, files in os.walk(base):
            for f in sorted(files):
                if not f.endswith(".txt"):
                    continue
                path = os.path.join(root, f)
                with open(path, "r", encoding="latin-1", errors="ignore") as infile:
                    for line in infile:
                        line = line.strip()
                        if not line or line.startswith("//"):
                            continue
                        parts = line.split("\t")
                        if len(parts) >= 4:
                            p1 = parts[0].split(",")
                            p4 = parts[3].split(",")
                            if len(p1) >= 3 and len(p4) >= 5:
                                from_map = p1[0].strip()
                                to_map = p4[2].strip()
                                try:
                                    fx, fy = int(p1[1]), int(p1[2])
                                    tx, ty = int(p4[3]), int(p4[4])
                                    landings[to_map].append((from_map, tx, ty))
                                    departures[from_map].append((to_map, fx, fy))
                                except ValueError:
                                    pass

    return landings, departures


def load_warper_coords():
    warper_txt = os.path.join(ROOT, "data_base/npc/custom/warper.txt")
    coords = {}
    if os.path.exists(warper_txt):
        with open(warper_txt, "r", encoding="latin-1", errors="ignore") as f:
            for line in f:
                m = re.search(r'Go\(\"([^\"]+)\",\s*(\d+),\s*(\d+)\)', line)
                if m:
                    coords[m.group(1)] = (int(m.group(2)), int(m.group(3)))
    return coords


def resolve_all_spawns():
    landings, departures = load_warp_landings_and_departures()
    warper_coords = load_warper_coords()

    all_maps = set(TOWNS.keys()) | set(landings.keys()) | set(departures.keys()) | set(warper_coords.keys())

    # Também incluir mapas do map_index se existirem
    map_index_file = os.path.join(ROOT, "data_base/db/map_index.txt")
    if os.path.isfile(map_index_file):
        with open(map_index_file, "r", encoding="latin-1", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("//"):
                    m_name = line.split()[0]
                    all_maps.add(m_name)

    spawns = {}

    for m in sorted(all_maps):
        # 1. Se for cidade: centro da cidade ("meio da cidade")
        if m in TOWNS:
            x, y, note = TOWNS[m]
            spawns[m] = (x, y, 'town', note)
            continue

        # 2. Se tiver landing vindo de portal:
        if m in landings:
            # Prioridade 1: landing vindo de uma cidade
            chosen = None
            for from_m, tx, ty in landings[m]:
                if from_m in TOWNS:
                    chosen = (tx, ty, 'portal', f'Portal de {from_m}')
                    break
            if not chosen:
                from_m, tx, ty = landings[m][0]
                chosen = (tx, ty, 'portal', f'Portal de {from_m}')
            spawns[m] = chosen
            continue

        # 3. Coordenada do warper oficial
        if m in warper_coords:
            wx, wy = warper_coords[m]
            spawns[m] = (wx, wy, 'portal', 'Coordenada Warper')
            continue

        # 4. Se tiver saída de portal neste mapa:
        if m in departures:
            to_m, fx, fy = departures[m][0]
            # Deslocamento leve para célula segura adjacente ao portal
            spawns[m] = (fx, fy, 'portal', f'Portal para {to_m}')
            continue

    return spawns


def generate_sql():
    spawns = resolve_all_spawns()

    data_dir = os.path.join(ROOT, "data")
    os.makedirs(data_dir, exist_ok=True)
    sql_path = os.path.join(data_dir, "world_map_spawns.sql")

    print(f"=== Gerador de Pontos de Spawn de Mapas (v3 Roguelike) ===")
    print(f"Total de mapas com coordenadas determinísticas: {len(spawns)}")

    town_count = sum(1 for _, _, t, _ in spawns.values() if t == 'town')
    portal_count = len(spawns) - town_count
    print(f"  - Cidades (meio da cidade): {town_count}")
    print(f"  - Mapas com portal:        {portal_count}")

    with open(sql_path, "w", encoding="utf-8") as f:
        f.write("-- Tabela de coordenadas determinísticas para @warp (meio da cidade ou perto de um portal)\n")
        f.write("CREATE TABLE IF NOT EXISTS `world_map_spawns` (\n")
        f.write("    `map_name` VARCHAR(32) PRIMARY KEY,\n")
        f.write("    `x` SMALLINT NOT NULL,\n")
        f.write("    `y` SMALLINT NOT NULL,\n")
        f.write("    `type` VARCHAR(16) NOT NULL DEFAULT 'portal',\n")
        f.write("    `note` VARCHAR(64) NULL\n")
        f.write(") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;\n\n")
        f.write("TRUNCATE TABLE `world_map_spawns`;\n\n")

        rows = []
        for m, (x, y, stype, note) in sorted(spawns.items()):
            safe_note = note.replace("'", "''")
            rows.append(f"('{m}', {x}, {y}, '{stype}', '{safe_note}')")

        for i in range(0, len(rows), 100):
            batch = rows[i:i + 100]
            f.write("INSERT INTO `world_map_spawns` (`map_name`, `x`, `y`, `type`, `note`) VALUES\n" + ",\n".join(batch) + ";\n")

    print(f"  ✓ SQL salvo em: {sql_path}")

    # Aplicar no container ragnarok-db se estiver em execução
    try:
        proc = subprocess.run(
            ["docker", "exec", "-i", "ragnarok-db", "mysql", "-u", "ragnarok", "-pragnarok", "ragnarok"],
            input=open(sql_path, "rb").read(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        print("  ✓ Tabela world_map_spawns aplicada no MariaDB com sucesso!")
    except Exception as e:
        print(f"  [INFO] Importação direta no MariaDB pulada ({e}). start.sh aplicará no boot.")


if __name__ == "__main__":
    generate_sql()

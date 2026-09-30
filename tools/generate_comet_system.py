#!/usr/bin/env python3
"""
tools/generate_comet_system.py

Gera o sistema dos 7 Fragmentos do Cometa Negro e a matriz de Taxi Distance no Grafo de Mapas:
1. Sorteia 7 estrelas clássicas da lista das 100 estrelas mais famosas (Sirius, Aldebaran, Deneb, etc.).
2. Nomeia cada MVP no formato: "<Nome da Estrela>, <Nome do MVP> <Adjetivo de Efeito>".
3. Aloca cada chefe em um mapa hostil distinto e calcula as distâncias no grafo (BFS).
4. Sincroniza as tabelas `world_comet_fragments` e `world_fragment_distances` no MariaDB.
"""

import os
import sys
import re
import json
import random
import subprocess
from collections import defaultdict, deque

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# As 100 estrelas clássicas mais conhecidas da astronomia
FAMOUS_STARS = [
    "Sirius", "Canopus", "Rigel", "Arcturus", "Vega", "Capella", "Aldebaran", "Betelgeuse",
    "Spica", "Antares", "Pollux", "Deneb", "Regulus", "Castor", "Bellatrix", "Alnilam",
    "Alnitak", "Saiph", "Polaris", "Algol", "Mira", "Mizar", "Alcor", "Achernar",
    "Hadar", "Acrux", "Mimosa", "Alioth", "Dubhe", "Merak", "Phecda", "Megrez",
    "Alkaid", "Shaula", "Sargas", "Peacock", "Alpheratz", "Mirfak", "Enif", "Scheat",
    "Markab", "Menkar", "Rasalhague", "Rastaban", "Eltanin", "Kochab", "Thuban", "Hamal",
    "Diphda", "Menkent", "Alphard", "Suhail", "Wezen", "Adhara", "Avior", "Miaplacidus",
    "Naos", "Atria", "Gacrux", "Nunki", "Sabik", "Alphecca", "Alsephina", "Aspidiske",
    "Muhlifain", "Alnair", "Fomalhaut", "Procyon", "Achird", "Caph", "Schedar", "Ruchbah",
    "Navi", "Sadr", "Gienah", "Albireo", "Mirach", "Almach", "Algedi", "Dabih",
    "Nashira", "Sadalsuud", "Sadalmelik", "Skat", "Albali", "Ankaa", "Kornephoros", "Sarir",
    "Zubenelgenubi", "Zubeneschamali", "Brachium", "Izar", "Muphrid", "Seginus", "Alchiba", "Cor Caroli",
    "Chara", "Botein", "Zaurak", "Electra"
]

EFFECT_ADJECTIVES = [
    "do Vazio", "Abissal", "Flamejante", "Glacial", "da Nebulosa",
    "Devorador", "Astral", "Sombrio", "Estelar", "do Eclipse",
    "Tempestuoso", "Radioativo", "Ancestral", "Corrompido", "Espectral",
    "Incandescente", "Fulminante", "do Crepúsculo", "Titânico", "do Meteoro"
]

BASE_BOSSES = [
    {"mob_id": 1039, "base_name": "Baphomet"},
    {"mob_id": 1159, "base_name": "Phreeoni"},
    {"mob_id": 1115, "base_name": "Eddga"},
    {"mob_id": 1150, "base_name": "Moonlight"},
    {"mob_id": 1252, "base_name": "Garm"},
    {"mob_id": 1272, "base_name": "Dark Lord"},
    {"mob_id": 1373, "base_name": "Lord of Death"},
]

STARTING_CITIES = {
    "prontera", "morocc", "geffen", "payon", "alberta", "izlude",
    "aldebaran", "lutie", "comodo", "yuno", "amatsu", "gonryun",
    "umbala", "lighthalzen", "louyang", "ayothaya", "einbroch",
    "einbech", "hugel", "rachel", "veins", "xmas", "jawaii", "niflheim"
}

PROTECTED_PATTERNS = (
    "sec_in", "prt_in", "morocc_in", "geffen_in", "payon_in", "alberta_in",
    "izlude_in", "aldeba_in", "xmas_in", "comodo_in", "yuno_in", "amatsu_in",
    "gon_in", "um_in", "lhz_in", "lou_in", "ayothaya_in", "ein_in", "hugel_in",
    "rachel_in", "veins_in", "mid_campin", "man_in", "spl_in", "job_", "prt_cas",
    "prt_church", "prt_castle", "gld_", "aldeg_cas", "gefg_cas", "payg_cas",
    "prtg_cas", "pvp_", "guildcastles", "arena", "sign",
    "new_", "que_", "airport", "lhz_airport", "y_airport", "_gld", "cas",
    "in_", "monk_in", "nif_in", "ra_in", "ve_in", "hu_in", "cmd_in", "ayo_in", "ama_in",
    "nameless_i", "jupe_gate", "jupe_area", "thana_step", "monk_test", "alb2trea", "alb_ship",
    "izlu2dun", "gef_tower", "alde_alche", "pay_arche", "lhz_cube", "kh_mansion",
    "ra_temple", "moc_ruins", "mosk_in", "yuno_pre", "jupe_cave"
)


def get_active_seed():
    if len(sys.argv) > 1 and sys.argv[1].strip():
        return sys.argv[1].strip()
    
    env_file = os.path.join(ROOT_DIR, ".env.rando")
    if os.path.isfile(env_file):
        with open(env_file, "r") as f:
            for line in f:
                if line.startswith("WORLD_SEED="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    
    # Fallback via MariaDB
    try:
        out = subprocess.check_output([
            "docker", "exec", "-i", "ragnarok-db", "mysql", "-u", "ragnarok", "-pragnarok", "ragnarok",
            "-e", "SELECT value FROM world_metadata WHERE `key` = 'active_seed' LIMIT 1;"
        ], stderr=subprocess.DEVNULL)
        lines = out.decode("utf-8").strip().split("\n")
        if len(lines) > 1 and lines[1].strip():
            return lines[1].strip()
    except Exception:
        pass

    return "v3-world"


def get_numeric_seed(seed_str):
    try:
        out = subprocess.check_output([
            "python3", os.path.join(ROOT_DIR, "tools/world_seed.py"), seed_str
        ])
        return int(out.decode("utf-8").strip())
    except Exception:
        import hashlib
        return int(hashlib.sha256(seed_str.encode("utf-8")).hexdigest()[:8], 16)


def load_connections(seed_str):
    adj = defaultdict(set)
    try:
        out = subprocess.check_output([
            "docker", "exec", "-i", "ragnarok-db", "mysql", "-u", "ragnarok", "-pragnarok", "ragnarok",
            "-e", f"SELECT from_map, to_map FROM world_map_connections WHERE seed = '{seed_str}';"
        ], stderr=subprocess.DEVNULL)
        lines = out.decode("utf-8").strip().split("\n")[1:]
        for line in lines:
            parts = line.split()
            if len(parts) >= 2:
                u, v = parts[0], parts[1]
                adj[u].add(v)
                adj[v].add(u)
    except Exception:
        sql_file = os.path.join(ROOT_DIR, "data/world_map_connections.sql")
        if os.path.isfile(sql_file):
            with open(sql_file, "r") as f:
                for line in f:
                    if f"'{seed_str}'" in line:
                        m = re.findall(r"\('([a-zA-Z0-9_]+)',\s*'([a-zA-Z0-9_]+)',", line)
                        for u, v in m:
                            adj[u].add(v)
                            adj[v].add(u)
    return adj


def load_candidate_maps(adj):
    candidate_maps = set()
    try:
        out = subprocess.check_output([
            "docker", "exec", "-i", "ragnarok-db", "mysql", "-u", "ragnarok", "-pragnarok", "ragnarok",
            "-e", "SELECT map_name FROM world_map_has_mobs WHERE total_spawns > 0;"
        ], stderr=subprocess.DEVNULL)
        lines = out.decode("utf-8").strip().split("\n")[1:]
        for line in lines:
            m = line.strip()
            if m:
                candidate_maps.add(m)
    except Exception:
        candidate_maps = set(adj.keys())

    gat_cache_file = os.path.join(ROOT_DIR, "tools/map_randomizer/gat_cache.json")
    gat_dims = {}
    if os.path.isfile(gat_cache_file):
        try:
            with open(gat_cache_file, "r") as gf:
                gat_dims = json.load(gf)
        except Exception:
            pass

    # Filtrar mapas proibidos e priorizar mapas compactos (<= 300x300, 30s-180s de travessia)
    valid_maps = []
    compact_maps = []
    for m in sorted(candidate_maps):
        if m in STARTING_CITIES:
            continue
        if any(pat in m for pat in PROTECTED_PATTERNS):
            continue
        if m not in adj:
            continue
        valid_maps.append(m)
        dim = gat_dims.get(m, {})
        # Mapas pequenos/médios de masmorras ou campos compactos (<= 300 de largura e altura)
        if dim.get("x", 400) <= 300 and dim.get("y", 400) <= 300:
            compact_maps.append(m)

    return compact_maps if len(compact_maps) >= 7 else valid_maps


def compute_bfs_distances(start_map, adj):
    distances = {start_map: 0}
    q = deque([start_map])
    while q:
        curr = q.popleft()
        curr_dist = distances[curr]
        for neighbor in adj[curr]:
            if neighbor not in distances:
                distances[neighbor] = curr_dist + 1
                q.append(neighbor)
    return distances


def main():
    seed_str = get_active_seed()
    num_seed = get_numeric_seed(seed_str)
    print(f"=== Gerando Sistema dos 7 Fragmentos do Cometa (Seed: {seed_str}) ===")

    rng = random.Random(num_seed + 7777)

    adj = load_connections(seed_str)
    print(f"  ✓ Grafo de mapas carregado: {len(adj)} mapas conectados.")

    valid_maps = load_candidate_maps(adj)
    print(f"  ✓ Mapas válidos para fragmentos: {len(valid_maps)} mapas.")

    if len(valid_maps) < 7:
        print("[ERRO] Mapas insuficientes para 7 fragmentos!")
        sys.exit(1)

    # 1. Escolher 7 estrelas famosas distintas deterministicamente
    shuffled_stars = list(FAMOUS_STARS)
    rng.shuffle(shuffled_stars)
    selected_stars = shuffled_stars[:7]

    # 2. Escolher 7 adjetivos de efeito distintos
    shuffled_adjectives = list(EFFECT_ADJECTIVES)
    rng.shuffle(shuffled_adjectives)
    selected_adjectives = shuffled_adjectives[:7]

    # 3. Escolher 7 mapas distintos e espalhados
    rng.shuffle(valid_maps)
    selected_maps = valid_maps[:7]

    fragments_data = []
    for i, boss in enumerate(BASE_BOSSES):
        frag_id = i + 1
        star = selected_stars[i]
        adj_effect = selected_adjectives[i]
        
        # Formato requisitado: "<nome da estrela>, <nome do mvp> + <adjetivo de efeito>"
        mob_full_name = f"{star}, {boss['base_name']} {adj_effect}"
        frag_title = f"Fragmento {star}"
        chosen_map = selected_maps[i]

        fragments_data.append({
            "id": frag_id,
            "seed": seed_str,
            "star_name": star,
            "map_name": chosen_map,
            "mob_id": boss["mob_id"],
            "mob_name": mob_full_name,
            "title": frag_title
        })
        print(f"  🌟 Fragmento #{frag_id} [{frag_title}]: '{mob_full_name}' alocado em '{chosen_map}'")

    # 4. Calcular Taxi Distance para cada fragmento
    all_distances = []  # (seed, from_map, fragment_id, distance_hops)
    for frag in fragments_data:
        frag_id = frag["id"]
        start_map = frag["map_name"]
        bfs_dists = compute_bfs_distances(start_map, adj)
        for map_name, hops in bfs_dists.items():
            all_distances.append((seed_str, map_name, frag_id, hops))

    print(f"  ✓ Taxi Distance computada para {len(all_distances)} pares (mapa, fragmento).")

    # 5. Gerar script SQL
    sql_path = os.path.join(ROOT_DIR, "data/world_comet_system.sql")
    os.makedirs(os.path.dirname(sql_path), exist_ok=True)
    with open(sql_path, "w", encoding="utf-8") as f:
        f.write("-- Sistema dos 7 Fragmentos do Cometa Negro & Radar de Grafo\n")
        f.write("""
CREATE TABLE IF NOT EXISTS `world_comet_fragments` (
    `id` TINYINT NOT NULL,
    `seed` VARCHAR(64) NOT NULL,
    `star_name` VARCHAR(40) NOT NULL,
    `map_name` VARCHAR(32) NOT NULL,
    `mob_id` INT NOT NULL,
    `mob_name` VARCHAR(80) NOT NULL,
    `title` VARCHAR(60) NOT NULL,
    `defeated` TINYINT(1) NOT NULL DEFAULT 0,
    `defeated_by` VARCHAR(30) NULL,
    `defeated_at` DATETIME NULL,
    PRIMARY KEY (`id`, `seed`),
    INDEX `idx_seed_def` (`seed`, `defeated`),
    INDEX `idx_map_seed` (`map_name`, `seed`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `world_fragment_distances` (
    `seed` VARCHAR(64) NOT NULL,
    `from_map` VARCHAR(32) NOT NULL,
    `fragment_id` TINYINT NOT NULL,
    `distance_hops` SMALLINT NOT NULL,
    PRIMARY KEY (`seed`, `from_map`, `fragment_id`),
    INDEX `idx_seed_map` (`seed`, `from_map`),
    INDEX `idx_seed_frag` (`seed`, `fragment_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
""")
        f.write(f"DELETE FROM `world_comet_fragments` WHERE `seed` = '{seed_str}';\n")
        f.write(f"DELETE FROM `world_fragment_distances` WHERE `seed` = '{seed_str}';\n\n")

        # Inserir os 7 fragmentos
        f.write("INSERT INTO `world_comet_fragments` (`id`, `seed`, `star_name`, `map_name`, `mob_id`, `mob_name`, `title`, `defeated`) VALUES\n")
        frag_rows = []
        for frag in fragments_data:
            frag_rows.append(f"({frag['id']}, '{frag['seed']}', '{frag['star_name']}', '{frag['map_name']}', {frag['mob_id']}, '{frag['mob_name']}', '{frag['title']}', 0)")
        f.write(",\n".join(frag_rows) + ";\n\n")

        # Inserir distâncias em lotes de 200
        batch_size = 200
        for i in range(0, len(all_distances), batch_size):
            batch = all_distances[i:i + batch_size]
            rows = [f"('{s}', '{m}', {fid}, {d})" for s, m, fid, d in batch]
            f.write("INSERT INTO `world_fragment_distances` (`seed`, `from_map`, `fragment_id`, `distance_hops`) VALUES\n")
            f.write(",\n".join(rows) + ";\n")

    print(f"  ✓ Script SQL exportado em: {sql_path}")

    # Aplicar no MariaDB se o container estiver ativo
    try:
        subprocess.run(
            ["docker", "exec", "-i", "ragnarok-db", "mysql", "-u", "ragnarok", "-pragnarok", "ragnarok"],
            input=open(sql_path, "rb").read(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        print("  ✓ Tabelas world_comet_fragments e world_fragment_distances sincronizadas no MariaDB com sucesso!")
    except Exception as e:
        print(f"  [INFO] Importação direta no MariaDB ignorada ({e}), o boot aplicará o arquivo.")

    print(f"=== Sistema dos Fragmentos do Cometa Gerado com Sucesso! ===\n")


if __name__ == "__main__":
    main()

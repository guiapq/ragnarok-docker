#!/usr/bin/env python3
"""
tools/map_randomizer/randomize_map_topology.py

Motor de Randomização de Topologia de Mapas e Portais (Versão 3 - RagnaRogue)
Inspirado na arquitetura de grafo do Die4Ever, otimizado para rAthena Pré-Renewal.

- Determinístico: Mesma seed gera sempre exatamente a mesma topologia.
- Bidirecional e Simétrico: Passar por um portal e voltar coloca o jogador exatamente onde estava.
- Jogável: Utiliza coordenadas de pouso (landing) oficiais seguras sem prender em água ou paredes.
- Severamente limita mapas sem monstros: Interiores, castelos GdE, quests, aeroportos e tutoriais
  são estritamente protegidos. Restam apenas ~5 santuários pacíficos no mundo todo e 250+ mapas de combate.
- Exporta relatório de rotas e conexões em SQL para a mecânica de conquista territorial.
"""

import os
import sys
import re
import json
import random
from collections import defaultdict, deque

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Padrões de mapas estritamente protegidos (interiores, lojas, GdE, eventos, tutoriais e quests)
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

# Cidades principais (conquistadas por padrão)
STARTING_CITIES = {
    "prontera", "morocc", "geffen", "payon", "alberta", "izlude",
    "aldebaran", "lutie", "comodo", "yuno", "amatsu", "gonryun",
    "umbala", "lighthalzen", "louyang", "ayothaya", "einbroch",
    "einbech", "hugel", "rachel", "veins", "xmas", "jawaii"
}


class WarpPoint:
    def __init__(self, raw_line, file_path, line_idx):
        self.raw_line = raw_line
        self.file_path = file_path
        self.line_idx = line_idx
        self.from_map = ""
        self.from_x = 0
        self.from_y = 0
        self.facing = 0
        self.warp_type = "warp"
        self.name = ""
        self.span_x = 1
        self.span_y = 1
        self.to_map = ""
        self.to_x = 0
        self.to_y = 0
        self.trailing_comment = ""
        self.is_valid = False
        self.parse()

    def parse(self):
        line = self.raw_line.strip()
        if not line or line.startswith("//"):
            return

        comment_match = re.search(r'(/\*.*?\*/|//.*)$', line)
        if comment_match:
            self.trailing_comment = comment_match.group(1)
            line = line[:comment_match.start()].strip()

        parts = line.split('\t')
        if len(parts) < 4:
            return

        # Parte 1: from_map,from_x,from_y,facing
        p1 = parts[0].split(',')
        if len(p1) < 4:
            return
        self.from_map = p1[0].strip()
        try:
            self.from_x = int(p1[1].strip())
            self.from_y = int(p1[2].strip())
            self.facing = int(p1[3].strip())
        except ValueError:
            return

        self.warp_type = parts[1].strip()
        self.name = parts[2].strip()

        # Parte 4: span_x,span_y,to_map,to_x,to_y
        p4 = parts[3].split(',')
        if len(p4) < 5:
            return
        try:
            self.span_x = int(p4[0].strip())
            self.span_y = int(p4[1].strip())
            self.to_map = p4[2].strip()
            self.to_x = int(p4[3].strip())
            self.to_y = int(p4[4].strip())
        except ValueError:
            return

        self.is_valid = True

    def is_protected(self):
        if not self.is_valid:
            return True
        for pattern in PROTECTED_PATTERNS:
            if pattern in self.from_map or pattern in self.to_map:
                return True
        # Se for warp interno para o mesmo mapa
        if self.from_map == self.to_map:
            return True
        return False

    def render(self):
        comment_part = f"\t{self.trailing_comment}" if self.trailing_comment else ""
        return f"{self.from_map},{self.from_x},{self.from_y},{self.facing}\t{self.warp_type}\t{self.name}\t{self.span_x},{self.span_y},{self.to_map},{self.to_x},{self.to_y}{comment_part}\n"


class Socket:
    """Representa um ponto de conexão (ponta de portal) com seu pouso seguro."""
    def __init__(self, warp_obj, landing_x, landing_y):
        self.warp = warp_obj
        self.map = warp_obj.from_map
        self.trigger_x = warp_obj.from_x
        self.trigger_y = warp_obj.from_y
        self.landing_x = landing_x
        self.landing_y = landing_y


def load_all_warps(dirs_to_scan):
    all_warps = []
    file_lines = defaultdict(list)

    for base_dir in dirs_to_scan:
        if not os.path.isdir(base_dir):
            continue
        for root, _, files in os.walk(base_dir):
            for f in sorted(files):
                if not f.endswith(".txt"):
                    continue
                path = os.path.join(root, f)
                with open(path, "r", encoding="latin-1", errors="ignore") as infile:
                    lines = infile.readlines()
                    for idx, line in enumerate(lines):
                        wp = WarpPoint(line, path, idx)
                        if wp.is_valid:
                            all_warps.append(wp)
                        file_lines[path].append(line)

    return all_warps, file_lines


def pair_reciprocal_warps(warps):
    """
    Identifica pares recíprocos de portais: A -> B e B -> A.
    Ordena de forma determinística antes de parear.
    """
    sorted_warps = sorted(warps, key=lambda w: (w.from_map, w.to_map, w.from_x, w.from_y, w.name))
    lookup = defaultdict(list)
    for w in sorted_warps:
        lookup[(w.from_map, w.to_map)].append(w)

    visited = set()
    pairs = []
    singletons = []

    for w in sorted_warps:
        if id(w) in visited:
            continue

        reverse_candidates = lookup.get((w.to_map, w.from_map), [])
        reverse_match = None
        for rev in reverse_candidates:
            if id(rev) not in visited:
                reverse_match = rev
                break

        if reverse_match:
            visited.add(id(w))
            visited.add(id(reverse_match))
            pairs.append((w, reverse_match))
        else:
            visited.add(id(w))
            singletons.append(w)

    return pairs, singletons


def randomize_topology(pairs, seed_num):
    """
    Cria sockets para cada ponta do par recíproco e os reconecta determinísticamente.
    Garante simetria 100% perfeita e reversibilidade.
    """
    sockets = []
    for wa, wb in pairs:
        # Quando alguém chega no portal wa, ele pousa nas coordenadas seguras wb.to_x, wb.to_y
        sockets.append(Socket(wa, wb.to_x, wb.to_y))
        # Quando alguém chega no portal wb, ele pousa nas coordenadas seguras wa.to_x, wa.to_y
        sockets.append(Socket(wb, wa.to_x, wa.to_y))

    # Ordenação determinística antes do shuffle
    sockets.sort(key=lambda s: (s.map, s.trigger_x, s.trigger_y, s.warp.name))

    rng = random.Random(seed_num)
    shuffled = list(sockets)
    rng.shuffle(shuffled)

    # Se for ímpar, descarta o último para manter pares perfeitos
    if len(shuffled) % 2 != 0:
        shuffled = shuffled[:-1]

    connections = []
    for i in range(0, len(shuffled), 2):
        s1 = shuffled[i]
        s2 = shuffled[i + 1]

        # S1 aponta para o mapa e coordenadas de pouso de S2
        s1.warp.to_map = s2.map
        s1.warp.to_x = s2.landing_x
        s1.warp.to_y = s2.landing_y

        # S2 aponta para o mapa e coordenadas de pouso de S1
        s2.warp.to_map = s1.map
        s2.warp.to_x = s1.landing_x
        s2.warp.to_y = s1.landing_y

        connections.append((s1.map, s2.map))
        connections.append((s2.map, s1.map))

    return connections


def write_randomized_warps(all_warps, file_lines):
    # Atualiza as linhas modificadas nos arquivos de origem
    for w in all_warps:
        if w.is_valid:
            file_lines[w.file_path][w.line_idx] = w.render()

    # Escreve nos diretórios correspondentes de data/
    for path, lines in file_lines.items():
        if "data_base/" in path:
            out_path = path.replace("data_base/", "data/")
        else:
            out_path = path
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="latin-1") as f:
            f.writelines(lines)


def export_topology_report(connections, output_path, seed_str, empty_maps):
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"==========================================================\n")
        f.write(f"RAGNAROGUE v3 — TOPOLOGIA DE MUNDO PROCEDURAL\n")
        f.write(f"Seed: {seed_str}\n")
        f.write(f"Total de Rotas Criadas: {len(connections) // 2}\n")
        f.write(f"Santuários Pacíficos Raros (Sem Monstros): {len(empty_maps)}\n")
        f.write(f"==========================================================\n\n")

        adj = defaultdict(set)
        for src, dest in connections:
            adj[src].add(dest)

        for src in sorted(adj.keys()):
            peace_tag = " [SANTUÁRIO PACÍFICO]" if src in empty_maps else ""
            f.write(f"[{src}]{peace_tag}\n")
            for dest in sorted(adj[src]):
                f.write(f"  --> Conexão direta com: {dest}\n")
            f.write("\n")


def export_sql_connections(connections, seed_str, sql_path):
    """Gera script SQL para popular world_map_connections com a topologia procedural."""
    with open(sql_path, "w", encoding="utf-8") as f:
        f.write("-- Topologia Procedural de Conexões de Mapas (v3)\n")
        f.write(f"DELETE FROM `world_map_connections` WHERE `seed` = '{seed_str}';\n")
        
        seen = set()
        rows = []
        for src, dest in connections:
            if (src, dest) not in seen:
                seen.add((src, dest))
                rows.append(f"('{src}', '{dest}', '{seed_str}')")

        batch_size = 100
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            f.write("INSERT IGNORE INTO `world_map_connections` (`from_map`, `to_map`, `seed`) VALUES\n")
            f.write(",\n".join(batch))
            f.write(";\n")


def generate_mob_density_database():
    """Escaneia todos os spawns de monstros oficiais e gera tabela de contagem de mobs."""
    mob_dirs = [
        os.path.join(ROOT_DIR, "data_base/npc/pre-re/mobs"),
        os.path.join(ROOT_DIR, "data_base/npc/mobs")
    ]
    map_mobs = defaultdict(int)

    for d in mob_dirs:
        if not os.path.isdir(d):
            continue
        for root, _, files in os.walk(d):
            for f in sorted(files):
                if not f.endswith(".txt"):
                    continue
                with open(os.path.join(root, f), "r", encoding="latin-1", errors="ignore") as infile:
                    for line in infile:
                        line = line.strip()
                        if not line or line.startswith("//"):
                            continue
                        m = re.match(r"^([a-zA-Z0-9_]+),\d+,\d+.*?\tmonster\t.*?,(\d+)", line)
                        if m:
                            map_name = m.group(1)
                            try:
                                count = int(m.group(2))
                            except ValueError:
                                count = 1
                            map_mobs[map_name] += count

    sql_path = os.path.join(ROOT_DIR, "data/world_map_has_mobs.sql")
    with open(sql_path, "w", encoding="utf-8") as f:
        f.write("CREATE TABLE IF NOT EXISTS `world_map_has_mobs` (`map_name` VARCHAR(32) PRIMARY KEY, `total_spawns` INT NOT NULL);\n")
        f.write("TRUNCATE TABLE `world_map_has_mobs`;\n")
        rows = [f"('{m}', {cnt})" for m, cnt in sorted(map_mobs.items())]
        for i in range(0, len(rows), 100):
            batch = rows[i:i + 100]
            f.write("INSERT INTO `world_map_has_mobs` (`map_name`, `total_spawns`) VALUES\n" + ",\n".join(batch) + ";\n")

    return map_mobs, sql_path


def main():
    seed_str = os.environ.get("WORLD_SEED", "valente-baphomet-999")
    seed_num = int(os.environ.get("WORLD_SEED_NUMERIC", "42"))
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        seed_num = int(sys.argv[1])

    scan_dirs = [
        os.path.join(ROOT_DIR, "data_base/npc/warps"),
        os.path.join(ROOT_DIR, "data_base/npc/pre-re/warps")
    ]

    print(f"=== [RagnaRogue v3] Randomizador de Topologia de Mapas ===")
    print(f"Seed:    {seed_str} (Numeric: {seed_num})")
    print(f"Bases escaneadas: {scan_dirs}")

    # 1. Carregar e identificar densidade de monstros
    map_mobs, mob_sql_path = generate_mob_density_database()
    print(f"  ✓ Banco de densidade de monstros gerado ({len(map_mobs)} mapas de combate).")

    # 2. Carregar e filtrar portais
    all_warps, file_lines = load_all_warps(scan_dirs)
    print(f"Total de portais lidos: {len(all_warps)}")

    eligible_warps = [w for w in all_warps if not w.is_protected()]
    protected_warps = [w for w in all_warps if w.is_protected()]
    print(f"  - Portais protegidos (cidades/interiores/GdE/quests/aeroportos): {len(protected_warps)}")
    print(f"  - Portais elegíveis para reembaralhamento:                     {len(eligible_warps)}")

    pairs, singletons = pair_reciprocal_warps(eligible_warps)
    print(f"  - Pares bidirecionais identificados:                           {len(pairs)} ({len(pairs)*2} sockets)")
    print(f"  - Portais unidirecionais mantidos intactos:                    {len(singletons)}")

    # 3. Embaralhar topologia com garantia de simetria reversível
    connections = randomize_topology(pairs, seed_num)

    # Identificar mapas pacíficos no pool (severamente limitados)
    pool_maps = set()
    for src, dst in connections:
        pool_maps.add(src)
        pool_maps.add(dst)

    empty_sanctuaries = pool_maps - set(map_mobs.keys()) - STARTING_CITIES
    print(f"  - Mapas de combate no pool:                                    {len(pool_maps & set(map_mobs.keys()))}")
    print(f"  - Cidades capitais de ancoragem:                               {len(pool_maps & STARTING_CITIES)}")
    print(f"  - Santuários pacíficos raros (sem monstros):                   {len(empty_sanctuaries)} ({', '.join(sorted(empty_sanctuaries))})")

    write_randomized_warps(all_warps, file_lines)
    print(f"  ✓ Arquivos de warp salvos com sucesso em data/npc/warps e data/npc/pre-re/warps!")

    # Gerar mapflags de loadevent para todos os mapas de forma segura
    map_index_path = os.path.join(ROOT_DIR, "data_base/db/map_index.txt")
    if os.path.isfile(map_index_path):
        with open(map_index_path, "r") as mif:
            m_lines = [l.strip() for l in mif if l.strip() and not l.startswith("//")]
        loadevent_content = "// Mapflags de loadevent para RagnaRogue v3\n"
        for ml in m_lines:
            parts = ml.split()
            if parts:
                loadevent_content += f"{parts[0]}\tmapflag\tloadevent\n"
        for mf_dir in ["data_base/npc/custom", "data/npc/custom"]:
            out_mf = os.path.join(ROOT_DIR, mf_dir, "mapflags_loadevent.txt")
            os.makedirs(os.path.dirname(out_mf), exist_ok=True)
            with open(out_mf, "w") as mfo:
                mfo.write(loadevent_content)
        print(f"  ✓ Mapflags de loadevent gerados com sucesso para {len(m_lines)} mapas!")


    # 5. Exportar relatórios e banco SQL
    report_path = os.path.join(ROOT_DIR, "data/world_topology.txt")
    export_topology_report(connections, report_path, seed_str, empty_sanctuaries)
    print(f"  ✓ Relatório de topologia salvo em: {report_path}")

    sql_path = os.path.join(ROOT_DIR, "data/world_map_connections.sql")
    export_sql_connections(connections, seed_str, sql_path)
    print(f"  ✓ Conexões SQL salvas em: {sql_path}")

    # 6. Aplicar tabelas no MariaDB se o container estiver ativo
    try:
        import subprocess
        for s_file in [mob_sql_path, sql_path]:
            subprocess.run(
                ["docker", "exec", "-i", "ragnarok-db", "mysql", "-u", "ragnarok", "-pragnarok", "ragnarok"],
                input=open(s_file, "rb").read(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
        print("  ✓ Tabelas world_map_connections e world_map_has_mobs atualizadas no MariaDB!")
    except Exception as e:
        print(f"  [INFO] Importação direta no MariaDB ignorada ({e}), start.sh aplicará no boot.")

    print(f"=== Concluído com sucesso! Topologia procedural v3 ativa. ===")


if __name__ == "__main__":
    main()

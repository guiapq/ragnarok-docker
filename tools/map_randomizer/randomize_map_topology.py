#!/usr/bin/env python3
"""
tools/map_randomizer/randomize_map_topology.py

Motor de Randomização de Topologia de Mapas e Portais (Versão 4 - RagnaRogue Pacing & Hall da Fama)
- Campanha de 4 Cidades com Dificuldade Progressiva (Até Ep 11.3 Nameless Island):
    Tier 1 (Inicial Compacta/Remota): Alberta, Lutie (xmas), Gonryun, Ayothaya, Comodo, Amatsu.
    Tier 2 (Intermediária Compacta): Izlude, Payon, Einbech. (Cidades gigantes/labirínticas banidas).
    Tier 3 (Fronteira Rápida): Hugel, Veins, Umbala.
    Tier 4 (Capital / Clímax Final): Prontera, Lighthalzen ou Rachel.
- Rotas Canônicas de Profundidade 4 fixa da Cidade até a Câmara do Boss:
    Passo 1 (Verde): Lv 1-20
    Passo 2 (Azul): Lv 21-45
    Passo 3 (Vermelho): Lv 46-75
    Passo 4 (Amarelo): Lv 76-99+ (Covil do Chefe / MVP)
- Progressão de Chefes e Trancas Condicionais:
    Ato 1 (Cidade 1): 1 Boss aberto -> derrotá-lo libera 2 Bosses -> derrotar os 3 libera Cidade 2.
    Ato 2 (Cidade 2): 3 caminhos já abertos -> derrotar os 3 libera Cidade 3.
    Ato 3 (Cidade 3): 2 caminhos de Boss abertos -> derrotar os 2 libera a Capital (Cidade 4).
    Ato 4 (Capital): Clímax Supremo (Monastério de Nameless / Biolabs 3 / Glast Heim).
- Portais Coloridos & Avisos de Rumo:
    Efeitos visuais coloridos contínuos emitidos nos portais (Verde, Azul, Vermelho, Amarelo).
    Caminhos fora da rota ("Off-path / Vazamentos") alertam: "está no rumo errado e poderá se perder profundamente!".
"""

import os
import sys
import re
import json
import math
import random
import subprocess
from collections import defaultdict

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 1. Classificação das Cidades em 4 Tiers de Dificuldade
TIER1_CITIES = ["alberta", "xmas", "gonryun", "ayothaya", "comodo", "amatsu"]
TIER2_CITIES = ["izlude", "payon", "einbech"]
TIER3_CITIES = ["hugel", "veins", "umbala"]
TIER4_CAPITALS = ["prontera", "lighthalzen", "rachel"]
OTHER_CITIES = ["geffen", "morocc", "aldebaran", "yuno", "louyang", "einbroch", "jawaii"]

ALL_CAMPAIGN_CITIES = set(TIER1_CITIES + TIER2_CITIES + TIER3_CITIES + TIER4_CAPITALS)
ALL_CITIES = set(TIER1_CITIES + TIER2_CITIES + TIER3_CITIES + TIER4_CAPITALS + OTHER_CITIES)

# Coordenadas oficiais centrais de cada cidade para evitar loop de portal
TOWNS = {
    'prontera': (156, 191), 'morocc': (156, 93), 'geffen': (119, 59),
    'payon': (162, 233), 'alberta': (192, 147), 'izlude': (128, 114),
    'aldebaran': (140, 131), 'lutie': (147, 134), 'xmas': (147, 134),
    'comodo': (209, 143), 'yuno': (157, 51), 'amatsu': (198, 84),
    'gonryun': (160, 120), 'umbala': (89, 157), 'niflheim': (21, 153),
    'louyang': (217, 100), 'jawaii': (249, 127), 'ayothaya': (151, 117),
    'einbroch': (64, 200), 'lighthalzen': (158, 92), 'einbech': (70, 95),
    'hugel': (96, 145), 'rachel': (130, 110), 'veins': (216, 123),
    'moscovia': (223, 184),
}

# 2. Blacklist Agressiva de Mapas Labirínticos e Confusos
LABYRINTH_BLACKLIST = {
    "prt_maze01", "prt_maze02", "prt_maze03",
    "ama_dun01", "lou_dun01",
    "jupe_area1", "jupe_area2", "jupe_core", "jupe_gate", "jupe_cave",
    "gl_step", "thana_step", "thana_boss",
    "in_sphinx1", "in_sphinx2", "in_sphinx3",
    "anthell01", "anthell02",
    "alde_dun01", "alde_dun02", "alde_dun03", "alde_dun04",
    "c_tower1", "c_tower3", "c_tower4",
    "que_", "job_", "airport", "lhz_airport", "y_airport", "airplane"
}

# 3. Hall da Fama Consagrado (Até Episódio 11.3 Nameless Island)
HALL_OF_FAME = {
    "GREEN": [ # Lv 1 ~ 20 (Verde)
        "prt_fild08", "pay_fild08", "gef_fild07", "moc_fild12",
        "iz_dun00", "prt_sewb1", "xmas_fild01", "pay_fild01"
    ],
    "BLUE": [ # Lv 21 ~ 45 (Azul)
        "pay_dun01", "gef_fild10", "iz_dun02", "moc_pryd01",
        "ice_dun01", "xmas_dun01", "ein_fild08", "mjo_dun01", "prt_sewb2"
    ],
    "RED": [ # Lv 46 ~ 75 (Vermelho)
        "orcsdun02", "pay_dun03", "iz_dun04", "moc_pryd04",
        "in_sphinx4", "ra_san01", "ice_dun02", "thor_v01",
        "abyss_02", "gl_prison", "gl_church", "nif_fild01", "nameless_n"
    ],
    "YELLOW_ACT1": [ # Chefes do Ato 1
        "prt_sewb4", "treasure02", "xmas_dun02", "beach_dun2"
    ],
    "YELLOW_ACT2": [ # Chefes do Ato 2
        "gef_fild03", "gef_dun02", "moc_pryd06", "in_sphinx5", "pay_dun04"
    ],
    "YELLOW_ACT3": [ # Chefes do Ato 3
        "thor_v03", "ice_dun03", "abyss_03", "odin_tem03", "nif_fild02"
    ],
    "CAPITAL_CLIMAX": { # Desafio Final da Capital
        "rachel": ["nameless_n", "abbey01", "abbey02", "abbey03"], # Nameless Island & Beelzebub
        "lighthalzen": ["lhz_dun01", "lhz_dun02", "lhz_dun03"],    # Biolabs 3
        "prontera": ["gl_cas01", "gl_church", "gl_knt02"],         # Baphomet / Glast Heim
    }
}

# Metadados de Nomes Amigáveis para os Chefes
BOSS_NAMES = {
    "prt_sewb4": "Besouro-Ladrão Dourado (GTB)",
    "treasure02": "Capitão Drake",
    "xmas_dun02": "Cavaleiro da Tempestade",
    "beach_dun2": "Tao Gunka",
    "gef_fild03": "Orc Herói",
    "gef_dun02": "Doppelganger",
    "moc_pryd06": "Osíris",
    "in_sphinx5": "Faraó",
    "pay_dun04": "Flor do Luar",
    "thor_v03": "Ifrit",
    "ice_dun03": "Ktullanux",
    "abyss_03": "Detardeurus",
    "odin_tem03": "Valquíria Randgris",
    "nif_fild02": "Senhor dos Mortos",
    "abbey03": "Beelzebub & Fallen Bishop (Nameless Island)",
    "lhz_dun03": "Somatology Biolabs 3",
    "gl_knt02": "Baphomet Supremo (Glast Heim)",
    "ra_san05": "Gloom Under Night"
}

# Padrões protegidos de mapas técnicos
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
        if self.from_map == self.to_map:
            return True
        return False

    def render(self):
        comment_part = f"\t{self.trailing_comment}" if self.trailing_comment else ""
        return f"{self.from_map},{self.from_x},{self.from_y},{self.facing}\t{self.warp_type}\t{self.name}\t{self.span_x},{self.span_y},{self.to_map},{self.to_x},{self.to_y}{comment_part}\n"


def load_gat_cache():
    gat_path = os.path.join(ROOT_DIR, "tools/map_randomizer/gat_cache.json")
    if os.path.isfile(gat_path):
        with open(gat_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_all_warps(dirs_to_scan):
    all_warps = []
    file_lines = defaultdict(list)
    warps_by_from_map = defaultdict(list)

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
                            warps_by_from_map[wp.from_map].append(wp)
                        file_lines[path].append(line)

    return all_warps, file_lines, warps_by_from_map


def build_portal_landing_map(all_warps):
    """
    Constrói o mapa de aterrissagens oficiais seguras para cada portal.
    Localiza os pontos originais de chegada que a Gravity posicionou a 2~10 células do portal.
    """
    orig_landings = defaultdict(list)
    for wp in all_warps:
        if wp.is_valid:
            orig_landings[wp.to_map].append((wp.to_x, wp.to_y))

    portal_landings = {}
    for wp in all_warps:
        if not wp.is_valid:
            continue
        cand = [
            (tx, ty) for (tx, ty) in orig_landings.get(wp.from_map, [])
            if 2.0 <= math.hypot(tx - wp.from_x, ty - wp.from_y) <= 10.0
        ]
        if cand:
            closest = min(cand, key=lambda t: math.hypot(t[0] - wp.from_x, t[1] - wp.from_y))
            portal_landings[(wp.from_map, wp.from_x, wp.from_y)] = closest

    return portal_landings, orig_landings


def get_safe_landing_for_warp(map_name, warp_from_x, warp_from_y, span_x, span_y, portal_landings, orig_landings, gat_cache):
    """
    Retorna uma coordenada de aterrissagem 100% segura e fora da caixa de colisão do portal de retorno.
    Elimina qualquer possibilidade de loop infinito de teleporte.
    """
    # 1. Chegada oficial comprovada deste portal
    if (map_name, warp_from_x, warp_from_y) in portal_landings:
        return portal_landings[(map_name, warp_from_x, warp_from_y)]

    # 2. Outra chegada oficial no mapa suficientemente afastada
    min_dist = max(span_x, span_y) + 2
    cand = [
        t for t in orig_landings.get(map_name, [])
        if min_dist <= math.hypot(t[0] - warp_from_x, t[1] - warp_from_y) <= 12.0
    ]
    if cand:
        return min(cand, key=lambda t: math.hypot(t[0] - warp_from_x, t[1] - warp_from_y))

    # 3. Ponto de centro de cidade (se for cidade)
    if map_name in TOWNS:
        return TOWNS[map_name]

    # 4. Deslocamento geométrico em direção ao centro do mapa
    cx, cy = 150, 150
    if map_name in gat_cache:
        cx = gat_cache[map_name].get("x", 150)
        cy = gat_cache[map_name].get("y", 150)

    offset = max(span_x, span_y) + 4
    dx = offset if warp_from_x < cx else -offset
    dy = offset if warp_from_y < cy else -offset
    return max(5, warp_from_x + dx), max(5, warp_from_y + dy)


def get_map_color_info(target_map):
    """Retorna cor, faixa de nível, efeito visual e cor hex para cada mapa de destino."""
    if target_map in ALL_CAMPAIGN_CITIES:
        return "AZUL", "Cidade Segura (Ponto de Retorno)", "EF_WATERFALL", 0x33CCFF, "BLUE"
    if target_map in HALL_OF_FAME["GREEN"]:
        return "VERDE", "Iniciante (Lv 1 ~ 20)", "EF_SANCTUARY", 0x33FF33, "GREEN"
    if target_map in HALL_OF_FAME["BLUE"]:
        return "AZUL", "Intermediário (Lv 21 ~ 45)", "EF_WATERFALL", 0x3399FF, "BLUE"
    if target_map in HALL_OF_FAME["RED"]:
        return "VERMELHO", "Ameaça Alta (Lv 46 ~ 75)", "EF_FIREPILLAR", 0xFF3333, "RED"
    # Qualquer outro mapa ou Boss / Clímax
    return "AMARELO", "AMEAÇA CRÍTICA / CHEFE (Lv 76 ~ 99+)", "EF_GLORIA", 0xFFFF00, "YELLOW"


def build_curated_campaign(seed_num):
    """
    Constrói deterministicamente a campanha de 4 cidades em profundidade 4 fixa por rota.
    """
    rng = random.Random(seed_num)

    c1 = rng.choice(TIER1_CITIES)
    c2 = rng.choice(TIER2_CITIES)
    c3 = rng.choice(TIER3_CITIES)
    c4 = rng.choice(TIER4_CAPITALS)

    print(f"\n[CAMPAIGN SELECTED BY SEED {seed_num}]")
    print(f"  Tier 1 (Inicial):       {c1.upper()}")
    print(f"  Tier 2 (Intermediária): {c2.upper()}")
    print(f"  Tier 3 (Fronteira):     {c3.upper()}")
    print(f"  Tier 4 (Capital Clímax):{c4.upper()}\n")

    # Pool de mapas disponíveis (embaralhados deterministicamente)
    greens = list(HALL_OF_FAME["GREEN"])
    blues = list(HALL_OF_FAME["BLUE"])
    reds = list(HALL_OF_FAME["RED"])
    rng.shuffle(greens)
    rng.shuffle(blues)
    rng.shuffle(reds)

    act1_bosses = rng.sample(HALL_OF_FAME["YELLOW_ACT1"], 3)
    act2_bosses = rng.sample(HALL_OF_FAME["YELLOW_ACT2"], 3)
    act3_bosses = rng.sample(HALL_OF_FAME["YELLOW_ACT3"], 2)

    campaign_routes = []
    # Estrutura de cada aresta:
    # (from_map, to_map, is_canon, is_gated, gate_boss_req, act_num, route_idx)
    edges = []

    # -------------------------------------------------------------
    # ATO 1: Cidade 1 -> 3 Bosses (Rota 1 aberta, Rotas 2 e 3 liberadas pelo Boss 1)
    # -------------------------------------------------------------
    for i, b in enumerate(act1_bosses):
        g = greens[i % len(greens)]
        u = blues[i % len(blues)]
        r = reds[i % len(reds)]
        is_gated = (i > 0) # Rota 1 é aberta; 2 e 3 são travadas até o Boss 1
        req_boss = act1_bosses[0] if is_gated else None

        # Profundidade 4 fixa: Cidade -> Green -> Blue -> Red -> Boss
        edges.append((c1, g, True, is_gated, req_boss, 1, i + 1))
        edges.append((g, u, True, is_gated, req_boss, 1, i + 1))
        edges.append((u, r, True, is_gated, req_boss, 1, i + 1))
        edges.append((r, b, True, is_gated, req_boss, 1, i + 1))

    # Transição Ato 1 -> Ato 2 (liberada após os 3 bosses de Ato 1)
    edges.append((c1, c2, True, True, "ALL_ACT1", 1, 99))

    # -------------------------------------------------------------
    # ATO 2: Cidade 2 -> 3 Bosses (Todos os 3 caminhos já abertos!)
    # -------------------------------------------------------------
    for i, b in enumerate(act2_bosses):
        g = greens[(i + 3) % len(greens)]
        u = blues[(i + 3) % len(blues)]
        r = reds[(i + 3) % len(reds)]

        # Profundidade 4 fixa: Cidade -> Green -> Blue -> Red -> Boss
        edges.append((c2, g, True, False, None, 2, i + 1))
        edges.append((g, u, True, False, None, 2, i + 1))
        edges.append((u, r, True, False, None, 2, i + 1))
        edges.append((r, b, True, False, None, 2, i + 1))

    # Transição Ato 2 -> Ato 3 (liberada após os 3 bosses de Ato 2)
    edges.append((c2, c3, True, True, "ALL_ACT2", 2, 99))

    # -------------------------------------------------------------
    # ATO 3: Cidade 3 -> 2 Bosses (2 caminhos abertos)
    # -------------------------------------------------------------
    for i, b in enumerate(act3_bosses):
        g = greens[(i + 6) % len(greens)]
        u = blues[(i + 6) % len(blues)]
        r = reds[(i + 6) % len(reds)]

        # Profundidade 4 fixa: Cidade -> Green -> Blue -> Red -> Boss
        edges.append((c3, g, True, False, None, 3, i + 1))
        edges.append((g, u, True, False, None, 3, i + 1))
        edges.append((u, r, True, False, None, 3, i + 1))
        edges.append((r, b, True, False, None, 3, i + 1))

    # Transição Ato 3 -> Capital (liberada após os 2 bosses de Ato 3)
    edges.append((c3, c4, True, True, "ALL_ACT3", 3, 99))

    # -------------------------------------------------------------
    # ATO 4: A Capital & Clímax Supremo
    # -------------------------------------------------------------
    climax_chain = HALL_OF_FAME["CAPITAL_CLIMAX"].get(c4, ["gl_cas01", "gl_church", "gl_knt02"])
    prev = c4
    for idx, next_m in enumerate(climax_chain):
        edges.append((prev, next_m, True, False, None, 4, idx + 1))
        prev = next_m

    # -------------------------------------------------------------
    # CAMINHOS ERRADOS (OFF-PATH / VAZAMENTOS HIGH-END)
    # Adiciona 4 a 6 conexões cruzadas exóticas que desviam da rota canônica
    # -------------------------------------------------------------
    offpath_candidates = [
        # Vazamento do Ato 1 para perigo
        (greens[0], reds[3 % len(reds)]),
        (blues[1], "nameless_n" if "nameless_n" in reds else reds[0]),
        # Vazamento do Ato 2 para perigo
        (greens[3 % len(greens)], act3_bosses[0]),
        (blues[4 % len(blues)], "thor_v01"),
        # Vazamento do Ato 3 para a Capital antes da hora
        (reds[6 % len(reds)], climax_chain[0]),
    ]
    for src, dst in offpath_candidates:
        edges.append((src, dst, False, False, None, 0, 0))

    campaign_meta = {
        "c1": c1, "c2": c2, "c3": c3, "c4": c4,
        "act1_bosses": act1_bosses,
        "act2_bosses": act2_bosses,
        "act3_bosses": act3_bosses,
        "climax_final": climax_chain[-1],
    }

    return edges, campaign_meta


def generate_topology_and_scripts(edges, campaign_meta, all_warps, file_lines, warps_by_from_map, gat_cache, seed_str, portal_landings, orig_landings):
    """
    Amarra os portais físicos (warps) com landing spots seguros e gera o script de auras coloridas e trancas.
    Desativa cidades inativas e portais fora da campanha para eliminar loops e vazamentos.
    """
    used_warps = set()
    configured_connections = []

    def find_free_warp(from_map):
        candidates = warps_by_from_map.get(from_map, [])
        for w in candidates:
            if id(w) not in used_warps:
                used_warps.add(id(w))
                return w
        return None

    # Cidades da campanha ativa vs cidades inativas
    active_cities = {campaign_meta["c1"], campaign_meta["c2"], campaign_meta["c3"], campaign_meta["c4"]}
    inactive_cities = ALL_CITIES - active_cities

    # Conjunto de todos os mapas válidos na campanha
    campaign_maps = set(active_cities)
    for src, dst, _, _, _, _, _ in edges:
        campaign_maps.add(src)
        campaign_maps.add(dst)

    # Processar cada aresta bidirecionalmente
    processed_pairs = set()
    warp_counter = 1

    for src, dst, is_canon, is_gated, req_boss, act_num, route_idx in edges:
        edge_key = (src, dst)
        if edge_key in processed_pairs:
            continue
        processed_pairs.add((src, dst))
        processed_pairs.add((dst, src))

        # 1. Encontrar portal de ida e de volta
        w_fwd = find_free_warp(src)
        w_rev = find_free_warp(dst)

        # 2. Calcular pouso seguro da Ida (em dst, afastado do portal de volta w_rev)
        if w_rev:
            dst_lx, dst_ly = get_safe_landing_for_warp(
                dst, w_rev.from_x, w_rev.from_y, w_rev.span_x, w_rev.span_y,
                portal_landings, orig_landings, gat_cache
            )
        elif dst in TOWNS:
            dst_lx, dst_ly = TOWNS[dst]
        elif dst in gat_cache:
            dst_lx, dst_ly = gat_cache[dst]["x"], gat_cache[dst]["y"]
        else:
            dst_lx, dst_ly = 100, 100

        # 3. Calcular pouso seguro da Volta (em src, afastado do portal de ida w_fwd)
        if w_fwd:
            src_lx, src_ly = get_safe_landing_for_warp(
                src, w_fwd.from_x, w_fwd.from_y, w_fwd.span_x, w_fwd.span_y,
                portal_landings, orig_landings, gat_cache
            )
        elif src in TOWNS:
            src_lx, src_ly = TOWNS[src]
        elif src in gat_cache:
            src_lx, src_ly = gat_cache[src]["x"], gat_cache[src]["y"]
        else:
            src_lx, src_ly = 100, 100

        # 4. Atribuir coordenadas nos warps físicos
        if w_fwd:
            w_fwd.to_map = dst
            w_fwd.to_x = dst_lx
            w_fwd.to_y = dst_ly
            fx, fy = w_fwd.from_x, w_fwd.from_y
            w_name = w_fwd.name
        else:
            fx, fy = src_lx, src_ly
            w_name = f"cwarp_{warp_counter}"
            warp_counter += 1

        if w_rev:
            w_rev.to_map = src
            w_rev.to_x = src_lx
            w_rev.to_y = src_ly
            r_fx, r_fy = w_rev.from_x, w_rev.from_y
            r_name = w_rev.name
        else:
            r_fx, r_fy = dst_lx, dst_ly
            r_name = f"cwarp_{warp_counter}"
            warp_counter += 1

        configured_connections.append((src, dst, is_canon, is_gated, req_boss, fx, fy, w_name))
        configured_connections.append((dst, src, is_canon, False, None, r_fx, r_fy, r_name))

    # Escrever arquivos de warp modificados em data/ e desativar warps de cidades inativas / fora da rota
    for w in all_warps:
        if not w.is_valid:
            continue
        if id(w) in used_warps:
            file_lines[w.file_path][w.line_idx] = w.render()
        else:
            # Preservar interiores de lojas, prédios e castelos (essenciais para jogabilidade)
            if w.is_protected():
                file_lines[w.file_path][w.line_idx] = w.render()
            elif w.from_map in inactive_cities or w.to_map in inactive_cities:
                # Desativa completamente portais em cidades inativas da seed
                file_lines[w.file_path][w.line_idx] = f"// [DISABLED_INACTIVE_CITY] {w.render()}"
            elif w.from_map in active_cities:
                # Nas cidades ativas, desativa portais de campo extras que não pertençam à campanha
                file_lines[w.file_path][w.line_idx] = f"// [DISABLED_CITY_PORTAL] {w.render()}"
            elif w.from_map in campaign_maps and w.to_map not in campaign_maps:
                # Nos mapas de rota, desativa saídas para mapas não participantes
                file_lines[w.file_path][w.line_idx] = f"// [DISABLED_OUT_OF_BOUNDS] {w.render()}"
            else:
                file_lines[w.file_path][w.line_idx] = w.render()

    for path, lines in file_lines.items():
        if "data_base/" in path:
            out_path = path.replace("data_base/", "data/")
        else:
            out_path = path
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="latin-1") as f:
            f.writelines(lines)

    # -------------------------------------------------------------
    # Gerar data/npc/custom/portal_auras.txt com Auras Coloridas e Trancas
    # -------------------------------------------------------------
    aura_content = [
        "//===== rAthena Script =======================================",
        "//= RagnaRogue v4 — Efeitos Visuais de Portais & Selos de Rota",
        f"//= Seed Ativa: {seed_str}",
        "//============================================================",
        "",
        "-	script	PortalAuraController	-1,{",
        "OnInit:",
        f'\t$@cur_world_seed$ = "{seed_str}";',
        f'\t$@cur_world_start_city$ = "{campaign_meta["c1"]}";',
        f'\tquery_sql("INSERT INTO `world_metadata` (`key`, `value`, `updated_at`) VALUES (\'start_city\', \'{campaign_meta["c1"]}\', NOW()) ON DUPLICATE KEY UPDATE `value` = VALUES(`value`), `updated_at` = NOW();");',
        f'\t// Garantir que APENAS a cidade inicial ativa esteja conquistada por padrão',
        f'\tquery_sql("DELETE FROM `world_map_conquests` WHERE `seed` = \'" + $@cur_world_seed$ + "\' AND `map_name` NOT IN (\'{campaign_meta["c1"]}\') AND `conquered_by` = \'Sistema\'");',
        f'\tquery_sql("INSERT IGNORE INTO `world_map_conquests` (`map_name`, `seed`, `conquered_by`, `conquered_at`) VALUES (\'{campaign_meta["c1"]}\', \'" + $@cur_world_seed$ + "\', \'Sistema\', NOW())");',
    ]

    # Desabilitar warps que começam travados
    for src, dst, is_canon, is_gated, req_boss, fx, fy, w_name in configured_connections:
        if is_gated and w_name:
            aura_content.append(f'\tdisablenpc "{w_name}";')

    aura_content.append("\tend;\n}\n")

    # Gerar cada NPC de aura e aviso
    npc_idx = 1
    for src, dst, is_canon, is_gated, req_boss, fx, fy, w_name in configured_connections:
        color_name, tier_desc, ef_name, hex_color, tier_id = get_map_color_info(dst)
        push_x, push_y = get_safe_landing_for_warp(
            src, fx, fy, 2, 2, portal_landings, orig_landings, gat_cache
        )

        boss_desc = BOSS_NAMES.get(req_boss, req_boss) if req_boss else ""

        aura_content.append(f"{src},{fx},{fy},0\tscript\t#paura_{npc_idx}\tHIDDEN_WARP_NPC,1,1,{{")
        aura_content.append("OnInit:")
        aura_content.append("\tinitnpctimer;")
        aura_content.append("\tend;")
        aura_content.append("OnTimer1500:")
        aura_content.append(f"\tspecialeffect {ef_name};")
        if color_name == "AMARELO":
            aura_content.append("\tspecialeffect 568; // Coluna de Luz Dourada Sagrada")
        aura_content.append("\tinitnpctimer;")
        aura_content.append("\tend;")

        aura_content.append("OnTouch:")
        # Verificação de Tranca Condicional
        if is_gated and req_boss:
            aura_content.append(f"\t// Tranca Condicional: Requer {req_boss}")
            if req_boss == "ALL_ACT1":
                b1, b2, b3 = campaign_meta["act1_bosses"]
                aura_content.append(f"\tquery_sql(\"SELECT count(*) FROM `world_map_conquests` WHERE `seed` = '\" + $@cur_world_seed$ + \"' AND `map_name` IN ('{b1}', '{b2}', '{b3}')\", .@done);")
                aura_content.append("\tif (.@done < 3) {")
                aura_content.append('\t\tspecialeffect 458;')
                aura_content.append('\t\tdispbottom "[PORTAL SELADO] O caminho para a próxima cidade exige derrotar os 3 Guardiões do Ato 1!", 0xFF3333;')
                aura_content.append(f'\t\twarp "{src}", {push_x}, {push_y};')
                aura_content.append("\t\tend;")
                aura_content.append("\t}")
                aura_content.append(f'\tquery_sql("INSERT IGNORE INTO `world_map_conquests` (`map_name`, `seed`, `conquered_by`, `conquered_at`) VALUES (\'{campaign_meta["c2"]}\', \'" + $@cur_world_seed$ + "\', \'Sistema\', NOW())");')
                if w_name:
                    aura_content.append(f'\tenablenpc "{w_name}";')
            elif req_boss == "ALL_ACT2":
                b1, b2, b3 = campaign_meta["act2_bosses"]
                aura_content.append(f"\tquery_sql(\"SELECT count(*) FROM `world_map_conquests` WHERE `seed` = '\" + $@cur_world_seed$ + \"' AND `map_name` IN ('{b1}', '{b2}', '{b3}')\", .@done);")
                aura_content.append("\tif (.@done < 3) {")
                aura_content.append('\t\tspecialeffect 458;')
                aura_content.append('\t\tdispbottom "[PORTAL SELADO] O caminho para a próxima cidade exige derrotar os 3 Guardiões do Ato 2!", 0xFF3333;')
                aura_content.append(f'\t\twarp "{src}", {push_x}, {push_y};')
                aura_content.append("\t\tend;")
                aura_content.append("\t}")
                aura_content.append(f'\tquery_sql("INSERT IGNORE INTO `world_map_conquests` (`map_name`, `seed`, `conquered_by`, `conquered_at`) VALUES (\'{campaign_meta["c3"]}\', \'" + $@cur_world_seed$ + "\', \'Sistema\', NOW())");')
                if w_name:
                    aura_content.append(f'\tenablenpc "{w_name}";')
            elif req_boss == "ALL_ACT3":
                b1, b2 = campaign_meta["act3_bosses"]
                aura_content.append(f"\tquery_sql(\"SELECT count(*) FROM `world_map_conquests` WHERE `seed` = '\" + $@cur_world_seed$ + \"' AND `map_name` IN ('{b1}', '{b2}')\", .@done);")
                aura_content.append("\tif (.@done < 2) {")
                aura_content.append('\t\tspecialeffect 458;')
                aura_content.append('\t\tdispbottom "[PORTAL SELADO] O caminho para a Capital Imperial exige derrotar os 2 Guardiões do Ato 3!", 0xFF3333;')
                aura_content.append(f'\t\twarp "{src}", {push_x}, {push_y};')
                aura_content.append("\t\tend;")
                aura_content.append("\t}")
                aura_content.append(f'\tquery_sql("INSERT IGNORE INTO `world_map_conquests` (`map_name`, `seed`, `conquered_by`, `conquered_at`) VALUES (\'{campaign_meta["c4"]}\', \'" + $@cur_world_seed$ + "\', \'Sistema\', NOW())");')
                if w_name:
                    aura_content.append(f'\tenablenpc "{w_name}";')
            else:
                aura_content.append(f"\tquery_sql(\"SELECT count(*) FROM `world_map_conquests` WHERE `seed` = '\" + $@cur_world_seed$ + \"' AND `map_name` = '{req_boss}'\", .@done);")
                aura_content.append("\tif (.@done == 0) {")
                aura_content.append('\t\tspecialeffect 458;')
                aura_content.append(f'\t\tdispbottom "[PORTAL SELADO] Caminho bloqueado! Derrote o Guardião {boss_desc} para quebrar o selo.", 0xFF3333;')
                aura_content.append(f'\t\twarp "{src}", {push_x}, {push_y};')
                aura_content.append("\t\tend;")
                aura_content.append("\t}")
                if w_name:
                    aura_content.append(f'\tenablenpc "{w_name}";')

        # Aviso de Rota Canônica vs Rumo Errado
        if is_canon:
            aura_content.append(f'\tdispbottom "[ROTA DO GUARDIÃO - {color_name}] {tier_desc} -> Rumo a {dst}", {hex_color};')
        else:
            aura_content.append('\tdispbottom "⚠️ [AVISO DE RUMO] Você sente correntes estranhas... este portal parece estar no rumo errado e você poderá se perder profundamente!", 0xFFAA00;')
            aura_content.append(f'\tdispbottom "[PORTAL {color_name}] Perigos do destino: {tier_desc} ({dst})", {hex_color};')

        aura_content.append("\tend;")
        aura_content.append("}\n")
        npc_idx += 1

    # Salvar script em data/ e data_base/
    for script_dir in ["data/npc/custom", "data_base/npc/custom"]:
        out_script = os.path.join(ROOT_DIR, script_dir, "portal_auras.txt")
        os.makedirs(os.path.dirname(out_script), exist_ok=True)
        with open(out_script, "w", encoding="utf-8") as sf:
            sf.write("\n".join(aura_content))

    return configured_connections


def export_topology_report(configured_connections, campaign_meta, output_path, seed_str):
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("==========================================================\n")
        f.write("RAGNAROGUE v4 — CAMPANHA PROCEDURAL DE 4 CIDADES & CORES\n")
        f.write(f"Seed: {seed_str}\n")
        f.write("==========================================================\n\n")

        f.write("PROGRESSÃO DE CIDADES & ATOS:\n")
        f.write(f"  [ATO 1 - Periferia/Início]   Cidade: {campaign_meta['c1'].upper()}\n")
        f.write(f"      Chefes do Ato 1: {', '.join(campaign_meta['act1_bosses'])}\n")
        f.write(f"      Regra: 1 Boss aberto -> abre outros 2 -> abre Cidade 2\n\n")

        f.write(f"  [ATO 2 - Intermediária]      Cidade: {campaign_meta['c2'].upper()}\n")
        f.write(f"      Chefes do Ato 2: {', '.join(campaign_meta['act2_bosses'])}\n")
        f.write(f"      Regra: 3 caminhos já abertos -> derrotar os 3 abre Cidade 3\n\n")

        f.write(f"  [ATO 3 - Fronteira Rápida]   Cidade: {campaign_meta['c3'].upper()}\n")
        f.write(f"      Chefes do Ato 3: {', '.join(campaign_meta['act3_bosses'])}\n")
        f.write(f"      Regra: 2 chefes antes de abrir a Capital Imperial\n\n")

        f.write(f"  [ATO 4 - A Capital / Clímax] Cidade: {campaign_meta['c4'].upper()}\n")
        f.write(f"      Desafio Supremo: {campaign_meta['climax_final'].upper()} ({BOSS_NAMES.get(campaign_meta['climax_final'], 'Endgame')})\n\n")

        f.write("==========================================================\n")
        f.write("CONEXÕES DE PORTAIS & CORES DE DIFICULDADE:\n")
        f.write("==========================================================\n")

        adj = defaultdict(list)
        for src, dst, is_canon, is_gated, req_boss, fx, fy, w_name in configured_connections:
            adj[src].append((dst, is_canon, is_gated, req_boss))

        for src in sorted(adj.keys()):
            f.write(f"\n[{src}]\n")
            for dst, is_canon, is_gated, req_boss in sorted(adj[src]):
                color_name, tier_desc, _, _, _ = get_map_color_info(dst)
                tag_canon = "[CANÔNICA]" if is_canon else "[CAMINHO ERRADO / VAZAMENTO]"
                tag_gate = f" [SELADO: Requer {req_boss}]" if is_gated else ""
                f.write(f"  --> [{color_name}] {dst} ({tier_desc}) {tag_canon}{tag_gate}\n")


def export_sql_connections(configured_connections, seed_str, sql_path, start_city):
    with open(sql_path, "w", encoding="utf-8") as f:
        f.write("-- Topologia Procedural de Conexões de Mapas (v4 Roguelike Pacing)\n")
        f.write(f"DELETE FROM `world_map_connections` WHERE `seed` = '{seed_str}';\n")
        f.write(f"INSERT INTO `world_metadata` (`key`, `value`, `updated_at`) VALUES ('start_city', '{start_city}', NOW()) ON DUPLICATE KEY UPDATE `value` = VALUES(`value`), `updated_at` = NOW();\n")

        seen = set()
        rows = []
        for src, dst, _, _, _, _, _, _ in configured_connections:
            if (src, dst) not in seen:
                seen.add((src, dst))
                rows.append(f"('{src}', '{dst}', '{seed_str}')")

        for i in range(0, len(rows), 100):
            batch = rows[i:i + 100]
            f.write("INSERT IGNORE INTO `world_map_connections` (`from_map`, `to_map`, `seed`) VALUES\n")
            f.write(",\n".join(batch))
            f.write(";\n")


def generate_mob_density_database():
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
    seed_str = os.environ.get("WORLD_SEED", "radiante-evil-druid-1649")
    seed_num = int(os.environ.get("WORLD_SEED_NUMERIC", "1649"))
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        arg1 = sys.argv[1]
        try:
            seed_num = int(arg1)
        except ValueError:
            seed_str = arg1
            try:
                out = subprocess.check_output(["python3", os.path.join(ROOT_DIR, "tools/world_seed.py"), seed_str])
                seed_num = int(out.decode("utf-8").strip())
            except Exception:
                import hashlib
                seed_num = int(hashlib.sha256(seed_str.encode("utf-8")).hexdigest()[:8], 16)

    scan_dirs = [
        os.path.join(ROOT_DIR, "data_base/npc/warps"),
        os.path.join(ROOT_DIR, "data_base/npc/pre-re/warps")
    ]

    print(f"=== [RagnaRogue v4] Gerador de Campanha & Portais Coloridos ===")
    print(f"Seed:    {seed_str} (Numeric: {seed_num})")

    # 1. Carregar densidade de monstros
    map_mobs, mob_sql_path = generate_mob_density_database()
    print(f"  ✓ Banco de densidade de monstros gerado ({len(map_mobs)} mapas).")

    # 2. Carregar todos os warps existentes e GAT cache
    all_warps, file_lines, warps_by_from_map = load_all_warps(scan_dirs)
    gat_cache = load_gat_cache()
    portal_landings, orig_landings = build_portal_landing_map(all_warps)
    print(f"  ✓ Total de warps lidos: {len(all_warps)} ({len(portal_landings)} pontos oficiais de chegada mapeados)")

    # 3. Construir a Campanha Determinística de 4 Cidades com Profundidade 4
    edges, campaign_meta = build_curated_campaign(seed_num)

    # 4. Gerar conexões de warps físicos e script de auras coloridas
    configured_connections = generate_topology_and_scripts(
        edges, campaign_meta, all_warps, file_lines, warps_by_from_map, gat_cache, seed_str,
        portal_landings, orig_landings
    )
    print(f"  ✓ {len(configured_connections) // 2} rotas de portais geradas com sucesso!")
    print(f"  ✓ Script de Auras Coloridas e Trancas gerado em data/npc/custom/portal_auras.txt")

    # 5. Gerar mapflags de loadevent para garantir eventos em todos os mapas
    map_index_path = os.path.join(ROOT_DIR, "data_base/db/map_index.txt")
    if os.path.isfile(map_index_path):
        with open(map_index_path, "r") as mif:
            m_lines = [l.strip() for l in mif if l.strip() and not l.startswith("//")]
        loadevent_content = "// Mapflags de loadevent para RagnaRogue v4\n"
        for ml in m_lines:
            parts = ml.split()
            if parts:
                loadevent_content += f"{parts[0]}\tmapflag\tloadevent\n"
        for mf_dir in ["data_base/npc/custom", "data/npc/custom"]:
            out_mf = os.path.join(ROOT_DIR, mf_dir, "mapflags_loadevent.txt")
            os.makedirs(os.path.dirname(out_mf), exist_ok=True)
            with open(out_mf, "w") as mfo:
                mfo.write(loadevent_content)
        print(f"  ✓ Mapflags de loadevent gerados para {len(m_lines)} mapas!")

    # 6. Exportar relatórios e banco SQL
    report_path = os.path.join(ROOT_DIR, "data/world_topology.txt")
    export_topology_report(configured_connections, campaign_meta, report_path, seed_str)
    print(f"  ✓ Relatório da campanha salvo em: {report_path}")

    sql_path = os.path.join(ROOT_DIR, "data/world_map_connections.sql")
    export_sql_connections(configured_connections, seed_str, sql_path, campaign_meta["c1"])
    print(f"  ✓ Conexões SQL salvas em: {sql_path}")

    # 7. Sincronizar com MariaDB se o container estiver rodando
    try:
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

    print(f"=== Concluído com sucesso! Campanha RagnaRogue v4 ativa. ===")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
tools/generate_seed.py

Gera uma semente aleatória temática para o Ragnarok no formato:
  adjetivo-nome-de-monstro-numero
Exemplos:
  furioso-poring-42
  sombrio-baphomet-777
  mistico-deviruchi-108
"""

import os
import random
import re
import sys

ADJETIVOS = [
    "furioso", "sombrio", "veloz", "valente", "lendario",
    "mistico", "caotico", "eterno", "flamejante", "congelante",
    "eletrico", "selvagem", "ancestral", "corajoso", "titanico",
    "sagrado", "infernal", "arcano", "brilhante", "espectral",
    "voraz", "silencioso", "temivel", "implacavel", "poderoso",
    "radiante", "noturno", "cosmico", "feroz", "colossal",
    "imortal", "fantasma", "glorioso", "divino", "abissal",
    "dourado", "cristalino", "tempestuoso", "sanguinario", "astral"
]

MONSTROS_ICÔNICOS = [
    "poring", "lunatic", "deviruchi", "baphomet", "pecopeco",
    "poporing", "marin", "spore", "fabre", "hydra",
    "chonchon", "ghostring", "angeling", "deviling", "archangeling",
    "orc-hero", "orc-lord", "maya", "osiris", "drake",
    "eddga", "moonlight", "phreeoni", "doppelganger", "mistress",
    "golden-thief-bug", "goblin", "kobold", "whisper", "smokey",
    "savage", "munak", "bongun", "bathory", "raydric",
    "wanderer", "abysmal-knight", "atroce", "valkyrie-randgris", "amon-ra",
    "dark-lord", "evil-druid", "gargoyle", "golem", "harpy",
    "injustice", "joker", "khalitzburg", "medusa", "minorous",
    "mummy", "nightmare", "pasana", "pyuriel", "requiem",
    "sohee", "strouf", "succubus", "taogunka", "zombie",
    "anubis", "dracula", "garm", "iffit", "beelzebub"
]


def extrair_monstros_mob_db():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidatos = [
        os.path.join(root, "data/db/pre-re/mob_db.txt"),
        os.path.join(root, "data_base/db/pre-re/mob_db.txt"),
    ]
    palavras_bloqueadas = {
        "flower", "plant", "egg", "chest", "dummy", "target", "treasure",
        "crystal", "bomb", "box", "trap", "mushroom", "marine-sphere",
        "warp", "hidden", "event", "shadow-of"
    }
    mobs = set(MONSTROS_ICÔNICOS)
    for caminho in candidatos:
        if os.path.isfile(caminho):
            try:
                with open(caminho, "r", encoding="latin-1") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("//"):
                            continue
                        cols = line.split(",")
                        if len(cols) >= 3:
                            nome = cols[2].strip()
                            nome_slug = re.sub(r'[^a-zA-Z0-9]+', '-', nome).strip('-').lower()
                            if 3 <= len(nome_slug) <= 15 and not any(p in nome_slug for p in palavras_bloqueadas):
                                mobs.add(nome_slug)
            except Exception:
                pass
            if len(mobs) > len(MONSTROS_ICÔNICOS):
                break
    return list(mobs)


def gerar_seed():
    adjetivo = random.choice(ADJETIVOS)
    # 85% de chance de usar monstro icônico clássico, ou outros monstros válidos
    todos_monstros = extrair_monstros_mob_db()
    if random.random() < 0.85:
        monstro = random.choice(MONSTROS_ICÔNICOS)
    else:
        monstro = random.choice(todos_monstros)
    numero = random.randint(10, 9999)
    return f"{adjetivo}-{monstro}-{numero}"


if __name__ == "__main__":
    seed = gerar_seed()
    print(seed)

#!/usr/bin/env python3
"""
tools/manage_translations.py

Gerenciador de Traduções PT-BR (Cronus -> rAthena).
Permite listar, diffar, aplicar, restaurar e validar traduções com o map-server.
"""

import argparse
import difflib
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CRONUS_NPC = os.path.join(ROOT, "cronus_base", "npc")
RATHENA_NPC = os.path.join(ROOT, "data", "npc")
BACKUP_DIR = os.path.join(ROOT, "data", "npc_backups")

# Mapeamento completo de diretórios rAthena -> Cronus
MODULES = {
    "kafras": {
        "rathena_dir": "kafras",
        "cronus_dir": "kafras",
        "files": {
            "kafras.txt": "kafras.txt",
            "functions_kafras.txt": "functions_kafras.txt",
            "cool_event_corp.txt": "cool_event_corp.txt",
            "dts_warper.txt": "dts_warper.txt",
            "../pre-re/kafras/kafras.txt": "../pre-re/kafras/kafras.txt",
        }
    },
    "cities": {
        "rathena_dir": "cities",
        "cronus_dir": "cidades",
        "files": {
            "prontera.txt": "prontera.txt",
            "geffen.txt": "geffen.txt",
            "morocc.txt": "morocc.txt",
            "payon.txt": "payon.txt",
            "alberta.txt": "alberta.txt",
            "aldebaran.txt": "aldebaran.txt",
            "comodo.txt": "comodo.txt",
            "izlude.txt": "izlude.txt",
            "lutie.txt": "lutie.txt",
            "yuno.txt": "yuno.txt",
            "amatsu.txt": "amatsu.txt",
            "gonryun.txt": "gonryun.txt",
            "umbala.txt": "umbala.txt",
            "niflheim.txt": "niflheim.txt",
            "louyang.txt": "louyang.txt",
            "jawaii.txt": "jawaii.txt",
            "ayothaya.txt": "ayothaya.txt",
            "einbroch.txt": "einbroch.txt",
            "lighthalzen.txt": "lighthalzen.txt",
            "einbech.txt": "einbech.txt",
            "hugel.txt": "hugel.txt",
            "rachel.txt": "rachel.txt",
            "veins.txt": "veins.txt",
            "moscovia.txt": "moscovia.txt",
            "manuk.txt": "manuk.txt",
            "splendide.txt": "splendide.txt",
            "../pre-re/cities/alberta.txt": "../pre-re/cidades/alberta.txt",
            "../pre-re/cities/izlude.txt": "../pre-re/cidades/izlude.txt",
            "../pre-re/cities/jawaii.txt": "../pre-re/cidades/jawaii.txt",
            "../pre-re/cities/yuno.txt": "../pre-re/cidades/yuno.txt",
        }
    },
    "airports": {
        "rathena_dir": "airports",
        "cronus_dir": "aeroportos",
        "files": {
            "airships.txt": "aeroplano.txt",
            "einbroch.txt": "einbroch.txt",
            "hugel.txt": "hugel.txt",
            "izlude.txt": "izlude.txt",
            "lighthalzen.txt": "lighthalzen.txt",
            "rachel.txt": "rachel.txt",
            "yuno.txt": "yuno.txt",
            "../pre-re/airports/izlude.txt": "../pre-re/aeroportos/izlude.txt",
        }
    },
    "guides": {
        "rathena_dir": "pre-re/guides",
        "cronus_dir": "pre-re/guias",
        "files": {
            "guides_alberta.txt": "guias_alberta.txt",
            "guides_aldebaran.txt": "guias_aldebaran.txt",
            "guides_amatsu.txt": "guias_amatsu.txt",
            "guides_ayothaya.txt": "guias_ayothaya.txt",
            "guides_comodo.txt": "guias_comodo.txt",
            "guides_einbroch.txt": "guias_einbroch.txt",
            "guides_geffen.txt": "guias_geffen.txt",
            "guides_gonryun.txt": "guias_gonryun.txt",
            "guides_hugel.txt": "guias_hugel.txt",
            "guides_izlude.txt": "guias_izlude.txt",
            "guides_juno.txt": "guias_juno.txt",
            "guides_lighthalzen.txt": "guias_lighthalzen.txt",
            "guides_louyang.txt": "guias_louyang.txt",
            "guides_morroc.txt": "guias_morroc.txt",
            "guides_moscovia.txt": "guias_moscovia.txt",
            "guides_niflheim.txt": "guias_niflheim.txt",
            "guides_payon.txt": "guias_payon.txt",
            "guides_prontera.txt": "guias_prontera.txt",
            "guides_rachel.txt": "guias_rachel.txt",
            "guides_umbala.txt": "guias_umbala.txt",
            "guides_veins.txt": "guias_veins.txt",
        }
    },
    "merchants": {
        "rathena_dir": "merchants",
        "cronus_dir": "comerciantes",
        "files": {
            "advanced_refiner.txt": "advanced_refiner.txt",
            "alchemist.txt": "Alquimia.txt",
            "buying_shops.txt": "buying_shops.txt",
            "coin_exchange.txt": "coin_exchange.txt",
            "dye_maker.txt": "Fabricar_Tinturas.txt",
            "elemental_trader.txt": "elemental_trader.txt",
            "enchan_arm.txt": "Encantar_Armaduras.txt",
            "gemstone.txt": "Troca_de_Gemas.txt",
            "hair_dyer.txt": "hair_dyer.txt",
            "hair_style.txt": "hair_style.txt",
            "inn.txt": "Hospedarias.txt",
            "kunai_maker.txt": "Fabricar_Kunais.txt",
            "milk_trader.txt": "milk_trader.txt",
            "novice_exchange.txt": "novice_exchange.txt",
            "old_pharmacist.txt": "Velho_Famaceutico.txt",
            "quivers.txt": "Aljaves.txt",
            "refine.txt": "Refinamento.txt",
            "renters.txt": "Aluguel.txt",
            "shops.txt": "Lojas.txt",
            "socket_enchant.txt": "Seiyablem.txt",
            "socket_enchant2.txt": "Leablem.txt",
            "wander_pet_food.txt": "wander_pet_food.txt",
            "cashheadgear_dye.txt": "cashheadgear_dye.txt",
            "../pre-re/merchants/ammo_boxes.txt": "../pre-re/comerciantes/Caixa_de_Municao.txt",
            "../pre-re/merchants/ammo_dealer.txt": "../pre-re/comerciantes/Criar_Municoes.txt",
            "../pre-re/merchants/shops.txt": "../pre-re/comerciantes/shops.txt",
            "../pre-re/merchants/socket_enchant2.txt": "Leablem.txt",
        }
    },
    "instances": {
        "rathena_dir": "instances",
        "cronus_dir": "instancias",
        "files": {
            "EndlessTower.txt": "Torre_Sem_Fim.txt",
            "NydhoggsNest.txt": "Ninho_de_Nidhogg.txt",
            "OrcsMemory.txt": "Memorial_dos_Orcs.txt",
            "SealedShrine.txt": "Altar_do_Selo.txt",
        }
    },
    "other": {
        "rathena_dir": "other",
        "cronus_dir": "outros",
        "files": {
            "auction.txt": "auction.txt",
            "books.txt": "books.txt",
            "bulletin_boards.txt": "bulletin_boards.txt",
            "comodo_gambling.txt": "comodo_gambling.txt",
            "divorce.txt": "divorce.txt",
            "fortune.txt": "fortune.txt",
            "gm_npcs.txt": "gm_npcs.txt",
            "guildpvp.txt": "guildpvp.txt",
            "gympass.txt": "gympass.txt",
            "hugel_bingo.txt": "hugel_bingo.txt",
            "mail.txt": "mail.txt",
            "marriage.txt": "marriage.txt",
            "mercenary_rent.txt": "mercenary_rent.txt",
            "monster_museum.txt": "monster_museum.txt",
            "monster_race.txt": "monster_race.txt",
            "poring_war.txt": "poring_war.txt",
            "powernpc.txt": "powernpc.txt",
            "pvp.txt": "pvp.txt",
            "turbo_track.txt": "turbo_track.txt",
            "arena/arena_aco.txt": "../pre-re/outros/arena/arena_aco.txt",
            "arena/arena_lvl50.txt": "../pre-re/outros/arena/arena_lvl50.txt",
            "arena/arena_lvl60.txt": "../pre-re/outros/arena/arena_lvl60.txt",
            "arena/arena_lvl70.txt": "../pre-re/outros/arena/arena_lvl70.txt",
            "arena/arena_lvl80.txt": "../pre-re/outros/arena/arena_lvl80.txt",
            "arena/arena_party.txt": "../pre-re/outros/arena/arena_party.txt",
            "arena/arena_point.txt": "../pre-re/outros/arena/arena_point.txt",
            "arena/arena_room.txt": "../pre-re/outros/arena/arena_room.txt",
            "../pre-re/other/bulletin_boards.txt": "../pre-re/outros/bulletin_boards.txt",
            "../pre-re/other/mercenary_rent.txt": "../pre-re/outros/mercenary_rent.txt",
            "../pre-re/other/pvp.txt": "../pre-re/outros/pvp.txt",
            "../pre-re/other/msg_boards.txt": "../pre-re/outros/msg_boards.txt",
            "../pre-re/other/resetskill.txt": "../pre-re/outros/resetskill.txt",
            "../pre-re/other/turbo_track.txt": "../pre-re/outros/turbo_track.txt",
        }
    },
    "jobs": {
        "rathena_dir": "jobs",
        "cronus_dir": "classes",
        "files": {
            "../pre-re/jobs/1-1/acolyte.txt": "../pre-re/classes/1-1/novico.txt",
            "../pre-re/jobs/1-1/archer.txt": "../pre-re/classes/1-1/arqueiro.txt",
            "../pre-re/jobs/1-1/mage.txt": "../pre-re/classes/1-1/mago.txt",
            "../pre-re/jobs/1-1/merchant.txt": "../pre-re/classes/1-1/mercador.txt",
            "../pre-re/jobs/1-1/swordman.txt": "../pre-re/classes/1-1/espadachim.txt",
            "../pre-re/jobs/1-1/thief.txt": "../pre-re/classes/1-1/gatuno.txt",
            "../pre-re/jobs/1-1e/taekwon.txt": "Expandida/1-1/taekwon.txt",
            "../pre-re/jobs/2-2/crusader.txt": "Segunda/2-2/templario.txt",
            "1-1e/gunslinger.txt": "Expandida/1-1/justiceiro.txt",
            "1-1e/ninja.txt": "Expandida/1-1/ninja.txt",
            "1-1e/taekwon.txt": "Expandida/1-1/taekwon.txt",
            "2-1/assassin.txt": "Segunda/2-1/mercenario.txt",
            "2-1/blacksmith.txt": "Segunda/2-1/ferreiro.txt",
            "2-1/hunter.txt": "Segunda/2-1/cacador.txt",
            "2-1/knight.txt": "Segunda/2-1/cavaleiro.txt",
            "2-1/priest.txt": "Segunda/2-1/sacerdote.txt",
            "2-1/wizard.txt": "Segunda/2-1/bruxo.txt",
            "2-1a/AssassinCross.txt": "Transcendental/2-1/algoz.txt",
            "2-1a/HighPriest.txt": "Transcendental/2-1/sumo_sacerdote.txt",
            "2-1a/HighWizard.txt": "Transcendental/2-1/arquimago.txt",
            "2-1a/LordKnight.txt": "Transcendental/2-1/lorde.txt",
            "2-1a/Sniper.txt": "Transcendental/2-1/atirador_de_elite.txt",
            "2-1a/WhiteSmith.txt": "Transcendental/2-1/mestre_ferreiro.txt",
            "2-1e/StarGladiator.txt": "Expandida/2-1/StarGladiator.txt",
            "2-2/alchemist.txt": "Segunda/2-2/alquimista.txt",
            "2-2/bard.txt": "Segunda/2-2/bardo.txt",
            "2-2/crusader.txt": "Segunda/2-2/templario.txt",
            "2-2/dancer.txt": "Segunda/2-2/odalisca.txt",
            "2-2/monk.txt": "Segunda/2-2/monge.txt",
            "2-2/rogue.txt": "Segunda/2-2/arruaceiro.txt",
            "2-2/sage.txt": "Segunda/2-2/sabio.txt",
            "2-2a/Champion.txt": "Transcendental/2-2/mestre.txt",
            "2-2a/Clown.txt": "Transcendental/2-2/menestrel.txt",
            "2-2a/Creator.txt": "Transcendental/2-2/criador.txt",
            "2-2a/Gypsy.txt": "Transcendental/2-2/cigana.txt",
            "2-2a/Paladin.txt": "Transcendental/2-2/paladino.txt",
            "2-2a/Professor.txt": "Transcendental/2-2/professor.txt",
            "2-2a/Stalker.txt": "Transcendental/2-2/desordeiro.txt",
            "2-2e/SoulLinker.txt": "Expandida/2-2/SoulLinker.txt",
            "novice/supernovice.txt": "Expandida/supernovice.txt",
            "valkyrie.txt": "Transcendental/valkyrie.txt",
            "../quests/skills/acolyte_skills.txt": "Habilidades/1-1/acolyte_skills.txt",
            "../quests/skills/archer_skills.txt": "Habilidades/1-1/archer_skills.txt",
            "../quests/skills/mage_skills.txt": "Habilidades/1-1/mage_skills.txt",
            "../quests/skills/merchant_skills.txt": "Habilidades/1-1/merchant_skills.txt",
            "../quests/skills/swordman_skills.txt": "Habilidades/1-1/swordman_skills.txt",
            "../quests/skills/thief_skills.txt": "Habilidades/1-1/thief_skills.txt",
            "../quests/skills/assassin_skills.txt": "Habilidades/2-1/assassin_skills.txt",
            "../quests/skills/blacksmith_skills.txt": "Habilidades/2-1/blacksmith_skills.txt",
            "../quests/skills/hunter_skills.txt": "Habilidades/2-1/hunter_skills.txt",
            "../quests/skills/knight_skills.txt": "Habilidades/2-1/knight_skills.txt",
            "../quests/skills/priest_skills.txt": "Habilidades/2-1/priest_skills.txt",
            "../quests/skills/wizard_skills.txt": "Habilidades/2-1/wizard_skills.txt",
            "../quests/skills/alchemist_skills.txt": "Habilidades/2-2/alchemist_skills.txt",
            "../quests/skills/bard_skills.txt": "Habilidades/2-2/bard_skills.txt",
            "../quests/skills/crusader_skills.txt": "Habilidades/2-2/crusader_skills.txt",
            "../quests/skills/dancer_skills.txt": "Habilidades/2-2/dancer_skills.txt",
            "../quests/skills/monk_skills.txt": "Habilidades/2-2/monk_skills.txt",
            "../quests/skills/rogue_skills.txt": "Habilidades/2-1/rogue_skills.txt",
            "../quests/skills/sage_skills.txt": "Habilidades/2-2/sage_skills.txt",
            "../quests/skills/novice_skills.txt": "Habilidades/novice_skills.txt",
            "../pre-re/quests/skills/swordman_skills.txt": "Habilidades/1-1/swordman_skills.txt",
        }
    },
    "quests": {
        "rathena_dir": "quests",
        "cronus_dir": "quests",
        "files": {
            "quests_alberta.txt": "cidades/Alberta.txt",
            "quests_aldebaran.txt": "cidades/Aldebaran.txt",
            "quests_amatsu.txt": "cidades/Amatsu.txt",
            "quests_ayothaya.txt": "cidades/Ayothaya.txt",
            "quests_comodo.txt": "cidades/Comodo.txt",
            "quests_ein.txt": "cidades/Ein.txt",
            "quests_geffen.txt": "cidades/Geffen.txt",
            "quests_gonryun.txt": "cidades/Gonryun.txt",
            "quests_hugel.txt": "cidades/Hugel.txt",
            "quests_izlude.txt": "cidades/Izlude.txt",
            "quests_juperos.txt": "cidades/Juperos.txt",
            "quests_lighthalzen.txt": "cidades/Lighthalzen.txt",
            "quests_louyang.txt": "cidades/Louyang.txt",
            "quests_lutie.txt": "cidades/Lutie.txt",
            "quests_morocc.txt": "cidades/Morocc.txt",
            "quests_moscovia.txt": "cidades/Moscovia.txt",
            "quests_niflheim.txt": "cidades/Niflheim.txt",
            "quests_payon.txt": "cidades/Payon.txt",
            "quests_prontera.txt": "cidades/Prontera.txt",
            "quests_rachel.txt": "cidades/Rachel.txt",
            "quests_umbala.txt": "cidades/Umbala.txt",
            "quests_veins.txt": "cidades/Veins.txt",
            "quests_yuno.txt": "cidades/Yuno.txt",
            "bard_quest.txt": "bard_quest.txt",
            "cooking_quest.txt": "cooking_quest.txt",
            "counteragent_mixture.txt": "counteragent_mixture.txt",
            "doomed_swords.txt": "doomed_swords.txt",
            "doomed_swords_quest.txt": "doomed_swords_quest.txt",
            "eye_of_hellion.txt": "eye_of_hellion.txt",
            "guildrelay.txt": "guildrelay.txt",
            "gunslinger_quests.txt": "gunslinger_quests.txt",
            "juice_maker.txt": "juice_maker.txt",
            "kiel_hyre_quest.txt": "kiel_hyre_quest.txt",
            "lvl4_weapon_quest.txt": "lvl4_weapon_quest.txt",
            "mage_solution.txt": "mage_solution.txt",
            "monstertamers.txt": "monstertamers.txt",
            "ninja_quests.txt": "ninja_quests.txt",
            "obb_quest.txt": "obb_quest.txt",
            "okolnir.txt": "okolnir.txt",
            "partyrelay.txt": "partyrelay.txt",
            "quests_13_1.txt": "quests_13_1.txt",
            "quests_13_2.txt": "quests_13_2.txt",
            "quests_airship.txt": "quests_airship.txt",
            "quests_nameless.txt": "quests_nameless.txt",
            "thana_quest.txt": "thana_quest.txt",
            "the_sign_quest.txt": "the_sign_quest.txt",
            "newgears/2004_headgears.txt": "chapeus/2004_headgears.txt",
            "newgears/2005_headgears.txt": "chapeus/2005_headgears.txt",
            "newgears/2006_headgears.txt": "chapeus/2006_headgears.txt",
            "newgears/2008_headgears.txt": "chapeus/2008_headgears.txt",
            "bunnyband.txt": "chapeus/bunnyband.txt",
            "mrsmile.txt": "chapeus/mrsmile.txt",
            "first_class/tu_acolyte.txt": "first_class/tu_acolyte.txt",
            "first_class/tu_archer.txt": "first_class/tu_archer.txt",
            "first_class/tu_ma_th01.txt": "first_class/tu_ma_th01.txt",
            "first_class/tu_magician01.txt": "first_class/tu_magician01.txt",
            "first_class/tu_merchant.txt": "first_class/tu_merchant.txt",
            "first_class/tu_sword.txt": "first_class/tu_sword.txt",
            "first_class/tu_thief01.txt": "first_class/tu_thief01.txt",
            "seals/brisingamen_seal.txt": "seals/brisingamen_seal.txt",
            "seals/god_weapon_creation.txt": "seals/god_weapon_creation.txt",
            "seals/megingard_seal.txt": "seals/megingard_seal.txt",
            "seals/mjolnir_seal.txt": "seals/mjolnir_seal.txt",
            "seals/seal_status.txt": "seals/seal_status.txt",
            "seals/sleipnir_seal.txt": "seals/sleipnir_seal.txt",
            "../pre-re/quests/cooking_quest.txt": "cooking_quest.txt",
            "../pre-re/quests/monstertamers.txt": "monstertamers.txt",
            "../pre-re/quests/mrsmile.txt": "chapeus/mrsmile.txt",
            "../pre-re/quests/quests_13_1.txt": "quests_13_1.txt",
            "../pre-re/quests/quests_izlude.txt": "cidades/Izlude.txt",
            "../pre-re/quests/quests_lighthalzen.txt": "cidades/Lighthalzen.txt",
            "../pre-re/quests/quests_nameless.txt": "quests_nameless.txt",
            "../pre-re/quests/the_sign_quest.txt": "the_sign_quest.txt",
            "../pre-re/quests/quests_veins.txt": "cidades/Veins.txt",
            "../pre-re/quests/quests_morocc.txt": "cidades/Morocc.txt",
            "../pre-re/quests/first_class/tu_archer.txt": "first_class/tu_archer.txt",
            "../pre-re/quests/seals/brisingamen_seal.txt": "seals/brisingamen_seal.txt",
            "../pre-re/quests/seals/megingard_seal.txt": "seals/megingard_seal.txt",
        }
    },
    "battleground": {
        "rathena_dir": "battleground",
        "cronus_dir": "campal",
        "files": {
            "flavius/flavius01.txt": "flavius/flavius01.txt",
            "flavius/flavius02.txt": "flavius/flavius02.txt",
            "flavius/flavius_enter.txt": "flavius/flavius_entrada.txt",
            "kvm/kvm01.txt": "kvm/kvm01.txt",
            "kvm/kvm02.txt": "kvm/kvm02.txt",
            "kvm/kvm03.txt": "kvm/kvm03.txt",
            "kvm/kvm_enter.txt": "kvm/kvm_entrada.txt",
            "kvm/kvm_item_pay.txt": "kvm/kvm_shop.txt",
            "tierra/tierra01.txt": "tierra/tierra01.txt",
            "tierra/tierra02.txt": "tierra/tierra02.txt",
            "tierra/tierra_enter.txt": "tierra/tierra_entrada.txt",
            "bg_common.txt": "bg_comum.txt",
        }
    },
    "events": {
        "rathena_dir": "events",
        "cronus_dir": "eventos",
        "files": {
            "gdevent_aru.txt": "gdevent_aru.txt",
            "gdevent_sch.txt": "gdevent_sch.txt",
            "god_se_festival.txt": "god_se_festival.txt",
        }
    }
}


def read_lines(filepath):
    """Lê arquivo em latin-1/windows-1252 para manter compatibilidade exata."""
    if not os.path.isfile(filepath):
        return []
    with open(filepath, "r", encoding="latin-1", errors="ignore") as f:
        return f.readlines()


def cmd_list(args):
    print("==================================================")
    print("Módulos de Tradução Disponíveis (Cronus -> rAthena)")
    print("==================================================")
    total_files = 0
    ready_files = 0
    for mod_name, mod in MODULES.items():
        print(f"\nMódulo: [{mod_name}] ({mod['rathena_dir']} <-> {mod['cronus_dir']})")
        for r_file, c_file in mod["files"].items():
            r_path = os.path.normpath(os.path.join(RATHENA_NPC, mod["rathena_dir"], r_file))
            c_path = os.path.normpath(os.path.join(CRONUS_NPC, mod["cronus_dir"], c_file))

            r_ok = os.path.isfile(r_path)
            c_ok = os.path.isfile(c_path)

            status = "[PRONTO]" if (r_ok and c_ok) else "[AUSENTE]"
            total_files += 1
            if r_ok and c_ok:
                ready_files += 1
            print(f"  {status} {r_file:35} <- cronus:{c_file}")
    print(f"\nTotal: {ready_files}/{total_files} arquivos prontos para sincronização.")


def cmd_diff(args):
    mod_name = args.module
    if mod_name not in MODULES:
        print(f"[ERRO] Módulo desconhecido: {mod_name}. Opções: {list(MODULES.keys())}")
        sys.exit(1)

    mod = MODULES[mod_name]
    target_file = getattr(args, "file", None)

    for r_file, c_file in mod["files"].items():
        if target_file and target_file != r_file:
            continue

        r_path = os.path.normpath(os.path.join(RATHENA_NPC, mod["rathena_dir"], r_file))
        c_path = os.path.normpath(os.path.join(CRONUS_NPC, mod["cronus_dir"], c_file))

        if not os.path.isfile(r_path) or not os.path.isfile(c_path):
            continue

        r_lines = read_lines(r_path)
        c_lines = read_lines(c_path)

        diff = list(difflib.unified_diff(
            r_lines[:150], c_lines[:150],
            fromfile=f"rAthena/{r_file}",
            tofile=f"Cronus/{c_file}",
            n=2
        ))

        if diff:
            print("--------------------------------------------------")
            print(f"Diff: {r_file} vs {c_file} (Amostra primeiras linhas)")
            print("--------------------------------------------------")
            for line in diff[:35]:
                sys.stdout.write(line)
            if len(diff) > 35:
                print(f"... ({len(diff)-35} linhas omitidas)")


def cmd_apply(args):
    mod_name = args.module
    if mod_name not in MODULES and mod_name != "all":
        print(f"[ERRO] Módulo desconhecido: {mod_name}. Opções: {list(MODULES.keys())} ou 'all'")
        sys.exit(1)

    mods_to_apply = MODULES.keys() if mod_name == "all" else [mod_name]
    target_file = getattr(args, "file", None)

    os.makedirs(BACKUP_DIR, exist_ok=True)
    applied_count = 0

    for m in mods_to_apply:
        mod = MODULES[m]
        for r_file, c_file in mod["files"].items():
            if target_file and target_file != r_file:
                continue

            r_path = os.path.normpath(os.path.join(RATHENA_NPC, mod["rathena_dir"], r_file))
            c_path = os.path.normpath(os.path.join(CRONUS_NPC, mod["cronus_dir"], c_file))

            if not os.path.isfile(c_path):
                print(f"[PULAR] Arquivo Cronus não encontrado: {c_path}")
                continue

            # Backup
            if os.path.isfile(r_path):
                rel_bkp = os.path.relpath(r_path, RATHENA_NPC)
                bkp_target = os.path.join(BACKUP_DIR, rel_bkp + ".bak")
                os.makedirs(os.path.dirname(bkp_target), exist_ok=True)
                if not os.path.isfile(bkp_target):
                    shutil.copy2(r_path, bkp_target)

            # Aplica tradução
            os.makedirs(os.path.dirname(r_path), exist_ok=True)
            shutil.copy2(c_path, r_path)
            applied_count += 1

    print(f"\nSucesso! {applied_count} arquivo(s) traduzido(s).")
    if getattr(args, "test", False):
        cmd_test(args)


def cmd_restore(args):
    mod_name = args.module
    if mod_name not in MODULES and mod_name != "all":
        print(f"[ERRO] Módulo desconhecido: {mod_name}")
        sys.exit(1)

    mods_to_restore = MODULES.keys() if mod_name == "all" else [mod_name]
    target_file = getattr(args, "file", None)

    restored_count = 0
    for m in mods_to_restore:
        mod = MODULES[m]
        for r_file in mod["files"].keys():
            if target_file and target_file != r_file:
                continue

            r_path = os.path.normpath(os.path.join(RATHENA_NPC, mod["rathena_dir"], r_file))
            rel_bkp = os.path.relpath(r_path, RATHENA_NPC)
            bkp_path = os.path.join(BACKUP_DIR, rel_bkp + ".bak")

            if os.path.isfile(bkp_path):
                shutil.copy2(bkp_path, r_path)
                print(f"[RESTAURADO] {rel_bkp} (via backup)")
                restored_count += 1
            else:
                db_path = os.path.join(ROOT, "data_base", "npc", rel_bkp)
                if os.path.isfile(db_path):
                    shutil.copy2(db_path, r_path)
                    print(f"[RESTAURADO] {rel_bkp} (via data_base original)")
                    restored_count += 1

    print(f"\n{restored_count} arquivo(s) restaurado(s).")


def cmd_test(args):
    print("\nValidando sintaxe dos scripts com o rAthena map-server (--run-once)...")
    res = subprocess.run(
        ["docker", "exec", "ragnarok-server", "/opt/rathena/map-server", "--run-once"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="latin-1"
    )
    if res.returncode == 0:
        print("[SUCESSO] rAthena carregou todos os scripts sem nenhum erro fatal!")
    else:
        print(f"[ERRO] Falha ao carregar scripts (código {res.returncode}):")
        lines = res.stdout.splitlines()
        for line in lines[-25:]:
            print(f"  {line}")


def main():
    parser = argparse.ArgumentParser(description="Gerenciador de Traduções Cronus -> rAthena")
    subparsers = parser.add_subparsers(dest="subcommand")

    p_list = subparsers.add_parser("list", help="Lista módulos e arquivos traduzíveis")
    p_diff = subparsers.add_parser("diff", help="Exibe diff entre vanilla rAthena e Cronus")
    p_diff.add_argument("module", choices=list(MODULES.keys()))
    p_diff.add_argument("--file", help="Arquivo específico")

    p_apply = subparsers.add_parser("apply", help="Aplica tradução de um módulo")
    p_apply.add_argument("module", choices=list(MODULES.keys()) + ["all"])
    p_apply.add_argument("--file", help="Arquivo específico")
    p_apply.add_argument("--test", action="store_true", help="Testa no rAthena após aplicar")

    p_restore = subparsers.add_parser("restore", help="Restaura arquivos originais")
    p_restore.add_argument("module", choices=list(MODULES.keys()) + ["all"])
    p_restore.add_argument("--file", help="Arquivo específico")

    p_test = subparsers.add_parser("test", help="Testa scripts ativos no container com --run-once")

    args = parser.parse_args()
    if args.subcommand == "list":
        cmd_list(args)
    elif args.subcommand == "diff":
        cmd_diff(args)
    elif args.subcommand == "apply":
        cmd_apply(args)
    elif args.subcommand == "restore":
        cmd_restore(args)
    elif args.subcommand == "test":
        cmd_test(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

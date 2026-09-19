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

# Mapeamento de diretórios rAthena -> Cronus
MODULES = {
    "kafras": {
        "rathena_dir": "kafras",
        "cronus_dir": "kafras",
        "files": {
            "kafras.txt": "kafras.txt",
            "functions_kafras.txt": "functions_kafras.txt",
            "cool_event_corp.txt": "cool_event_corp.txt",
            "dts_warper.txt": "dts_warper.txt",
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
    for mod_name, mod in MODULES.items():
        print(f"\nMódulo: [{mod_name}] ({mod['rathena_dir']} <-> {mod['cronus_dir']})")
        for r_file, c_file in mod["files"].items():
            r_path = os.path.join(RATHENA_NPC, mod["rathena_dir"], r_file)
            c_path = os.path.join(CRONUS_NPC, mod["cronus_dir"], c_file)

            r_ok = os.path.isfile(r_path)
            c_ok = os.path.isfile(c_path)

            status = "[PRONTO]" if (r_ok and c_ok) else "[AUSENTE]"
            print(f"  {status} {r_file:25} <- cronus:{c_file}")


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

        r_path = os.path.join(RATHENA_NPC, mod["rathena_dir"], r_file)
        c_path = os.path.join(CRONUS_NPC, mod["cronus_dir"], c_file)

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

            r_path = os.path.join(RATHENA_NPC, mod["rathena_dir"], r_file)
            c_path = os.path.join(CRONUS_NPC, mod["cronus_dir"], c_file)

            if not os.path.isfile(c_path):
                print(f"[PULAR] Arquivo Cronus não encontrado: {c_path}")
                continue

            # Backup
            if os.path.isfile(r_path):
                bkp_sub = os.path.join(BACKUP_DIR, mod["rathena_dir"])
                os.makedirs(bkp_sub, exist_ok=True)
                shutil.copy2(r_path, os.path.join(bkp_sub, r_file + ".bak"))

            # Aplica tradução
            shutil.copy2(c_path, r_path)
            print(f"[OK] Aplicado: {mod['rathena_dir']}/{r_file} <- {c_file}")
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

            r_path = os.path.join(RATHENA_NPC, mod["rathena_dir"], r_file)
            bkp_path = os.path.join(BACKUP_DIR, mod["rathena_dir"], r_file + ".bak")

            if os.path.isfile(bkp_path):
                shutil.copy2(bkp_path, r_path)
                print(f"[RESTAURADO] {mod['rathena_dir']}/{r_file} (via backup)")
                restored_count += 1
            else:
                # Tenta fallback na data_base original
                db_path = os.path.join(ROOT, "data_base", "npc", mod["rathena_dir"], r_file)
                if os.path.isfile(db_path):
                    shutil.copy2(db_path, r_path)
                    print(f"[RESTAURADO] {mod['rathena_dir']}/{r_file} (via data_base original)")
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

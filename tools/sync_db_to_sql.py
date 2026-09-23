#!/usr/bin/env python3
"""
tools/sync_db_to_sql.py

Sincroniza os dados gerados/randomizados pelo pipeline em tools (item_db e mob_db)
diretamente para as tabelas SQL do MariaDB (item_db e mob_db).

Garante que:
1. O rAthena carregue todos os monstros, stats, drops e itens via SQL (use_sql_db: yes).
2. O Laravel (e testes unitários com Pest) possam consultar e validar todo o estado do mundo via SQL.
"""

import os
import sys
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_db_credentials():
    """Lê as credenciais do banco a partir do .env ou variáveis de ambiente."""
    env_file = os.path.join(ROOT, ".env")
    creds = {
        "host": os.environ.get("RATHENA_DB_HOST", "127.0.0.1"),
        "port": os.environ.get("RATHENA_DB_PORT", "3306"),
        "user": os.environ.get("MYSQL_USER", "ragnarok"),
        "password": os.environ.get("MYSQL_PASSWORD", "ragnarok"),
        "database": os.environ.get("MYSQL_DATABASE", "ragnarok"),
    }
    if os.path.isfile(env_file):
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k == "MYSQL_USER":
                    creds["user"] = v
                elif k == "MYSQL_PASSWORD":
                    creds["password"] = v
                elif k == "MYSQL_DATABASE":
                    creds["database"] = v
                elif k == "BIND_IP" and v != "0.0.0.0":
                    creds["host"] = v
    return creds


def escape_sql(val):
    if val is None:
        return "NULL"
    return "'" + str(val).replace("\\", "\\\\").replace("'", "''") + "'"


def parse_item_db_line(line):
    """
    Formato item_db.txt rAthena:
    ID,AegisName,Name,Type,Buy,Sell,Weight,ATK,DEF,Range,Slots,Job,Upper,Gender,Loc,wLV,eLV,Refine,View,{ Script },{ OnEquip_Script },{ OnUnequip_Script }
    """
    line = line.strip()
    if not line or line.startswith("//"):
        return None

    # Separar os blocos de scripts { ... } do início dos campos
    scripts = []
    # Encontrar { ... }
    clean_line = line
    pattern = re.compile(r'\{([^}]*)\}')
    matches = list(pattern.finditer(line))
    
    if matches:
        first_match_start = matches[0].start()
        header_part = line[:first_match_start].rstrip(',')
        parts = [p.strip() for p in header_part.split(',')]
        
        script = matches[0].group(1).strip() if len(matches) > 0 else ""
        equip_script = matches[1].group(1).strip() if len(matches) > 1 else ""
        unequip_script = matches[2].group(1).strip() if len(matches) > 2 else ""
    else:
        parts = [p.strip() for p in line.split(',')]
        script, equip_script, unequip_script = "", "", ""

    if len(parts) < 19:
        return None

    try:
        item_id = int(parts[0])
    except ValueError:
        return None

    name_english = parts[1]
    name_japanese = parts[2]
    
    def safe_int(idx, default=0):
        if idx < len(parts) and parts[idx] != "":
            try:
                return int(parts[idx])
            except ValueError:
                return default
        return default

    item_type = safe_int(3, 0)
    price_buy = safe_int(4, 0)
    price_sell = safe_int(5, 0)
    weight = safe_int(6, 0)
    attack = safe_int(7, 0)
    defence = safe_int(8, 0)
    item_range = safe_int(9, 0)
    slots = safe_int(10, 0)
    equip_jobs = safe_int(11, 0)
    equip_upper = safe_int(12, 0)
    equip_genders = safe_int(13, 0)
    equip_locations = safe_int(14, 0)
    weapon_level = safe_int(15, 0)
    equip_level = safe_int(16, 0)
    refineable = safe_int(17, 0)
    view = safe_int(18, 0)

    return {
        "id": item_id,
        "name_english": name_english,
        "name_japanese": name_japanese,
        "type": item_type,
        "price_buy": price_buy,
        "price_sell": price_sell,
        "weight": weight,
        "attack": attack,
        "defence": defence,
        "range": item_range,
        "slots": slots,
        "equip_jobs": equip_jobs,
        "equip_upper": equip_upper,
        "equip_genders": equip_genders,
        "equip_locations": equip_locations,
        "weapon_level": weapon_level,
        "equip_level": equip_level,
        "refineable": refineable,
        "view": view,
        "script": script,
        "equip_script": equip_script,
        "unequip_script": unequip_script,
    }


def parse_mob_db_line(line):
    """
    Formato mob_db.txt rAthena:
    ID,Sprite_Name,kName,iName,LV,HP,SP,EXP,JEXP,Range1,ATK1,ATK2,DEF,MDEF,STR,AGI,VIT,INT,DEX,LUK,Range2,Range3,Scale,Race,Element,Mode,Speed,ADelay,aMotion,dMotion,MEXP,MVP1id,MVP1per,MVP2id,MVP2per,MVP3id,MVP3per,Drop1id,Drop1per,Drop2id,Drop2per,Drop3id,Drop3per,Drop4id,Drop4per,Drop5id,Drop5per,Drop6id,Drop6per,Drop7id,Drop7per,Drop8id,Drop8per,Drop9id,Drop9per,DropCardid,DropCardper
    """
    line = line.strip()
    if not line or line.startswith("//"):
        return None

    parts = [p.strip() for p in line.split(',')]
    if len(parts) < 57:
        return None

    try:
        mob_id = int(parts[0])
    except ValueError:
        return None

    def safe_int(idx, default=0):
        if idx < len(parts) and parts[idx] != "":
            try:
                return int(parts[idx], 0)
            except ValueError:
                return default
        return default

    return {
        "ID": mob_id,
        "Sprite": parts[1],
        "kName": parts[2],
        "iName": parts[3],
        "LV": safe_int(4),
        "HP": safe_int(5),
        "SP": safe_int(6),
        "EXP": safe_int(7),
        "JEXP": safe_int(8),
        "Range1": safe_int(9),
        "ATK1": safe_int(10),
        "ATK2": safe_int(11),
        "DEF": safe_int(12),
        "MDEF": safe_int(13),
        "STR": safe_int(14),
        "AGI": safe_int(15),
        "VIT": safe_int(16),
        "INT": safe_int(17),
        "DEX": safe_int(18),
        "LUK": safe_int(19),
        "Range2": safe_int(20),
        "Range3": safe_int(21),
        "Scale": safe_int(22),
        "Race": safe_int(23),
        "Element": safe_int(24),
        "Mode": safe_int(25),
        "Speed": safe_int(26),
        "aDelay": safe_int(27),
        "aMotion": safe_int(28),
        "dMotion": safe_int(29),
        "MEXP": safe_int(30),
        "MVP1id": safe_int(31),
        "MVP1per": safe_int(32),
        "MVP2id": safe_int(33),
        "MVP2per": safe_int(34),
        "MVP3id": safe_int(35),
        "MVP3per": safe_int(36),
        "Drop1id": safe_int(37),
        "Drop1per": safe_int(38),
        "Drop2id": safe_int(39),
        "Drop2per": safe_int(40),
        "Drop3id": safe_int(41),
        "Drop3per": safe_int(42),
        "Drop4id": safe_int(43),
        "Drop4per": safe_int(44),
        "Drop5id": safe_int(45),
        "Drop5per": safe_int(46),
        "Drop6id": safe_int(47),
        "Drop6per": safe_int(48),
        "Drop7id": safe_int(49),
        "Drop7per": safe_int(50),
        "Drop8id": safe_int(51),
        "Drop8per": safe_int(52),
        "Drop9id": safe_int(53),
        "Drop9per": safe_int(54),
        "DropCardid": safe_int(55),
        "DropCardper": safe_int(56),
    }


def execute_sql_batch(creds, queries):
    """Executa consultas SQL via mysql client local ou docker exec."""
    full_sql = "SET FOREIGN_KEY_CHECKS=0;\n" + "\n".join(queries) + "\nSET FOREIGN_KEY_CHECKS=1;\n"
    
    # Tenta rodar via docker exec ragnarok-server se o client local não estiver disponível
    cmd = [
        "docker", "exec", "-i", "ragnarok-server",
        "mysql", "-h", "db", "-u", creds["user"], f"-p{creds['password']}", creds["database"]
    ]
    try:
        proc = subprocess.run(cmd, input=full_sql.encode('utf-8'), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Fallback: mysql local
    local_cmd = [
        "mysql", "-h", creds["host"], "-P", creds["port"], "-u", creds["user"], f"-p{creds['password']}", creds["database"]
    ]
    proc = subprocess.run(local_cmd, input=full_sql.encode('utf-8'), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return True


def sync_items(creds, item_file):
    if not os.path.isfile(item_file):
        print(f"[PULADO] Arquivo de itens não encontrado: {item_file}")
        return 0

    print(f"--> Carregando itens de: {item_file}")
    items = []
    with open(item_file, "r", encoding="latin-1", errors="ignore") as f:
        for line in f:
            item = parse_item_db_line(line)
            if item:
                items.append(item)

    print(f"    Total de itens parseados: {len(items)}")
    if not items:
        return 0

    # Construir queries em lotes de 500
    batch_size = 500
    batches = []
    current_batch = []

    for item in items:
        val_str = (
            f"({item['id']}, {escape_sql(item['name_english'])}, {escape_sql(item['name_japanese'])}, "
            f"{item['type']}, {item['price_buy']}, {item['price_sell']}, {item['weight']}, "
            f"{item['attack']}, {item['defence']}, {item['range']}, {item['slots']}, "
            f"{item['equip_jobs']}, {item['equip_upper']}, {item['equip_genders']}, {item['equip_locations']}, "
            f"{item['weapon_level']}, {item['equip_level']}, {item['refineable']}, {item['view']}, "
            f"{escape_sql(item['script'])}, {escape_sql(item['equip_script'])}, {escape_sql(item['unequip_script'])})"
        )
        current_batch.append(val_str)
        if len(current_batch) >= batch_size:
            sql = (
                "REPLACE INTO `item_db` (`id`,`name_english`,`name_japanese`,`type`,`price_buy`,`price_sell`,`weight`,`attack`,`defence`,`range`,`slots`,`equip_jobs`,`equip_upper`,`equip_genders`,`equip_locations`,`weapon_level`,`equip_level`,`refineable`,`view`,`script`,`equip_script`,`unequip_script`) VALUES\n"
                + ",\n".join(current_batch) + ";"
            )
            batches.append(sql)
            current_batch = []

    if current_batch:
        sql = (
            "REPLACE INTO `item_db` (`id`,`name_english`,`name_japanese`,`type`,`price_buy`,`price_sell`,`weight`,`attack`,`defence`,`range`,`slots`,`equip_jobs`,`equip_upper`,`equip_genders`,`equip_locations`,`weapon_level`,`equip_level`,`refineable`,`view`,`script`,`equip_script`,`unequip_script`) VALUES\n"
            + ",\n".join(current_batch) + ";"
        )
        batches.append(sql)

    print(f"    Sincronizando {len(batches)} lotes no banco MariaDB...")
    execute_sql_batch(creds, batches)
    print(f"  ✓ {len(items)} itens sincronizados com sucesso na tabela item_db!")
    return len(items)


def sync_mobs(creds, mob_file):
    if not os.path.isfile(mob_file):
        print(f"[PULADO] Arquivo de monstros não encontrado: {mob_file}")
        return 0

    print(f"--> Carregando monstros de: {mob_file}")
    mobs = []
    with open(mob_file, "r", encoding="latin-1", errors="ignore") as f:
        for line in f:
            mob = parse_mob_db_line(line)
            if mob:
                mobs.append(mob)

    print(f"    Total de monstros parseados: {len(mobs)}")
    if not mobs:
        return 0

    columns = [
        "ID", "Sprite", "kName", "iName", "LV", "HP", "SP", "EXP", "JEXP", "Range1", "ATK1", "ATK2",
        "DEF", "MDEF", "STR", "AGI", "VIT", "INT", "DEX", "LUK", "Range2", "Range3", "Scale", "Race",
        "Element", "Mode", "Speed", "aDelay", "aMotion", "dMotion", "MEXP",
        "MVP1id", "MVP1per", "MVP2id", "MVP2per", "MVP3id", "MVP3per",
        "Drop1id", "Drop1per", "Drop2id", "Drop2per", "Drop3id", "Drop3per",
        "Drop4id", "Drop4per", "Drop5id", "Drop5per", "Drop6id", "Drop6per",
        "Drop7id", "Drop7per", "Drop8id", "Drop8per", "Drop9id", "Drop9per",
        "DropCardid", "DropCardper"
    ]
    col_str = "`,`".join(columns)

    batch_size = 200
    batches = []
    current_batch = []

    for mob in mobs:
        vals = []
        for col in columns:
            v = mob[col]
            if isinstance(v, str):
                vals.append(escape_sql(v))
            else:
                vals.append(str(v))
        current_batch.append("(" + ",".join(vals) + ")")

        if len(current_batch) >= batch_size:
            sql = f"REPLACE INTO `mob_db` (`{col_str}`) VALUES\n" + ",\n".join(current_batch) + ";"
            batches.append(sql)
            current_batch = []

    if current_batch:
        sql = f"REPLACE INTO `mob_db` (`{col_str}`) VALUES\n" + ",\n".join(current_batch) + ";"
        batches.append(sql)

    print(f"    Sincronizando {len(batches)} lotes de monstros no banco MariaDB...")
    execute_sql_batch(creds, batches)
    print(f"  ✓ {len(mobs)} monstros sincronizados com sucesso na tabela mob_db!")
    return len(mobs)


def main():
    print("=== Sincronizador de Mundo Procedural para Banco de Dados SQL (item_db / mob_db) ===")
    creds = get_db_credentials()

    item_candidates = [
        os.path.join(ROOT, "data/db/pre-re/item_db.txt"),
        os.path.join(ROOT, "data_base/db/pre-re/item_db.txt"),
    ]
    mob_candidates = [
        os.path.join(ROOT, "data/db/pre-re/mob_db.txt"),
        os.path.join(ROOT, "data_base/db/pre-re/mob_db.txt"),
    ]

    item_file = next((f for f in item_candidates if os.path.isfile(f)), None)
    mob_file = next((f for f in mob_candidates if os.path.isfile(f)), None)

    if not item_file or not mob_file:
        print("[ERRO] Arquivos item_db.txt ou mob_db.txt não localizados.")
        sys.exit(1)

    sync_items(creds, item_file)
    sync_mobs(creds, mob_file)
    print("=== Sincronização SQL Concluída com Sucesso! ===")


if __name__ == "__main__":
    main()

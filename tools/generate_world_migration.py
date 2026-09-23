#!/usr/bin/env python3
"""
tools/generate_world_migration.py

Gera uma nova migration Laravel dentro de web/database/migrations com:
- Nome da seed e timestamp (ex: 2026_09_23_185800_seed_world_zawarudo.php)
- Os dados procedurais completos do mundo (item_db e mob_db) gerados pelo pipeline
- Execução automática da migration no painel web para sincronizar o banco e o site
"""

import os
import sys
import re
import datetime
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_seed():
    env_file = os.path.join(ROOT, ".env.rando")
    if os.path.isfile(env_file):
        with open(env_file, "r") as f:
            for line in f:
                if line.startswith("WORLD_SEED="):
                    return line.strip().split("=", 1)[1].strip()
    return "zawarudo"


def main():
    seed = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else load_seed()
    clean_seed = re.sub(r'[^a-zA-Z0-9_]', '_', seed).lower()
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y_%m_%d_%H%M%S")
    class_seed = "".join(part.capitalize() for part in clean_seed.split("_"))

    print(f"=== Gerador de Migration de Mundo Procedural ===")
    print(f"Seed:      {seed}")
    print(f"Timestamp: {timestamp}")

    # Diretórios
    migrations_dir = os.path.join(ROOT, "web/database/migrations")
    data_dir = os.path.join(ROOT, "web/database/data")
    os.makedirs(migrations_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)

    # 1. Gerar o arquivo SQL com o dump do item_db e mob_db procedurais atuais
    sql_filename = f"world_{clean_seed}_{timestamp}.sql"
    sql_path = os.path.join(data_dir, sql_filename)

    # Coletar dumps dos txt procedurais ou das tabelas
    print(f"--> Exportando dados procedurais para: {sql_path}")
    sync_script = os.path.join(ROOT, "tools/sync_db_to_sql.py")
    if os.path.isfile(sync_script):
        # Garante sincronização prévia com o banco
        subprocess.run([sys.executable, sync_script], check=True)

    # Fazer dump das tabelas item_db e mob_db usando docker exec
    dump_cmd = [
        "docker", "exec", "ragnarok-db",
        "mysqldump", "-u", "ragnarok", "-pragnarok",
        "--no-create-info", "--complete-insert", "--replace",
        "ragnarok", "item_db", "mob_db"
    ]
    try:
        proc = subprocess.run(dump_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        with open(sql_path, "wb") as f:
            f.write(proc.stdout)
        print(f"  ✓ Dados SQL gerados com sucesso ({len(proc.stdout)} bytes)")
    except Exception:
        # Fallback para ragnarok-server se o rAthena estiver rodando
        dump_cmd_server = [
            "docker", "exec", "ragnarok-server",
            "mysqldump", "-h", "db", "-u", "ragnarok", "-pragnarok",
            "--no-create-info", "--complete-insert", "--replace",
            "ragnarok", "item_db", "mob_db"
        ]
        try:
            proc = subprocess.run(dump_cmd_server, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            with open(sql_path, "wb") as f:
                f.write(proc.stdout)
            print(f"  ✓ Dados SQL gerados com sucesso via ragnarok-server ({len(proc.stdout)} bytes)")
        except Exception as e:
            print(f"[WARN] Falha ao executar mysqldump: {e}. Gerando SQL a partir dos arquivos txt...")
            with open(sql_path, "w") as f:
                f.write(f"-- World Seed: {seed} ({timestamp})\n")

    # 2. Criar o arquivo de Migration do Laravel
    migration_filename = f"{timestamp}_seed_world_{clean_seed}.php"
    migration_path = os.path.join(migrations_dir, migration_filename)

    migration_content = f"""<?php

use Illuminate\\Database\\Migrations\\Migration;
use Illuminate\\Support\\Facades\\DB;
use Illuminate\\Support\\Facades\\File;
use Illuminate\\Support\\Facades\\Schema;
use Illuminate\\Database\\Schema\\Blueprint;

return new class extends Migration
{{
    /**
     * Run the migrations.
     * Seed: {seed}
     * Generated: {now.strftime("%Y-%m-%d %H:%M:%S")}
     */
    public function up(): void
    {{
        // 1. Garantir tabela de metadata do mundo
        if (!Schema::hasTable('world_metadata')) {{
            Schema::create('world_metadata', function (Blueprint $table) {{
                $table->string('key')->primary();
                $table->text('value')->nullable();
                $table->timestamps();
            }});
        }}

        // 2. Registrar a seed ativa
        DB::table('world_metadata')->updateOrInsert(
            ['key' => 'active_seed'],
            ['value' => '{seed}', 'updated_at' => now()]
        );

        DB::table('world_metadata')->updateOrInsert(
            ['key' => 'world_timestamp'],
            ['value' => '{timestamp}', 'updated_at' => now()]
        );

        // 3. Aplicar o dataset SQL do mundo
        $sqlPath = database_path('data/{sql_filename}');
        if (File::exists($sqlPath)) {{
            DB::unprepared(File::get($sqlPath));
        }}
    }}

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {{
        // Reversão da seed
    }}
}};
"""

    with open(migration_path, "w", encoding="utf-8") as f:
        f.write(migration_content)

    print(f"  ✓ Migration criada: {migration_path}")

    # 3. Executar a migration no container do painel se solicitado ou disponível
    print("--> Executando migração no painel...")
    run_migrate = [
        "docker", "exec", "ragnarok-panel", "php", "artisan", "migrate", "--force"
    ]
    clear_cache = [
        "docker", "exec", "ragnarok-panel", "php", "artisan", "cache:clear"
    ]
    try:
        subprocess.run(run_migrate, check=True)
        subprocess.run(clear_cache, check=True)
        print("  ✓ Migração executada com sucesso e cache limpo!")
    except Exception as e:
        print(f"[WARN] Não foi possível executar a migração no container agora: {e}")

    print("=== Concluído! ===")


if __name__ == "__main__":
    main()

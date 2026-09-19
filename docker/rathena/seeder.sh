#!/bin/bash
# =============================================================================
# RAGNAROGUE – Seeder de Contas de Teste
# Cria contas teste_* com personagens prontos para QA de cada classe:
#   - 1ª Classe: teste_swordie, teste_mage, teste_archer, teste_acolyte, teste_merchant, teste_thief
#   - 2ª Classe + Transclasse correspondente em cada conta:
#       teste_knight     -> Knight + Lord Knight
#       teste_wizard     -> Wizard + High Wizard
#       teste_priest     -> Priest + High Priest
#       teste_blacksmith -> Blacksmith + Whitesmith
#       teste_hunter     -> Hunter + Sniper
#       teste_assassin   -> Assassin + Assassin Cross
#   - Classes Expandidas:
#       teste_extended   -> Gunslinger + Soul Linker + Star Gladiator + Super Novice
# Configurados com:
#   - Level 99 Base / 50 Job (70 Job para Transclasses, 99 Job para Super Novice)
#   - Atributos com builds clássicas e realistas de Pre-Renewal
#   - Allskills habilitadas (no groups.conf e na tabela skill)
#   - Inventário enxuto e leve (<25% do peso máximo)
# Uso: bash seeder.sh [--reset]   (--reset apaga e recria os personagens)
# =============================================================================
set -e

DB_HOST="${RATHENA_DB_HOST:-db}"
DB_PORT="${RATHENA_DB_PORT:-3306}"
DB_USER="${MYSQL_USER:-ragnarok}"
DB_PASS="${MYSQL_PASSWORD:-ragnarok}"
DB_NAME="${MYSQL_DATABASE:-ragnarok}"

RESET=0
if [ "$1" = "--reset" ]; then
    RESET=1
fi

SQL() { mysql -h "$DB_HOST" -P "$DB_PORT" -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" -e "$1" 2>/dev/null; }
SQLR() { mysql -h "$DB_HOST" -P "$DB_PORT" -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" -sNe "$1" 2>/dev/null; }

echo "=== RAGNAROGUE – Seeder de contas de teste (1ª, 2ª, Trans e Expandidas) ==="
echo "DB: ${DB_HOST}:${DB_PORT}/${DB_NAME}"

# Aguardar DB
until mysqladmin ping -h "$DB_HOST" -P "$DB_PORT" -u"$DB_USER" -p"$DB_PASS" --silent 2>/dev/null; do
    echo "Aguardando MariaDB..."
    sleep 2
done

# ─────────────────────────────────────────────────────────────────────────────
# 1. Garantir que a coluna settings tem DEFAULT vazio
# ─────────────────────────────────────────────────────────────────────────────
SQL "ALTER TABLE \`char\` MODIFY \`settings\` text NOT NULL DEFAULT '';" 2>/dev/null || true
if [ "$RESET" -eq 1 ]; then
    SQL "DELETE FROM \`inventory\` WHERE char_id = 0;" 2>/dev/null || true
    SQL "DELETE FROM \`skill\` WHERE char_id = 0;" 2>/dev/null || true
fi

# Localizar skill_tree.txt
SKILL_TREE=""
for path in "/opt/rathena/db/pre-re/skill_tree.txt" "./data/db/pre-re/skill_tree.txt" "/home/luiz/Projetos/ragnarok-docker/data/db/pre-re/skill_tree.txt"; do
    if [ -f "$path" ]; then
        SKILL_TREE="$path"
        break
    fi
done

# ─────────────────────────────────────────────────────────────────────────────
# 2. Definições de Contas
#    Formato: "account_id|userid|password"
# ─────────────────────────────────────────────────────────────────────────────
declare -A ACCOUNTS=(
    ["teste_swordie"]="2000010|teste_swordie|teste123"
    ["teste_mage"]="2000011|teste_mage|teste123"
    ["teste_archer"]="2000012|teste_archer|teste123"
    ["teste_acolyte"]="2000013|teste_acolyte|teste123"
    ["teste_merchant"]="2000014|teste_merchant|teste123"
    ["teste_thief"]="2000015|teste_thief|teste123"
    ["teste_knight"]="2000016|teste_knight|teste123"
    ["teste_wizard"]="2000017|teste_wizard|teste123"
    ["teste_priest"]="2000018|teste_priest|teste123"
    ["teste_blacksmith"]="2000019|teste_blacksmith|teste123"
    ["teste_hunter"]="2000020|teste_hunter|teste123"
    ["teste_assassin"]="2000021|teste_assassin|teste123"
    ["teste_extended"]="2000022|teste_extended|teste123"
)

# ─────────────────────────────────────────────────────────────────────────────
# 3. Definições de Personagens
#    Formato: "account_id|char_num|char_name|class_id|base_level|job_level|start_map|sx|sy"
# ─────────────────────────────────────────────────────────────────────────────
CHARACTERS=(
    # 1ª Classes
    "2000010|0|Swordie Test|1|99|50|prontera|155|185"
    "2000011|0|Mage Test|2|99|50|prontera|155|185"
    "2000012|0|Archer Test|3|99|50|prontera|155|185"
    "2000013|0|Acolyte Test|4|99|50|prontera|155|185"
    "2000014|0|Merchant Test|5|99|50|prontera|155|185"
    "2000015|0|Thief Test|6|99|50|prontera|155|185"

    # 2ª Classes + Transclasses
    "2000016|0|Knight Test|7|99|50|prontera|155|185"
    "2000016|1|Lord Knight Test|4008|99|70|prontera|155|185"

    "2000017|0|Wizard Test|9|99|50|prontera|155|185"
    "2000017|1|High Wizard Test|4010|99|70|prontera|155|185"

    "2000018|0|Priest Test|8|99|50|prontera|155|185"
    "2000018|1|High Priest Test|4009|99|70|prontera|155|185"

    "2000019|0|Blacksmith Test|10|99|50|prontera|155|185"
    "2000019|1|Whitesmith Test|4011|99|70|prontera|155|185"

    "2000020|0|Hunter Test|11|99|50|prontera|155|185"
    "2000020|1|Sniper Test|4012|99|70|prontera|155|185"

    "2000021|0|Assassin Test|12|99|50|prontera|155|185"
    "2000021|1|Assassin Cross Test|4013|99|70|prontera|155|185"

    # Classes Expandidas (teste_extended)
    "2000022|0|Gunslinger Test|24|99|50|prontera|155|185"
    "2000022|1|Soul Linker Test|4049|99|50|prontera|155|185"
    "2000022|2|Star Glad Test|4047|99|50|prontera|155|185"
    "2000022|3|SuperNovice Test|23|99|99|prontera|155|185"
)

# ─────────────────────────────────────────────────────────────────────────────
# 4. Criar/atualizar contas no login
# ─────────────────────────────────────────────────────────────────────────────
for key in "${!ACCOUNTS[@]}"; do
    IFS='|' read -r acct_id userid password <<< "${ACCOUNTS[$key]}"

    SQL "
    INSERT INTO \`login\` (\`account_id\`, \`userid\`, \`user_pass\`, \`sex\`, \`email\`, \`group_id\`, \`birthdate\`, \`character_slots\`)
    VALUES ($acct_id, '$userid', '$password', 'M', '${userid}@test.local', 6, '2000-01-01', 9)
    ON DUPLICATE KEY UPDATE
        \`user_pass\` = '$password',
        \`group_id\`  = 6,
        \`character_slots\` = 9;
    "

    # Se --reset, remover personagens, inventário e skills existentes desta conta
    if [ "$RESET" -eq 1 ]; then
        EXISTING_IDS=$(SQLR "SELECT char_id FROM \`char\` WHERE account_id = $acct_id;")
        for cid in $EXISTING_IDS; do
            SQL "DELETE FROM \`inventory\`       WHERE char_id = $cid;" 2>/dev/null || true
            SQL "DELETE FROM \`skill\`           WHERE char_id = $cid;" 2>/dev/null || true
            SQL "DELETE FROM \`memo\`            WHERE char_id = $cid;" 2>/dev/null || true
            SQL "DELETE FROM \`event_speedruns\` WHERE char_id = $cid;" 2>/dev/null || true
            SQL "DELETE FROM \`event_mvp_kills\` WHERE char_id = $cid;" 2>/dev/null || true
        done
        SQL "DELETE FROM \`char\` WHERE account_id = $acct_id;" 2>/dev/null || true
    fi
done

# Limpeza global de telemetria para contas de teste e caracteres com '%Test%'
SQL "DELETE FROM \`event_speedruns\` WHERE char_id IN (SELECT char_id FROM \`char\` WHERE account_id >= 2000010) OR name LIKE '%Test%';" 2>/dev/null || true
SQL "DELETE FROM \`event_mvp_kills\` WHERE char_id IN (SELECT char_id FROM \`char\` WHERE account_id >= 2000010) OR char_name LIKE '%Test%';" 2>/dev/null || true

# ─────────────────────────────────────────────────────────────────────────────
# 5. Criar personagens e inventário
# ─────────────────────────────────────────────────────────────────────────────
for char_def in "${CHARACTERS[@]}"; do
    IFS='|' read -r acct_id char_num char_name class_id base_lvl job_lvl start_map sx sy <<< "$char_def"

    echo ""
    echo "→ Provisionando: $char_name (account_id=$acct_id, slot=$char_num, class=$class_id, Lv.$base_lvl/$job_lvl)"

    CHAR_EXISTS=$(SQLR "SELECT COUNT(*) FROM \`char\` WHERE account_id = $acct_id AND char_num = $char_num;")
    if [ "$CHAR_EXISTS" -gt 0 ]; then
        echo "  [ok] Personagem já existe no slot $char_num."
        CHAR_ID=$(SQLR "SELECT char_id FROM \`char\` WHERE account_id = $acct_id AND char_num = $char_num LIMIT 1;")
    else
        # Builds clássicas e realistas de Pre-Renewal
        case $class_id in
            1)    # Swordman: Agi/Str 1H
                STR=82; AGI=65; VIT=45; INT=1;  DEX=45; LUK=1;  MAXHP=8500;  MAXSP=300 ;;
            2)    # Mage: Int/Dex Bolt/Firewall
                STR=1;  AGI=9;  VIT=30; INT=95; DEX=75; LUK=1;  MAXHP=3200;  MAXSP=1100 ;;
            3)    # Archer: Agi/Dex DS
                STR=1;  AGI=80; VIT=25; INT=15; DEX=90; LUK=25; MAXHP=4500;  MAXSP=500 ;;
            4)    # Acolyte: Support Int/Vit/Dex
                STR=1;  AGI=20; VIT=50; INT=85; DEX=60; LUK=1;  MAXHP=5200;  MAXSP=1150 ;;
            5)    # Merchant: Battle Str/Agi/Vit
                STR=82; AGI=65; VIT=45; INT=1;  DEX=45; LUK=1;  MAXHP=6800;  MAXSP=350 ;;
            6)    # Thief: Agi/Str Dagger
                STR=70; AGI=85; VIT=30; INT=1;  DEX=42; LUK=15; MAXHP=5500;  MAXSP=300 ;;
            7)    # Knight: 2H Agi/Str Quicken
                STR=85; AGI=75; VIT=50; INT=1;  DEX=45; LUK=9;  MAXHP=12000; MAXSP=450 ;;
            4008) # Lord Knight: Spiral/Frenzy/BB
                STR=88; AGI=70; VIT=60; INT=1;  DEX=45; LUK=1;  MAXHP=16500; MAXSP=550 ;;
            8)    # Priest: Full Support Vit/Int/Dex
                STR=1;  AGI=9;  VIT=60; INT=92; DEX=70; LUK=9;  MAXHP=7500;  MAXSP=1650 ;;
            4009) # High Priest: FS / Meditatio
                STR=1;  AGI=9;  VIT=65; INT=95; DEX=75; LUK=9;  MAXHP=9500;  MAXSP=2100 ;;
            9)    # Wizard: High Int/Dex Caster
                STR=1;  AGI=9;  VIT=35; INT=99; DEX=85; LUK=9;  MAXHP=4200;  MAXSP=1500 ;;
            4010) # High Wizard: AMP / Storm Gust
                STR=1;  AGI=9;  VIT=40; INT=99; DEX=90; LUK=9;  MAXHP=5500;  MAXSP=1900 ;;
            10)   # Blacksmith: Battle Smith Str/Agi/Dex
                STR=85; AGI=75; VIT=45; INT=1;  DEX=45; LUK=2;  MAXHP=9000;  MAXSP=480 ;;
            4011) # Whitesmith: Cart Boost / Meltdown
                STR=90; AGI=75; VIT=50; INT=1;  DEX=45; LUK=2;  MAXHP=12000; MAXSP=600 ;;
            11)   # Hunter: Agi/Dex Falcon / DS
                STR=9;  AGI=85; VIT=30; INT=20; DEX=90; LUK=35; MAXHP=6000;  MAXSP=650 ;;
            4012) # Sniper: True Sight / Sharp Shooting
                STR=9;  AGI=90; VIT=30; INT=20; DEX=95; LUK=40; MAXHP=7800;  MAXSP=850 ;;
            12)   # Assassin: Crit/Katar Agi/Str/Luk
                STR=78; AGI=85; VIT=35; INT=1;  DEX=40; LUK=42; MAXHP=7800;  MAXSP=420 ;;
            4013) # Assassin Cross: EDP / SinX Crit
                STR=85; AGI=85; VIT=40; INT=1;  DEX=40; LUK=42; MAXHP=10500; MAXSP=550 ;;
            24)   # Gunslinger: Desperado Agi/Dex
                STR=1;  AGI=85; VIT=40; INT=15; DEX=92; LUK=10; MAXHP=6500;  MAXSP=600 ;;
            4049) # Soul Linker: Esma / Support Int/Dex
                STR=1;  AGI=9;  VIT=55; INT=95; DEX=75; LUK=1;  MAXHP=7500;  MAXSP=1500 ;;
            4047) # Star Gladiator: Kick / Solar Str/Agi/Dex
                STR=85; AGI=80; VIT=45; INT=1;  DEX=50; LUK=1;  MAXHP=9000;  MAXSP=500 ;;
            23)   # Super Novice: Hybrid Melee/Caster
                STR=60; AGI=80; VIT=30; INT=50; DEX=60; LUK=10; MAXHP=4000;  MAXSP=700 ;;
            *)
                STR=50; AGI=50; VIT=50; INT=50; DEX=50; LUK=50; MAXHP=5000;  MAXSP=500 ;;
        esac

        SQL "
        INSERT INTO \`char\`
            (\`account_id\`, \`char_num\`, \`name\`, \`class\`,
             \`base_level\`, \`job_level\`, \`zeny\`,
             \`str\`, \`agi\`, \`vit\`, \`int\`, \`dex\`, \`luk\`,
             \`max_hp\`, \`hp\`, \`max_sp\`, \`sp\`,
             \`status_point\`, \`skill_point\`,
             \`hair\`, \`hair_color\`,
             \`last_map\`, \`last_x\`, \`last_y\`,
             \`save_map\`, \`save_x\`, \`save_y\`,
             \`sex\`, \`settings\`)
        VALUES
            ($acct_id, $char_num, '$char_name', $class_id,
             $base_lvl, $job_lvl, 50000,
             $STR, $AGI, $VIT, $INT, $DEX, $LUK,
             $MAXHP, $MAXHP, $MAXSP, $MAXSP,
             15, 0,
             1, 4,
             '$start_map', $sx, $sy,
             '$start_map', $sx, $sy,
             'M', '');
        "
        CHAR_ID=$(SQLR "SELECT char_id FROM \`char\` WHERE account_id = $acct_id AND char_num = $char_num LIMIT 1;")
        echo "  [criado] char_id=$CHAR_ID ($char_name) - Lv.$base_lvl/$job_lvl"
    fi

    # Inserir todas as habilidades da classe na tabela `skill`
    if [ -n "$SKILL_TREE" ] && [ -f "$SKILL_TREE" ]; then
        SKILL_SQL=$(awk -F'[,/]' -v j="$class_id" -v cid="$CHAR_ID" '
            $1 == j && $2 > 0 {
                if (vals != "") vals = vals ", ";
                vals = vals sprintf("(%d,%d,%d,0)", cid, $2, $3)
            }
            END {
                if (vals != "")
                    print "INSERT INTO `skill` (`char_id`,`id`,`lv`,`flag`) VALUES " vals " ON DUPLICATE KEY UPDATE `lv`=VALUES(`lv`);"
            }' "$SKILL_TREE")
        if [ -n "$SKILL_SQL" ]; then
            SQL "$SKILL_SQL"
            echo "  [skills] Habilidades de classe desbloqueadas no nível máximo."
        fi
    fi

    # Inventário leve (< 25% de peso para não sobrecarregar HP/SP)
    INV_COUNT=$(SQLR "SELECT COUNT(*) FROM \`inventory\` WHERE char_id = $CHAR_ID;")
    if [ "$INV_COUNT" -eq 0 ]; then
        echo "  [inventário] Adicionando consumíveis e equipamentos leves..."

        # Consumíveis comuns
        declare -A COMMON_ITEMS=(
            ["501"]="30"     # Poção Vermelha
            ["505"]="15"     # Poção Azul
            ["601"]="20"     # Asa de Mosca
            ["602"]="5"      # Asa de Borboleta
            ["611"]="5"      # Lupa
            ["12103"]="5"    # Emblema Oficial
        )

        for item_id in "${!COMMON_ITEMS[@]}"; do
            amount=${COMMON_ITEMS[$item_id]}
            SQL "
            INSERT INTO \`inventory\` (\`char_id\`, \`nameid\`, \`amount\`, \`equip\`, \`identify\`, \`refine\`, \`card0\`, \`card1\`, \`card2\`, \`card3\`)
            VALUES ($CHAR_ID, $item_id, $amount, 0, 1, 0, 0, 0, 0, 0)
            ON DUPLICATE KEY UPDATE \`amount\` = $amount;
            " 2>/dev/null || true
        done

        # Equipamentos por classe
        case $class_id in
            1)    # Swordman: Falchion, Buckler, Chain Mail, Shoes, Muffler
                for eq in "1102,1,2,0" "2102,1,32,0" "2315,1,16,0" "2401,1,64,0" "2502,1,4,0"; do
                    IFS=',' read -r eid eamt eequip eref <<< "$eq"
                    SQL "INSERT INTO \`inventory\` (\`char_id\`,\`nameid\`,\`amount\`,\`equip\`,\`identify\`,\`refine\`) VALUES ($CHAR_ID,$eid,$eamt,$eequip,1,$eref) ON DUPLICATE KEY UPDATE \`amount\`=$eamt;" 2>/dev/null || true
                done
                ;;
            7)    # Knight: Two-Handed Sword, Chain Mail, Shoes, Muffler
                for eq in "1113,1,34,0" "2315,1,16,0" "2401,1,64,0" "2502,1,4,0"; do
                    IFS=',' read -r eid eamt eequip eref <<< "$eq"
                    SQL "INSERT INTO \`inventory\` (\`char_id\`,\`nameid\`,\`amount\`,\`equip\`,\`identify\`,\`refine\`) VALUES ($CHAR_ID,$eid,$eamt,$eequip,1,$eref) ON DUPLICATE KEY UPDATE \`amount\`=$eamt;" 2>/dev/null || true
                done
                ;;
            4008) # Lord Knight: Claymore, Legion Plate, Shoes, Muffler
                for eq in "1162,1,34,0" "2341,1,16,0" "2401,1,64,0" "2502,1,4,0"; do
                    IFS=',' read -r eid eamt eequip eref <<< "$eq"
                    SQL "INSERT INTO \`inventory\` (\`char_id\`,\`nameid\`,\`amount\`,\`equip\`,\`identify\`,\`refine\`) VALUES ($CHAR_ID,$eid,$eamt,$eequip,1,$eref) ON DUPLICATE KEY UPDATE \`amount\`=$eamt;" 2>/dev/null || true
                done
                ;;
            2)    # Mage: Wand, Guard, Silk Robe, Shoes, Muffler
                for eq in "1605,1,2,0" "2101,1,32,0" "2320,1,16,0" "2401,1,64,0" "2502,1,4,0"; do
                    IFS=',' read -r eid eamt eequip eref <<< "$eq"
                    SQL "INSERT INTO \`inventory\` (\`char_id\`,\`nameid\`,\`amount\`,\`equip\`,\`identify\`,\`refine\`) VALUES ($CHAR_ID,$eid,$eamt,$eequip,1,$eref) ON DUPLICATE KEY UPDATE \`amount\`=$eamt;" 2>/dev/null || true
                done
                ;;
            9|4010) # Wizard / High Wizard: Arc Wand, Guard, Silk Robe, Shoes, Muffler
                for eq in "1613,1,2,0" "2101,1,32,0" "2320,1,16,0" "2401,1,64,0" "2502,1,4,0"; do
                    IFS=',' read -r eid eamt eequip eref <<< "$eq"
                    SQL "INSERT INTO \`inventory\` (\`char_id\`,\`nameid\`,\`amount\`,\`equip\`,\`identify\`,\`refine\`) VALUES ($CHAR_ID,$eid,$eamt,$eequip,1,$eref) ON DUPLICATE KEY UPDATE \`amount\`=$eamt;" 2>/dev/null || true
                done
                ;;
            3)    # Archer: Composite Bow, 500 Flechas, Tights, Shoes, Muffler
                for eq in "1704,1,34,0" "1750,500,0,0" "2312,1,16,0" "2401,1,64,0" "2502,1,4,0"; do
                    IFS=',' read -r eid eamt eequip eref <<< "$eq"
                    SQL "INSERT INTO \`inventory\` (\`char_id\`,\`nameid\`,\`amount\`,\`equip\`,\`identify\`,\`refine\`) VALUES ($CHAR_ID,$eid,$eamt,$eequip,1,$eref) ON DUPLICATE KEY UPDATE \`amount\`=$eamt;" 2>/dev/null || true
                done
                ;;
            11|4012) # Hunter / Sniper: Hunter Bow, 500 Flechas, Tights, Shoes, Muffler
                for eq in "1716,1,34,0" "1750,500,0,0" "2312,1,16,0" "2401,1,64,0" "2502,1,4,0"; do
                    IFS=',' read -r eid eamt eequip eref <<< "$eq"
                    SQL "INSERT INTO \`inventory\` (\`char_id\`,\`nameid\`,\`amount\`,\`equip\`,\`identify\`,\`refine\`) VALUES ($CHAR_ID,$eid,$eamt,$eequip,1,$eref) ON DUPLICATE KEY UPDATE \`amount\`=$eamt;" 2>/dev/null || true
                done
                ;;
            4)    # Acolyte: Mace, Buckler, Saint's Robe, Shoes, Muffler
                for eq in "1502,1,2,0" "2102,1,32,0" "2307,1,16,0" "2401,1,64,0" "2502,1,4,0"; do
                    IFS=',' read -r eid eamt eequip eref <<< "$eq"
                    SQL "INSERT INTO \`inventory\` (\`char_id\`,\`nameid\`,\`amount\`,\`equip\`,\`identify\`,\`refine\`) VALUES ($CHAR_ID,$eid,$eamt,$eequip,1,$eref) ON DUPLICATE KEY UPDATE \`amount\`=$eamt;" 2>/dev/null || true
                done
                ;;
            8|4009) # Priest / High Priest: Chain, Buckler, Saint's Robe, Shoes, Muffler
                for eq in "1505,1,2,0" "2102,1,32,0" "2307,1,16,0" "2401,1,64,0" "2502,1,4,0"; do
                    IFS=',' read -r eid eamt eequip eref <<< "$eq"
                    SQL "INSERT INTO \`inventory\` (\`char_id\`,\`nameid\`,\`amount\`,\`equip\`,\`identify\`,\`refine\`) VALUES ($CHAR_ID,$eid,$eamt,$eequip,1,$eref) ON DUPLICATE KEY UPDATE \`amount\`=$eamt;" 2>/dev/null || true
                done
                ;;
            5)    # Merchant: Battle Axe, Buckler, Chain Mail, Shoes, Muffler
                for eq in "1302,1,2,0" "2102,1,32,0" "2315,1,16,0" "2401,1,64,0" "2502,1,4,0"; do
                    IFS=',' read -r eid eamt eequip eref <<< "$eq"
                    SQL "INSERT INTO \`inventory\` (\`char_id\`,\`nameid\`,\`amount\`,\`equip\`,\`identify\`,\`refine\`) VALUES ($CHAR_ID,$eid,$eamt,$eequip,1,$eref) ON DUPLICATE KEY UPDATE \`amount\`=$eamt;" 2>/dev/null || true
                done
                ;;
            10|4011) # Blacksmith / Whitesmith: Two-Handed Axe, Chain Mail, Shoes, Muffler
                for eq in "1305,1,34,0" "2315,1,16,0" "2401,1,64,0" "2502,1,4,0"; do
                    IFS=',' read -r eid eamt eequip eref <<< "$eq"
                    SQL "INSERT INTO \`inventory\` (\`char_id\`,\`nameid\`,\`amount\`,\`equip\`,\`identify\`,\`refine\`) VALUES ($CHAR_ID,$eid,$eamt,$eequip,1,$eref) ON DUPLICATE KEY UPDATE \`amount\`=$eamt;" 2>/dev/null || true
                done
                ;;
            6)    # Thief: Main Gauche, Guard, Tights, Shoes, Muffler
                for eq in "1207,1,2,0" "2101,1,32,0" "2312,1,16,0" "2401,1,64,0" "2502,1,4,0"; do
                    IFS=',' read -r eid eamt eequip eref <<< "$eq"
                    SQL "INSERT INTO \`inventory\` (\`char_id\`,\`nameid\`,\`amount\`,\`equip\`,\`identify\`,\`refine\`) VALUES ($CHAR_ID,$eid,$eamt,$eequip,1,$eref) ON DUPLICATE KEY UPDATE \`amount\`=$eamt;" 2>/dev/null || true
                done
                ;;
            12|4013) # Assassin / SinX: Jur, Damascus, Tights, Shoes, Muffler
                for eq in "1251,1,34,0" "1218,1,2,0" "2312,1,16,0" "2401,1,64,0" "2502,1,4,0"; do
                    IFS=',' read -r eid eamt eequip eref <<< "$eq"
                    SQL "INSERT INTO \`inventory\` (\`char_id\`,\`nameid\`,\`amount\`,\`equip\`,\`identify\`,\`refine\`) VALUES ($CHAR_ID,$eid,$eamt,$eequip,1,$eref) ON DUPLICATE KEY UPDATE \`amount\`=$eamt;" 2>/dev/null || true
                done
                ;;
            24)   # Gunslinger: Six Shooter, 500 Bullets, Tights, Shoes, Muffler
                for eq in "13100,1,34,0" "13200,500,0,0" "2312,1,16,0" "2401,1,64,0" "2502,1,4,0"; do
                    IFS=',' read -r eid eamt eequip eref <<< "$eq"
                    SQL "INSERT INTO \`inventory\` (\`char_id\`,\`nameid\`,\`amount\`,\`equip\`,\`identify\`,\`refine\`) VALUES ($CHAR_ID,$eid,$eamt,$eequip,1,$eref) ON DUPLICATE KEY UPDATE \`amount\`=$eamt;" 2>/dev/null || true
                done
                ;;
            4049) # Soul Linker: Wand, Guard, Silk Robe, Shoes, Muffler
                for eq in "1605,1,2,0" "2101,1,32,0" "2320,1,16,0" "2401,1,64,0" "2502,1,4,0"; do
                    IFS=',' read -r eid eamt eequip eref <<< "$eq"
                    SQL "INSERT INTO \`inventory\` (\`char_id\`,\`nameid\`,\`amount\`,\`equip\`,\`identify\`,\`refine\`) VALUES ($CHAR_ID,$eid,$eamt,$eequip,1,$eref) ON DUPLICATE KEY UPDATE \`amount\`=$eamt;" 2>/dev/null || true
                done
                ;;
            4047) # Star Gladiator: Book, Buckler, Chain Mail, Shoes, Muffler
                for eq in "1550,1,2,0" "2102,1,32,0" "2315,1,16,0" "2401,1,64,0" "2502,1,4,0"; do
                    IFS=',' read -r eid eamt eequip eref <<< "$eq"
                    SQL "INSERT INTO \`inventory\` (\`char_id\`,\`nameid\`,\`amount\`,\`equip\`,\`identify\`,\`refine\`) VALUES ($CHAR_ID,$eid,$eamt,$eequip,1,$eref) ON DUPLICATE KEY UPDATE \`amount\`=$eamt;" 2>/dev/null || true
                done
                ;;
            23)   # Super Novice: Main Gauche, Guard, Cotton Shirt, Shoes, Muffler
                for eq in "1207,1,2,0" "2101,1,32,0" "2301,1,16,0" "2401,1,64,0" "2502,1,4,0"; do
                    IFS=',' read -r eid eamt eequip eref <<< "$eq"
                    SQL "INSERT INTO \`inventory\` (\`char_id\`,\`nameid\`,\`amount\`,\`equip\`,\`identify\`,\`refine\`) VALUES ($CHAR_ID,$eid,$eamt,$eequip,1,$eref) ON DUPLICATE KEY UPDATE \`amount\`=$eamt;" 2>/dev/null || true
                done
                ;;
        esac

        echo "  [ok] Inventário leve populado com sucesso."
    else
        echo "  [ok] Inventário já existente ($INV_COUNT itens)."
    fi

done

echo ""
echo "=== Seeder concluído com sucesso! ==="
echo ""
echo "Contas e Personagens de teste configurados:"
echo "  ┌──────────────────────┬─────────────┬──────┬──────────────────────────────────┬─────────────┐"
echo "  │ Conta                │ Senha       │ Slot │ Personagem                       │ Classe      │"
echo "  ├──────────────────────┼─────────────┼──────┼──────────────────────────────────┼─────────────┤"
for char_def in "${CHARACTERS[@]}"; do
    IFS='|' read -r acct_id char_num char_name class_id base_lvl job_lvl _ _ _ <<< "$char_def"
    acct_name=""
    for k in "${!ACCOUNTS[@]}"; do
        if [[ "${ACCOUNTS[$k]}" == "${acct_id}|"* ]]; then
            acct_name="$k"
            break
        fi
    done
    printf "  │ %-20s │ %-11s │ %-4s │ %-32s │ Lv.%2d/%2d   │\n" "$acct_name" "teste123" "$char_num" "$char_name" "$base_lvl" "$job_lvl"
done
echo "  └──────────────────────┴─────────────┴──────┴──────────────────────────────────┴─────────────┘"
echo ""
echo "  Todas as contas têm Group 6 (Tester):"
echo "  - All Skills desbloqueadas e comando @allskill habilitado"
echo "  - Comandos: @go, @warp, @item, @zeny, @heal, @alive, @jobchange, @speed, @storage"
echo "  - Descontadas do placar de Speedrun/MVP (telemetria de torneio ignora contas de teste)"

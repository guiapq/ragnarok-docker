#!/bin/bash

DB="/opt/rathena/db/re/item_db.txt"
if [ ! -f "$DB" ]; then
    DB="/usr/bin/rathena/db/re/item_db.txt"
fi
if [ ! -f "$DB" ]; then
    DB="data/db/re/item_db.txt"
fi
IDS="2214|2501|2401|2829|2828"

echo "================================="
echo "RAGNAROK META ANALYZER"
echo "================================="

echo
echo ">>> Coletando scripts dos itens..."
echo "---------------------------------"

SCRIPTS=$(grep -E "^($IDS)," "$DB" | awk -F'{' '{print $2}' | awk -F'}' '{print $1}')

echo
echo ">>> Contando stats..."
echo "---------------------------------"

declare -A stats

for stat in bAtk bMatk bHit bCritical bFlee bDef bMdef bMaxHP bMaxSP bAspdRate; do
    COUNT=$(echo "$SCRIPTS" | grep -o "$stat" | wc -l)
    stats[$stat]=$COUNT
    printf "%-12s %s\n" "$stat" "$COUNT"
done

echo
echo ">>> Detectando tendências..."
echo "---------------------------------"

atk=${stats[bAtk]}
matk=${stats[bMatk]}
crit=${stats[bCritical]}
aspd=${stats[bAspdRate]}
hit=${stats[bHit]}
flee=${stats[bFlee]}
def=${stats[bDef]}
hp=${stats[bMaxHP]}

echo
echo "[META INTERPRETATION]"

# META PRINCIPAL
if (( crit + aspd > atk + matk )); then
    echo "⚡ Meta voltado para CRIT / ASPD"
elif (( atk > matk )); then
    echo "⚔️ Meta voltado para MELEE (ATK)"
elif (( matk > atk )); then
    echo "🔥 Meta voltado para MAGIC (MATK)"
fi

# SUPORTE
if (( hit > 3 )); then
    echo "🎯 Alta precisão favorecida"
fi

if (( flee > 3 )); then
    echo "💨 Builds evasivas viáveis"
fi

if (( def + hp > 5 )); then
    echo "🛡️ Tank está viável"
fi

echo
echo "[CLASSES SUGERIDAS]"

# SUGESTÕES
if (( crit + aspd > 4 )); then
    echo "👉 Assassin / Crit Knight / AGI builds"
fi

if (( atk > 4 )); then
    echo "👉 Knight / Blacksmith / Melee builds"
fi

if (( matk > 4 )); then
    echo "👉 Wizard / Sage"
fi

if (( flee > 4 )); then
    echo "👉 Rogue / Assassin (dodge)"
fi

if (( def + hp > 6 )); then
    echo "👉 Crusader / Tank builds"
fi

echo
echo "[CLASSES EM SOFRIMENTO]"

# CURSED DETECTION (porca mesmo)
if (( matk == 0 )); then
    echo "💀 Magic builds provavelmente ruins"
fi

if (( crit == 0 )); then
    echo "💀 Crit builds provavelmente ruins"
fi

if (( flee == 0 )); then
    echo "💀 Dodge builds inviáveis"
fi

if (( hit == 0 )); then
    echo "💀 Problemas sérios de precisão"
fi

echo
echo "================================="
echo "ANALYSIS COMPLETE"
echo "================================="

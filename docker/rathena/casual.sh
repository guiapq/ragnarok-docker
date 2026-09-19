#!/bin/bash

set -e

if [ -d "/opt/rathena" ]; then
    RATHENA="/opt/rathena"
else
    RATHENA="/usr/bin/rathena"
fi

APPLY_ONLY=0
if [ "$1" = "--apply-only" ] || [ "$1" = "--no-start" ]; then
    APPLY_ONLY=1
fi

if [ "$APPLY_ONLY" -eq 0 ]; then
    if pgrep -f map-server > /dev/null; then
        echo "rAthena está rodando, parando para aplicar configurações..."
        cd $RATHENA
        ./athena-start stop || true
    fi
fi

echo "=== Aplicando modo CASUAL ==="
echo "Rathena path: $RATHENA"

#################################
# 1 - EXP rates
#################################

sed -i 's/base_exp_rate:.*/base_exp_rate: 33000/' $RATHENA/conf/battle/exp.conf || true
sed -i 's/job_exp_rate:.*/job_exp_rate: 33000/' $RATHENA/conf/battle/exp.conf || true

#################################
# 2 - DROP rates (Pacing Roguelike v2)
#################################

# Como o randomize_drops.py já calibra as probabilidades por tier de monstro,
# usamos multiplicadores suaves para manter o ritmo sem lotar o chão de entulho:
sed -i 's/item_rate_common:.*/item_rate_common: 120/' $RATHENA/conf/battle/drops.conf || true
sed -i 's/item_rate_heal:.*/item_rate_heal: 100/' $RATHENA/conf/battle/drops.conf || true
sed -i 's/item_rate_equip:.*/item_rate_equip: 150/' $RATHENA/conf/battle/drops.conf || true
sed -i 's/item_rate_card:.*/item_rate_card: 200/' $RATHENA/conf/battle/drops.conf || true
sed -i 's/item_rate_common_boss:.*/item_rate_common_boss: 150/' $RATHENA/conf/battle/drops.conf || true
sed -i 's/item_rate_equip_boss:.*/item_rate_equip_boss: 200/' $RATHENA/conf/battle/drops.conf || true
sed -i 's/item_rate_card_boss:.*/item_rate_card_boss: 200/' $RATHENA/conf/battle/drops.conf || true

#################################
# 3 - Tolerância de Peso e Regeneração Natural Roguelike
#################################

echo "=== Ajustando tolerância de peso e regeneração ==="

# Permite regenerar HP/SP naturalmente até 85% de peso (zero travamento para o Aprendiz)
sed -i 's/natural_heal_weight_rate:.*/natural_heal_weight_rate: 85/' $RATHENA/conf/battle/player.conf || true
sed -i 's/natural_heal_weight_rate_renewal:.*/natural_heal_weight_rate_renewal: 85/' $RATHENA/conf/battle/player.conf || true
sed -i 's/max_cart_weight:.*/max_cart_weight: 10000/' $RATHENA/conf/battle/player.conf || true

#################################
# 4 - remover PIN
#################################

echo "=== Desativando sistema de PIN ==="

sed -i 's/pincode_enabled:.*/pincode_enabled: no/' $RATHENA/conf/char_athena.conf || true
sed -i 's/pincode_force:.*/pincode_force: no/' $RATHENA/conf/char_athena.conf || true

echo "PIN config atual:"
grep pincode $RATHENA/conf/char_athena.conf || true

#################################
# 5 - starter items (Leves, sem sobrepeso para o Aprendiz)
#################################

mkdir -p $RATHENA/npc/custom

cat <<EOF > $RATHENA/npc/custom/starter_items.txt
-	script	Starter_Items	-1,{

OnPCLoginEvent:
	if (#starter_items_given == 0) {
		getitem 611,500;   // Lupa (peso 0)
		dispbottom "Você recebeu 500 lupas iniciais (peso zero)!";
		getitem 501,100;   // Poção Vermelha (peso leve)
		getitem 504,30;    // Poção Branca (peso leve)
		getitem 505,20;    // Poção Azul (peso leve)
		getitem 601,60;    // Asa de Mosca (peso leve)
		getitem 602,15;    // Asa de Borboleta (peso leve)
		getitem 2607,2;    // Presilha [1] (Clip com bônus procedurais)
		getitem 2214,1;    // Laço de Cabelo
		getitem 2501,1;    // Capuz
		getitem 2401,1;    // Sandálias
		getitem 2102,1;    // Vantagem / Guard
		getitem 2306,1;    // Traje de Noviço / Adventurer's Suit
		getitem 1207,1;    // Faca / Main Gauche
		getitem 4002,2;    // Carta Fabre
		getitem 4003,1;    // Carta Pupa
		getitem 4012,2;    // Carta Ovo de Besouro-Ladrão
		getitem 969,3;     // Ouro (peso leve)
		getitem 603,3;     // Caixa Velha Azul (OBB)
		getitem 616,2;     // Álbum Velho de Cartas (OCA)

		#starter_items_given = 1;
		dispbottom "Você recebeu o Pacote Inicial Roguelike!";
	}
	end;
}
EOF

#################################
# 5 - ativar NPCs existentes
#################################

NPCCONF=$RATHENA/npc/scripts_custom.conf

echo "=== Ativando NPCs CASUAL ==="

enable_npc() {
    sed -i "s|//npc: npc/custom/$1|npc: npc/custom/$1|" "$NPCCONF" || true
}

enable_npc warper.txt
enable_npc healer.txt
enable_npc stylist.txt
enable_npc card_remover.txt
enable_npc platinum_skills.txt
enable_npc resetnpc.txt
enable_npc jobmaster.txt

# garantir starter items
if ! grep -q "starter_items.txt" "$NPCCONF"; then
    echo "npc: npc/custom/starter_items.txt" >> "$NPCCONF"
fi

# Telemetria de Evento / Torneio (Speedrun 99 e MVP Bounty)
cat <<EOF > $RATHENA/npc/custom/event_telemetry.txt
-	script	EventTelemetry	-1,{
OnPCLoginEvent:
	if (getgmlevel() > 0 || getcharid(3) >= 2000010) end;
	if (char_created_tick == 0) {
		char_created_tick = gettimetick(2);
	}
	end;

OnPCBaseLvUpEvent:
	if (getgmlevel() > 0 || getcharid(3) >= 2000010) end;
	if (BaseLevel >= 99 && has_achieved_99 == 0) {
		has_achieved_99 = 1;
		.@now_tick = gettimetick(2);
		if (char_created_tick == 0) {
			char_created_tick = .@now_tick;
		}
		.@total_seconds = .@now_tick - char_created_tick;
		if (.@total_seconds < 1) {
			.@total_seconds = 1;
		}
		.@mins = .@total_seconds / 60;
		query_sql("INSERT INTO event_speedruns (char_id, name, class, base_level, job_level, total_seconds, achieved_at, created_at, updated_at) VALUES (" + getcharid(0) + ", '" + escape_sql(strcharinfo(0)) + "', " + Class + ", " + BaseLevel + ", " + JobLevel + ", " + .@total_seconds + ", NOW(), NOW(), NOW()) ON DUPLICATE KEY UPDATE total_seconds = VALUES(total_seconds), updated_at = NOW()");
		announce "[TORNEIO SPEEDRUN] " + strcharinfo(0) + " alcançou o Nível 99 em " + .@mins + " minutos!", bc_all, 0x00FF00;
	}
	end;

OnNPCKillEvent:
	if (getgmlevel() > 0 || getcharid(3) >= 2000010) end;
	if (getmonsterinfo(killedrid, MOB_MVPEXP) > 0) {
		.@mob_name$ = getmonsterinfo(killedrid, MOB_NAME);
		query_sql("INSERT INTO event_mvp_kills (char_id, char_name, mob_id, mob_name, killed_at, created_at, updated_at) VALUES (" + getcharid(0) + ", '" + escape_sql(strcharinfo(0)) + "', " + killedrid + ", '" + escape_sql(.@mob_name$) + "', NOW(), NOW(), NOW())");
		announce "[MVP BOUNTY] " + strcharinfo(0) + " derrotou o chefe " + .@mob_name$ + "!", bc_all, 0xFF8800;
	}
	end;
}
EOF

if ! grep -q "event_telemetry.txt" "$NPCCONF"; then
    echo "npc: npc/custom/event_telemetry.txt" >> "$NPCCONF"
fi

#################################
# 5 - garantir carregamento dos NPCs custom
#################################

ATHENACONF="$RATHENA/npc/scripts_athena.conf"

echo "=== Garantindo scripts_custom.conf ==="

if ! grep -q "scripts_custom.conf" "$ATHENACONF"; then
    echo "import: npc/scripts_custom.conf" >> "$ATHENACONF"
    echo "scripts_custom.conf adicionado ao scripts_athena.conf"
fi

# Corrigir entrada incorreta (npc: em vez de import:)
sed -i 's|^npc: npc/scripts_custom.conf$|import: npc/scripts_custom.conf|' "$ATHENACONF" || true


#################################
# 6 - finalizar ou reiniciar rAthena
#################################

if [ "$APPLY_ONLY" -eq 0 ]; then
    echo "=== Reiniciando rAthena ==="
    cd $RATHENA
    ./athena-start start 1 || ./athena-start start || true
    echo "=== rAthena reiniciado com sucesso com o modo CASUAL ==="
else
    echo "=== Modo CASUAL aplicado com sucesso nas configurações ==="
fi

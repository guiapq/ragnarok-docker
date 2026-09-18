#!/bin/bash

set -e

if pgrep -f map-server > /dev/null
then
  echo "rAthena est   rodando, parando..."
  cd /usr/bin/rathena
  sh ./athena-start stop
fi


echo "=== Parando rAthena se estiver rodando ==="

cd /usr/bin/rathena

sh ./athena-start stop || true


#################################
# path
#################################

#RATHENA=${RATHENA_PATH:-/datastoresetup/usr-bin-rathena}
RATHENA=/usr/bin/rathena

echo "=== Aplicando modo CASUAL ==="
echo "Rathena path: $RATHENA"

#################################
# 1 - EXP rates
#################################

sed -i 's/base_exp_rate:.*/base_exp_rate: 33000/' $RATHENA/conf/battle/exp.conf || true
sed -i 's/job_exp_rate:.*/job_exp_rate: 33000/' $RATHENA/conf/battle/exp.conf || true

#################################
# 2 - DROP rates
#################################

sed -i 's/item_rate_common:.*/item_rate_common: 1500/' $RATHENA/conf/battle/drops.conf || true
sed -i 's/item_rate_heal:.*/item_rate_heal: 500/' $RATHENA/conf/battle/drops.conf || true
sed -i 's/item_rate_equip:.*/item_rate_equip: 1000/' $RATHENA/conf/battle/drops.conf || true
sed -i 's/item_rate_card:.*/item_rate_card: 300/' $RATHENA/conf/battle/drops.conf || true

#################################
# 3 - remover PIN
#################################

echo "=== Desativando sistema de PIN ==="

sed -i 's/pincode_enabled:.*/pincode_enabled: no/' $RATHENA/conf/char_athena.conf || true
sed -i 's/pincode_force:.*/pincode_force: no/' $RATHENA/conf/char_athena.conf || true

echo "PIN config atual:"
grep pincode $RATHENA/conf/char_athena.conf || true

#################################
# 4 - starter items
#################################

mkdir -p $RATHENA/npc/custom

cat <<EOF > $RATHENA/npc/custom/starter_items.txt
-	script	Starter_Items	-1,{

OnPCLoginEvent:
	if (#starter_items_given == 0) {
		getitem 611,10000; // lupa
		dispbottom "Você recebeu 10000 lupas iniciais!";
                getitem 501,150;		
		getitem 4002,2;
                getitem 22508,1;
                getitem 2828,1;  //enhanced
		getitem 2214,1;
		getitem 602,5;    // Butterfly Wing
		getitem 2829,1;   //greed
		getitem 2501,1;
                getitem 2401,1;
		getitem 4003,1;
		getitem 4012,2;
		getitem 969,3;
		getitem 616,25;
		getitem 2060,20;
		getitem 2059,20;
		getitem 12323,90;
		getitem 2102,1;
		getitem 2306,1;
		getitem 1207,1;

		#starter_items_given = 1;
		dispbottom "Você recebeu 150 poções iniciais e mais!";
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
	if (#char_created_tick == 0) {
		#char_created_tick = gettimetick(2);
	}
	end;

OnPCBaseLvUpEvent:
	if (BaseLevel >= 99 && #has_achieved_99 == 0) {
		#has_achieved_99 = 1;
		.@now_tick = gettimetick(2);
		.@total_seconds = .@now_tick - #char_created_tick;
		if (.@total_seconds < 1) {
			.@total_seconds = 1;
		}
		.@mins = .@total_seconds / 60;
		query_sql("INSERT INTO event_speedruns (char_id, name, class, base_level, job_level, total_seconds, achieved_at, created_at, updated_at) VALUES (" + getcharid(0) + ", '" + escape_sql(strcharinfo(0)) + "', " + Class + ", " + BaseLevel + ", " + JobLevel + ", " + .@total_seconds + ", NOW(), NOW(), NOW()) ON DUPLICATE KEY UPDATE total_seconds = VALUES(total_seconds), updated_at = NOW()");
		announce "[TORNEIO SPEEDRUN] " + strcharinfo(0) + " alcançou o Nível 99 em " + .@mins + " minutos!", bc_all, 0x00FF00;
	}
	end;

OnNPCKillEvent:
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
    echo "npc: npc/scripts_custom.conf" >> "$ATHENACONF"
    echo "scripts_custom.conf adicionado ao scripts_athena.conf"
fi


#################################
# 6 - iniciar servidor
#################################

echo "=== Iniciando rAthena ==="

cd /
sh start.sh

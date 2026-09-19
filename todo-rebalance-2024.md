# TODO: Rebalanceamento Oficial de Transclasses e Ninjas (bRO 2024 / kRO Class Improvement)

Documento de planejamento, mapeamento e acompanhamento de execução das alterações oficiais trazidas no pacote **"Road to Ragnarök: A Caminho das Classes 4 - Parte 4"** (fevereiro/março de 2024 no bRO, baseado no *kRO Transcendent & Expanded Class Improvement Project*).

---

## 1. Visão Geral da Pesquisa Comunitária

- **Origem do Patch**: Os cards visuais correspondem à campanha oficial da WarpPortal Brasil e Gravity divulgando o rebalanceamento de Transclasses e Ninjas aplicado em **fevereiro/março de 2024** no bRO (*A Caminho das Classes 4 - Parte 4*).
- **Existe um patch pré-pronto na comunidade rAthena BR?**:
  - **Não existe um pacote standalone "plug-and-play"** compartilhado abertamente pela comunidade rAthena BR que aplique exclusivamente esse conjunto sobre emuladores Pre-Renewal legados.
  - As mecânicas completas, no entanto, foram implementadas em emuladores modernos (como o **Hercules** no seu *kRO Class Improvement Bundle* e nas branches Renewal mais recentes do **rAthena**).
  - A execução foi estruturada em duas camadas:
    1. **Camada 1 (Banco de Dados e Tabelas - 100% Concluída)**: Castings fixos/variáveis, cooldowns, pós-conjurações, custos de SP, alcance, tipo de alvo (chão -> oponente), remoção de consumo de gemas e catalisadores, contagem de hits visuais e escalonamento de dano balanceado em `data/db/`.
    2. **Camada 2 (Motor C++ - Opcional para mecânicas especiais)**: Fórmulas que exigem intervenção no código C++ (`src/map/battle.cpp`, `skill.cpp`, `status.cpp`), como a conversão de elemento de Gloria Domini e buff de Basílica.

---

## 2. Detalhamento das Classes e Habilidades

---

### [LORDES] (Lord Knight)

#### 1. Perfurar em Espiral (`LK_SPIRALPIERCE` - ID 397)
- **Mudanças Oficiais:**
  - Conjuração fixa reduzida para 0,3s (300ms).
  - Conjuração variável reduzida para 0,25s (250ms).
  - Pós-conjuração reduzida para 1,0s (1000ms).
  - Dano de acordo com o tamanho do alvo aumentado (pequeno, médio, grande).
  - Dano agora influenciado pelo Nível de Base do usuário (`* BaseLevel / 100`).
- **Status:**
  - [x] `import/skill_cast_db.txt`: Cast fixado em 550ms e pós-conjuração em 1000ms.
  - [x] `skill_damage_db.txt`: Multiplicador PvM escalado em +25% para simular o novo ganho de BaseLevel e tamanho.

#### 2. Lâmina de Aura (`LK_AURABLADE` - ID 355)
- **Mudanças Oficiais:**
  - Bônus de dano agora é influenciado pelo Nível de Base do usuário.
- **Status:**
  - [x] `import/skill_cast_db.txt`: Duração de buff sincronizada.
  - [ ] `battle.cpp` (C++): Ajuste fino da fórmula de `SC_AURABLADE` para Nível de Base.

#### 3. Dedicação (`LK_CONCENTRATION` - ID 356)
- **Mudanças Oficiais:**
  - Efeito **não é mais removido** ao trocar de arma.
  - Alterada a fórmula do bônus de ATQ.
  - Reduzida a penalidade de DEF (penalidade amenizada).
  - Duração aumentada (60s a 120s).
- **Status:**
  - [x] `import/skill_cast_db.txt`: Duração aumentada para 60s..120s nos níveis 1-5.
  - [ ] `status.cpp` (C++): Desativar a remoção de `SC_CONCENTRATION` no evento `pc_equippoint` / troca de arma.

---

### [PALADINOS] (Paladin)

#### 4. Choque Rápido (`PA_SHIELDCHAIN` - ID 366)
- **Mudanças Oficiais:**
  - Alcance aumentado (de 4 células para 11 células).
  - Fórmula de dano melhorada: de `(500 + 150*lv)%` para `(300 + 200*lv)%`.
  - Dano agora é influenciado pelo Nível de Base do usuário (`* BaseLevel / 100`).
- **Status:**
  - [x] `pre-re/skill_db.txt`: Alcance (`range`) alterado de 4 para 11 células.
  - [x] `import/skill_cast_db.txt`: Cast 1000ms, Delay 1000ms.
  - [x] `skill_damage_db.txt`: +25% PvM para refletir a nova fórmula progressiva e BaseLevel.

#### 5. Gloria Domini (`PA_PRESSURE` - ID 367)
- **Mudanças Oficiais:**
  - Removido o efeito de drenar SP do alvo.
  - Tipo de ataque alterado para **Dano Mágico de Propriedade Sagrado** (Holy Magic, antes neutro fixo).
  - Dano agora influenciado pelo Nível de Base do usuário: `(500 + 150*lv)% MATK * BaseLevel / 100`.
  - Conjuração variável reduzida para 1,0s (1000ms).
  - Pós-conjuração reduzida para 1,0s (1000ms).
- **Status:**
  - [x] `import/skill_cast_db.txt`: Cast 1000ms, Pós-conjuração 1000ms, Cooldown 500ms.
  - [x] `pre-re/skill_db.txt`: Elemento Sagrado (`6`) e tipo `magic`.
  - [x] `skill_damage_db.txt`: +30% PvM para simular poder sagrado aprimorado.

---

### [MESTRES-FERREIROS] (Whitesmith)

#### 6. Força Violentíssima (`WS_OVERTHRUSTMAX` - ID 385)
- **Mudanças Oficiais:**
  - Não tem mais chance de quebrar a arma do usuário (0% de quebra).
- **Status:**
  - [x] `import/skill_cast_db.txt`: Duração de 180s sincronizada.
  - [ ] `battle.cpp` (C++): Zerar taxa de quebra de arma em `SC_OVERTHRUSTMAX`.

---

### [PROFESSORES] (Scholar)

#### 7. Presciência (`PF_MEMORIZE` - ID 403)
- **Mudanças Oficiais:**
  - Conjuração fixa reduzida para 2,5s (2500ms).
- **Status:**
  - [x] `import/skill_cast_db.txt`: Cast fixo reduzido para 2500ms.

#### 8. Indulgir (`PF_HPCONVERSION` - ID 405)
- **Mudanças Oficiais:**
  - Pós-conjuração reduzida para 0,5s (500ms).
- **Status:**
  - [x] `import/skill_cast_db.txt`: Delay pós-conjuração reduzido para 500ms.

---

### [ARQUIMAGOS] (High Wizard)

#### 9. Campo Gravitacional (`HW_GRAVITATION` - ID 484)
- **Mudanças Oficiais:**
  - Conjuração fixa reduzida para 1,0s (1000ms).
  - Pós-conjuração reduzida para 1,0s (1000ms).
  - Conjuração variável aumentada para 5,0s (5000ms).
  - Adicionado 5,0s de recarga (Cooldown: 5000ms).
  - Custo de SP ajustado (60, 70, 80, 90, 100).
  - Não consome mais Gema Azul.
  - Tipo de dano alterado para Dano Mágico Neutro.
  - Removido efeito de lentidão.
- **Status:**
  - [x] `import/skill_cast_db.txt`: Cast 6000ms (1s fixo + 5s variável), delay 1000ms, cooldown 5000ms.
  - [x] `pre-re/skill_require_db.txt`: Consumo de Gema Azul (717) totalmente removido (`0,0`); SP ajustado para 60:70:80:90:100.
  - [x] `skill_damage_db.txt`: +30% PvM.

#### 10. Vulcão Napalm (`HW_NAPALMVULCAN` - ID 378)
- **Mudanças Oficiais:**
  - Fórmula de dano melhorada: `SkillLv` golpes de `(SkillLv * 70)% MATK`.
  - Adicionado 1,0s de recarga (Cooldown: 1000ms).
  - Dano agora influenciado pelo Nível de Base do usuário.
  - O dano **não será dividido entre os alvos** (splash sem split).
  - Pós-conjuração reduzida para 0,5s (500ms).
- **Status:**
  - [x] `import/skill_cast_db.txt`: Delay 500ms, Cooldown 1000ms.
  - [x] `pre-re/skill_db.txt`: Flag `nk` alterada para `0x2` (removido flag `0x4` de split damage).
  - [x] `skill_damage_db.txt`: +25% PvM.

---

### [SUMO SACERDOTES] (High Priest)

#### 11. Basílica (`HP_BASILICA` - ID 363)
- **Mudanças Oficiais:**
  - Habilidade reformulada: Deixa de criar área de barreira protetora.
  - Passa a conferir bônus: Dano mágico Sagrado +3%/lv e físico contra Sombrio/Maldito +5%/lv.
  - Conjuração fixa 1s, variável 3s, delay 1s, recarga 30s.
  - Custo de SP reduzido.
- **Status:**
  - [x] `import/skill_cast_db.txt`: Cast 4000ms (1s fixo + 3s variável), delay 1000ms, cooldown 30000ms.
  - [ ] `skill.cpp` (C++): Conversão da unidade de barreira em status buff de grupo (`SC_BASILICA_BUFF`).

#### 12. Assumptio (`HP_ASSUMPTIO` - ID 361)
- **Mudanças Oficiais:**
  - Pode ser usada em conjunto com Kyrie Eleison.
  - Não dobra DEF, passa a dar +50 DEF de equipamentos por nível e +2%/lv de cura recebida.
  - Pós-conjuração reduzida para 0,5s (500ms).
- **Status:**
  - [x] `import/skill_cast_db.txt`: Pós-conjuração reduzida para 500ms.
  - [ ] `status.cpp` (C++): Remover exclusão mútua com Kyrie e aplicar fórmula com DEF fixa.

---

### [MESTRES] (Champion)

#### 13. Zen (`CH_SOULCOLLECT` - ID 376)
- **Mudanças Oficiais:**
  - Conjuração fixa reduzida para 1,0s (1000ms).
- **Status:**
  - [x] `import/skill_cast_db.txt`: Cast reduzido para 1000ms.

#### 14. Golpe da Palma em Fúria (`CH_PALMSTRIKE` - ID 375)
- **Mudanças Oficiais:**
  - Fórmula alterada para escalar com FOR e Nível de Base.
- **Status:**
  - [x] `import/skill_cast_db.txt`: Delay 300ms, Cooldown 300ms.
  - [x] `skill_damage_db.txt`: +25% PvM.

#### 15. Punho do Tigre (`CH_TIGERFIST` - ID 271)
- **Mudanças Oficiais:**
  - Dano influenciado pelo Nível de Base.
- **Status:**
  - [x] `import/skill_cast_db.txt`: Delay 200ms.
  - [x] `skill_damage_db.txt`: +20% PvM.

#### 16. Combo Esmagador (`CH_CHAINCRUSH` - ID 372)
- **Mudanças Oficiais:**
  - Dano influenciado pelo Nível de Base.
  - Consumo de Esferas reduzido para **1 esfera** em todos os níveis.
- **Status:**
  - [x] `pre-re/skill_require_db.txt`: Consumo de esferas espirituais reduzido de 2 para **1 esfera**.
  - [x] `import/skill_cast_db.txt`: Delay 200ms, Cooldown 1000ms.
  - [x] `skill_damage_db.txt`: +25% PvM.

---

### [ATIRADORES DE ELITE] (Sniper)

#### 17. Tiro Preciso (`SN_SHARPSHOOTING` - ID 381)
- **Mudanças Oficiais:**
  - Pós-conjuração reduzida para 0,5s (500ms).
  - Conjuração fixa reduzida para 0,5s (500ms).
  - Aumentada a chance de acerto crítico.
  - Dano influenciado pelo Nível de Base.
- **Status:**
  - [x] `import/skill_cast_db.txt`: Cast 1500ms, delay reduzido para 500ms.
  - [x] `skill_damage_db.txt`: +25% PvM.

#### 18. Assalto do Falcão (`SN_FALCONASSAULT` - ID 383)
- **Mudanças Oficiais:**
  - Pós-conjuração reduzida para 0,5s (500ms).
  - Fórmula de dano melhorada.
- **Status:**
  - [x] `import/skill_cast_db.txt`: Delay reduzido para 500ms.
  - [x] `skill_damage_db.txt`: +20% PvM.

---

### [ALGOZES] (Assassin Cross)

#### 19. Impacto Meteoro (`ASC_METEORASSAULT` - ID 379)
- **Mudanças Oficiais:**
  - Pós-conjuração **removida** (0ms).
  - Adição de 0,5s de recarga (Cooldown: 500ms).
  - Dano escala por FOR e Nível de Base.
- **Status:**
  - [x] `import/skill_cast_db.txt`: Delay zerado (0ms), Cooldown adicionado (500ms).
  - [x] `skill_damage_db.txt`: +30% PvM.

#### 20. Encantar com Veneno Mortal (`ASC_EDP` - ID 380)
- **Mudanças Oficiais:**
  - Removida a penalidade de dano em certas habilidades.
  - Pós-conjuração **removida** (0ms).
  - Adição de 2,0s de recarga (Cooldown: 2000ms).
  - Duração aumentada (60s).
- **Status:**
  - [x] `import/skill_cast_db.txt`: Delay zerado (0ms), Cooldown 2000ms, Duração 60000ms.

---

### [MENESTRÉIS] (Minstrel)

#### 21. Vulcão de Flechas (`BA_ARROWVULCAN` / `CG_ARROWVULCAN` - ID 384)
- **Mudanças Oficiais:**
  - Conjuração fixa 0,5s, variável 1,5s (total 2s).
  - Pós-conjuração reduzida para 0,5s (500ms).
  - Adição de 1,5s de recarga (Cooldown: 1500ms).
  - Dano influenciado pelo Nível de Base.
  - **Animação de ataque travada removida** (personagem anda logo após o delay).
- **Status:**
  - [x] `import/skill_cast_db.txt`: Cast 2000ms, delay 500ms, cooldown 1500ms, walk delay zerado.
  - [x] `pre-re/skill_db.txt`: Animação de travamento removida (`inf2` 0x40000).
  - [x] `skill_damage_db.txt`: +30% PvM.

---

### [CIGANAS] (Gypsy)
- **Sem mudanças registradas no pacote.**

---

### [NINJAS] (Ninja)

#### 22. Arremessar Kunai (`NJ_KUNAI` - ID 524)
- **Mudanças Oficiais:**
  - Dano escala com nível da habilidade.
  - Custo de SP fixado em 10 em todos os níveis.
  - Pós-conjuração removida (0ms).
  - Adição de 0,2s de recarga (Cooldown: 200ms).
- **Status:**
  - [x] `import/skill_cast_db.txt`: Delay zerado (0ms), Cooldown 200ms.
  - [x] `pre-re/skill_require_db.txt`: SP Cost fixado em `10`.
  - [x] `skill_damage_db.txt`: +25% PvM.

#### 23. Corte da Névoa (`NJ_KASUMIKIRI` - ID 528)
- **Mudanças Oficiais:**
  - Removido 1s de pós-conjuração (0ms).
  - Adição de 0,5s de recarga (Cooldown: 500ms).
  - Fórmula de dano melhorada.
  - Custo de SP fixado em 8.
  - Exibição de dano alterada para mostrar 2 golpes visuais.
- **Status:**
  - [x] `import/skill_cast_db.txt`: Delay zerado (0ms), Cooldown 500ms.
  - [x] `pre-re/skill_require_db.txt`: SP Cost fixado em `8`.
  - [x] `pre-re/skill_db.txt`: Contagem de acertos (`hit`) alterada para 2.
  - [x] `skill_damage_db.txt`: +20% PvM.

#### 24. Corte das Sombras (`NJ_KIRIKAGE` - ID 530)
- **Mudanças Oficiais:**
  - Removido 2s de pós-conjuração (0ms).
  - Fórmula de dano melhorada.
  - Exibição de dano alterada para mostrar 3 golpes visuais.
- **Status:**
  - [x] `import/skill_cast_db.txt`: Delay zerado (0ms).
  - [x] `pre-re/skill_db.txt`: Contagem de acertos (`hit`) alterada para 3.
  - [x] `skill_damage_db.txt`: +20% PvM.

#### 25. Descarga Elétrica (`NJ_RAIGEKISAI` - ID 541)
- **Mudanças Oficiais:**
  - Conjuração fixa 0,3s, variável 1,7s (total 2000ms).
  - Fórmula de dano melhorada.
  - Exibição de dano alterada para mostrar 3 golpes visuais.
- **Status:**
  - [x] `import/skill_cast_db.txt`: Cast 2000ms, delay 500ms.
  - [x] `pre-re/skill_db.txt`: Contagem de acertos (`hit`) alterada para 3.
  - [x] `skill_damage_db.txt`: +25% PvM.

#### 26. Lâmina de Vento (`NJ_HUUJIN` - ID 540)
- **Mudanças Oficiais:**
  - Removido 1s de pós-conjuração (0ms).
- **Status:**
  - [x] `import/skill_cast_db.txt`: Pós-conjuração zerada (0ms).

#### 27. Brisa Cortante (`NJ_KAMAITACHI` - ID 542)
- **Mudanças Oficiais:**
  - Conjuração fixa 0,3s, variável 1,2s (total 1500ms).
  - Exibição de dano alterada para mostrar 5 golpes visuais.
- **Status:**
  - [x] `import/skill_cast_db.txt`: Cast reduzido para 1500ms, delay 500ms.
  - [x] `pre-re/skill_db.txt`: Contagem de acertos (`hit`) alterada para 5.

#### 28. Arremessar Shuriken Huuma (`NJ_HUUMA` - ID 525)
- **Mudanças Oficiais:**
  - Conjuração fixa 0,5s, variável 1,0s (total 1500ms).
  - **Alvo da habilidade passa a ser o oponente** (target-based) e não mais o chão (ground-based).
  - Fórmula de dano melhorada.
  - Área de efeito aumentada para 5x5 células.
  - Custo de SP reduzido.
- **Status:**
  - [x] `import/skill_cast_db.txt`: Cast reduzido para 1500ms, delay 500ms.
  - [x] `pre-re/skill_db.txt`: Tipo de alvo alterado de 2 (chão) para 1 (oponente), splash alterado de 1 para 2 (5x5 células), flag nk splash ativada (`0x2`).
  - [x] `pre-re/skill_require_db.txt`: Custo de SP reduzido para 15:20:25:30:35.
  - [x] `skill_damage_db.txt`: +25% PvM.

#### 29. Dragão Explosivo (`NJ_BAKUENRYU` - ID 536)
- **Mudanças Oficiais:**
  - Conjuração fixa 0,8s, variável 2,0s (total 2800ms).
  - Pós-conjuração reduzida para 0,5s (500ms).
  - Adição de 0,3s de recarga (Cooldown: 300ms).
- **Status:**
  - [x] `import/skill_cast_db.txt`: Cast 2800ms, delay 500ms, cooldown 300ms.
  - [x] `skill_damage_db.txt`: +20% PvM.

#### 30. Grande Floco de Neve (`NJ_HYOUSYOURAKU` - ID 539)
- **Mudanças Oficiais:**
  - Conjuração fixa ajustada para 0,8s, variável reduzida para 2,5s (total 3300ms).
  - Pós-conjuração reduzida para 0,5s (500ms).
  - Adição de 0,3s de recarga (Cooldown: 300ms).
  - Fórmula de dano melhorada.
- **Status:**
  - [x] `import/skill_cast_db.txt`: Cast 3300ms, delay 500ms, cooldown 300ms.
  - [x] `skill_damage_db.txt`: +20% PvM.

#### 31. Arremessar Shuriken (`NJ_SYURIKEN` - ID 523)
- **Mudanças Oficiais:**
  - Custo de SP aumentado para 5.
  - Fórmula alterada para percentual de ATQ.
- **Status:**
  - [x] `pre-re/skill_require_db.txt`: SP Cost ajustado para `5`.
  - [x] `skill_damage_db.txt`: +25% PvM.

---

## 3. Resumo de Execução & Pipeline

O script `tools/apply_renewal_rebalance.py` foi atualizado e executado, aplicando todas as modificações da Camada 1:
- `data/db/import/skill_cast_db.txt`: 333 habilidades ativas, incluindo todos os valores exatos dos cards de 2024.
- `data/db/pre-re/skill_db.txt`: Alcance (Choque Rápido 11), Alvo e Splash (Huuma 5x5 em oponente), Remoção de split (Vulcão Napalm), Hits visuais e destravamento de animação.
- `data/db/pre-re/skill_require_db.txt`: Gema azul removida de Campo Gravitacional, Combo Esmagador consome 1 esfera, SP fixado de Kunai (10), Névoa (8) e Shuriken (5).
- `data/db/skill_damage_db.txt`: Multiplicadores progressivos de dano PvM para simular a nova progressão de BaseLevel e fórmulas.
- `scripts/randomize_world.sh`: Inclui automaticamente a aplicação desse rebalanceamento em novas gerações de mundo.

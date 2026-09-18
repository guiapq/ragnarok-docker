# Ragnarok Docker v2 — Roadmap & Backlog de Evolução

Este documento consolida o estado atual das entregas da **Versão 2 (v2)** e detalha o planejamento técnico das próximas funcionalidades de gameplay procedural, sincronização cliente-servidor e infraestrutura autônoma.


---

## 0. Identidade & Filosofia de Design (Roguelike Efêmero & Torneios de Eventos)

> **Premissa Fundamental**: Este projeto **não é um MMO eterno**, com economia inflacionária, WoE massiva de centenas de players ou grind de meses. É um servidor **descartável e portátil**, projetado para:
> 1. **Loop Roguelike Solo (~12 horas)**: Um jogador cria seu personagem, progride do nível 1 ao 99 em um único final de semana, monta uma build funcional com drops procedurais, derrota MVPs solo e "vai trabalhar na segunda-feira com o dever cumprido".
> 2. **Operações Curtas e Descartáveis (1 dia a 3 meses)**: Ideal para ser levantado localmente em computadores de eventos de anime, encontros presenciais, LAN parties ou temporadas rápidas. Ao fim da rodada/evento, o mundo pode ser descartado ou resetado com uma nova seed.
> 3. **Competitividade Local / Metropolitana**: Em eventos presenciais de anime ou redes locais, o foco competitivo é o desafio rápido:
>    - **Speedrun 1-99**: Quem atinge o nível máximo mais rápido a partir de uma seed desconhecida.
>    - **MVP Bounty Hunter**: Placar ao vivo de caça a MVPs (primeiro a abater, maior quantidade de MVPs distintos solados).
>    - **Modo Telão/Kiosk**: Interface do painel que pode ficar aberta em fullscreen numa TV/projetor no estande do evento exibindo a liderança em tempo real.
> 4. **Fora de Escopo**: Economia persistente de mercado de longo prazo, guerras de guilda (GvG/WoE) de grande escala, taxas punitivas de 0.01% e sistemas burocráticos de retenção de jogadores.

---

## 1. Fundação da Versão 2 (Entregas Concluídas)

- [x] **Versionamento Git e Isolamento de Legado**:
  - Tag anotada `v1.0.0` congelando o estado monólito legado.
  - Branch de referência `v1` e branch ativa de trabalho `v2` publicadas no GitHub.
- [x] **roBrowser Estável e Personalizado**:
  - Código apontado para o fork próprio [`guiapq/roBrowserLegacy`](https://github.com/guiapq/roBrowserLegacy).
  - Commit travado no estado estável de 6 meses atrás (`fd9183f` — 18/03/2026).
  - Build-arg configurável `ROBROWSER_COMMIT` integrado no `docker-compose.yml`, `.env` e `.env.example`.
- [x] **Build Nativo do rAthena (Eliminação do `tvoll/ragnadocker`)**:
  - Dockerfile multi-stage nativo (`docker/rathena/Dockerfile`) compilando direto do fork [`guiapq/rathena`](https://github.com/guiapq/rathena) no commit `ac46920e73819662811573253d9b22592e8ad985`.
  - Remoção completa de Apache embutido, FluxCP legado e pacotes obsoletos.
  - Symlink `/usr/bin/rathena -> /opt/rathena` mantendo 100% de retrocompatibilidade com scripts operacionais.
- [x] **Inicialização Resiliente e Auto-Migração do Banco**:
  - Healthcheck ativo no `start.sh` com espera por `mysqladmin ping`.
  - Auto-importação de `main.sql` e `logs.sql` em bancos novos, eliminando falhas de tabela inexistente.
  - Logs unificados em primeiro plano (`tail -f`).
- [x] **Docker Registry Local (`localhost:5000`)**:
  - Serviço oficial `registry:2` integrado no `docker-compose.yml` com volume persistente `registry_data`.
  - Automação no `Makefile`: `make registry-up`, `make tag-images`, `make push-images`.
- [x] **Painel Web Moderno (Laravel 10 + Filament v3)**:
  - Submódulo Git `web/` apontando para o fork [`guiapq/ragnabraza-cp`](https://github.com/guiapq/ragnabraza-cp).
  - Container PHP 8.2 Alpine com Composer e extensões necessárias (`docker/panel/Dockerfile`).
  - Recursos Filament criados: `UserResource` (contas `login`), `CharacterResource` (personagens com reset de mapa) e `WorldDatabase` (explorador procedural).

---

## 2. Sincronização Dinâmica Client/Server (Item Descriptions em Runtime)

> **Objetivo**: Fazer com que qualquer item, atributo procedural, bônus ou arma gerada pelo `randomize_world.sh` exiba nome, status e lore corretos no roBrowser sem precisar recompilar ou alterar o `data.grf`.

- [x] **Criar Gerador de Metadados (`tools/generate_item_info_lua.py`)**:
  - Ler `data/db/re/item_db.txt` e extrair atributos calculados (`bAtk`, `bMatk`, `bCrit`, `bStr`, etc.).
  - Gerar descrições ricas com formatação nativa colorida do Ragnarok (`^RRGGBB`).
  - Associar itens customizados a sprites e ícones clássicos existentes via `identifiedResourceName` (ex: `"검"` para espadas, `"클립"` para acessórios).
  - Salvar o arquivo diretamente em `data/System/itemInfo.lua` (montado no container do roBrowser).
- [x] **Configuração do roBrowser para Leitura Dinâmica**:
  - Garantir no `Config.local.js` do roBrowser a flag `loadLua: true` e carregamento de `data/System/itemInfo.lua`.
  - Servido diretamente via HTTP sem reconstrução de `data.grf`.
- [x] **Integração no Pipeline de Geração**:
  - Adicionado `generate_item_info_lua.py` no final de `scripts/randomize_world.sh` para sincronização instantânea a cada novo mundo.

---

## 3. Engine de Drops Procedurais Inteligente (Refatoração de `randomize_drops.py`)

> **Objetivo**: Substituir a randomização ingênua (sorteio uniforme de IDs) por um sistema calibrado para o **Loop Roguelike Solo de 12 Horas**, onde o jogador é 100% autossuficiente (Solo Self-Found), sem depender de comércio com outros players.

- [x] **Sistema de Tiers por Nível de Monstro (Level Brackets)**:
  - Categorizar monstros pelo campo de nível (`cols[3]` de `mob_db.txt`):
    - *Tier 1 (Lv 1–25)*: Consumíveis básicos, armas tier 1, armaduras leves, etcs simples.
    - *Tier 2 (Lv 26–50)*: Poções médias, armas tier 2, armaduras médias, minérios brutos.
    - *Tier 3 (Lv 51–75)*: Poções brancas, armas tier 3, armaduras de placas, oridecon/elunium.
    - *Tier 4 (Lv 76–99 / Mini-bosses)*: Armas tier 4, acessórios raros, joias.
    - *Tier 5 (MvPs)*: Equipamentos divinos, slots máximos, caixas raras.
  - Implementar mecânica de *Lucky Roll* (2% a 5% de chance de um monstro puxar um item do Tier seguinte).
- [x] **Slots de Drop com Papéis Estruturados (Role-based Slots)**:
  - *Slot 1 (Sobrevivência Solo)*: Cura e utilitários (poções, asas, ervas) com taxa generosa (30% a 60%) para sustentar gameplay sem priest.
  - *Slots 2–3 (Economia)*: Itens Etc para venda no NPC com taxa de 40% a 70%.
  - *Slot 4 (Progressão)*: Minérios de refino e gemas com taxa de 10% a 25%.
  - *Slot 5 (Equipamento do Tier)*: Armas e armaduras compatíveis com taxa de 5% a 15% (viabilizando montagem de build em 12h).
  - *Slot 6 (Equipamento Raro / Joia)*: Itens especiais com taxa de 1% a 3%.
  - *Slot 7 (Curiosidade)*: Velha Caixa Azul, Galho Seco, etc., com taxa de 1% a 5%.
  - *Slot 8 (Carta)*: Carta preservada ou com chance ponderada.
- [x] **Curva de Probabilidade Ponderada e Pools Inteligentes**:
  - Classificação automática a partir de `eLV`, `wLV`, `Sell` e `Type` do `item_db.txt`.
- [x] **Curadoria e Limpeza de Base**:
  - Filtro de peso máximo (<=600) e IDs válidos.

---

## 4. Pesquisa & POC: "Libre GRF" (Assets Livres e Client Ultra-Leve)

> **Objetivo**: Avaliar e prototipar um pacote de assets 100% open-source/livre, reduzindo o client de ~3 GB para ~20 MB e eliminando qualquer dependência de arquivos proprietários da Gravity.

- [ ] **Mapeamento Mínimo do roBrowser**:
  - Listar o conjunto estrito de arquivos que o roBrowser precisa para abrir a tela de jogo:
    - Texturas da UI básica (`data/texture/유저인터페이스/...`).
    - 1 sprite e animação de classe básica (ex: Aprendiz / Espadachim).
    - 1 mapa funcional minimalista (arquivos `.gnd`, `.rsw`, `.rsm`).
    - 3 a 5 monstros básicos.
    - Efeitos sonoros essenciais (golpe, dano, andar).
- [ ] **Pipeline de Montagem Automatizada (`tools/build_libre_grf.py`)**:
  - Script em Python para empacotar uma pasta de assets livres no formato GRF standard (GRF 0x200).
- [ ] **Configuração em Cascata no roBrowser**:
  - Configurar `remoteClient` no `Config.local.js` para suportar overlay:
    ```javascript
    remoteClient: [
        "libre.grf",       // Assets livres e leves da base
        "data.grf"        // Opcional: GRF oficial se fornecido pelo usuário
    ]
    ```

---

## 5. Expansão do Painel Web (Filament v3) & Módulo de Torneios / Eventos

> **Objetivo**: Fornecer controle operacional rápido e interfaces competitivas locais para telões em convenções de anime e encontros presenciais.

- [x] **Módulo Competitivo Local (Torneios de Convenção de Anime)**:
  - **Speedrun 1-99 Leaderboard**:
    - Tabela de classificação no Filament (`EventTournaments.php`) e rota pública `/scoreboard` com ranking ordenado pelo menor tempo real de jogo (`formatted_time`).
  - **MVP Bounty Hunter Board**:
    - Monitoramento de abates de MVPs com contagem de kills totais e diversidade de chefes eliminados.
  - **Modo Kiosk / Telão do Evento (`/scoreboard`)**:
    - View pública com auto-refresh a cada 15 segundos e design retro arcade neon/dark para projetores e TVs em estandes de convenção.
  - **Telemetria de Servidor no rAthena (`casual.sh`)**:
    - Script customizado `event_telemetry.txt` capturando `OnPCBaseLvUpEvent` (registro no Lv 99) e `OnNPCKillEvent` (abates de MVP) com persistência no MySQL e broadcast global in-game.
  - **Ferramenta de Reset de Temporada / Novo Dia de Evento**:
    - Ação administrativa no Filament para limpar os placares e preparar nova rodada com seed limpa.
- [ ] **World Seed Manager Interativo**:
  - Adicionar ação de formulário no Filament para digitar uma nova seed e disparar a geração do mundo (`make world SEED=...`) em segundo plano, exibindo os logs em tempo real na interface web.
- [ ] **Visualizador Detalhado de Drops e Spawns**:
  - Expandir a página `WorldDatabase` para mostrar quais monstros dropam determinado item pesquisado e em quais mapas eles aparecem.

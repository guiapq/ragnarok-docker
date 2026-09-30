# Arquitetura do Sistema — RagnaRogue (v3.0)

Este documento descreve a organização arquitetural da stack RagnaRogue, fluxos de dados, subsistemas procedurais e o ciclo de vida dos dados em runtime.

---

## 1. Visão Geral dos Microsserviços

A infraestrutura é executada em containers Docker orquestrados por `docker-compose.yml`:

```
                       +-----------------------+
                       |    Navegador Web      |
                       +-----------+-----------+
                                   |
         +-------------------------+-------------------------+
         |                         |                         |
         v :8000                   v :8001                   v :8080
+-----------------+       +-----------------+       +-----------------+
| ragnarok-panel  |       |    robrowser    |       |   phpMyAdmin    |
| (Laravel 10 /   |       | (Node 20 HTTP / |       | (Administração  |
|  Filament v3)   |       |  WASM Client)   |       |  do Banco SQL)  |
+--------+--------+       +--------+--------+       +--------+--------+
         |                         | :5999 (WebSocket)       |
         |                         v                         |
         |                +-----------------+                |
         |                | ragnarok-server |                |
         |                | (rAthena C++    |<---------------+
         |                |  Login/Char/Map)|
         |                +--------+--------+
         |                         |
         +------------+            | :3306 (TCP)
                      |            |
                      v            v
               +-------------------------+
               |       ragnarok-db       |
               |     (MariaDB 10.5)      |
               +-------------------------+
```

### Componentes:
1. **`ragnarok-server` (rAthena Pré-Renewal)**:
   - Compilado com customizações para taxas roguelike, sistema de miasma e telemetria de speedruns.
   - Monta em runtime o diretório local `./data:/rAthena`.
2. **`robrowser` (Cliente Web HTML5/WebAssembly)**:
   - Servidor HTTP na porta `8001` servindo a aplicação roBrowser.
   - Engine Lua executada nativamente via WebAssembly (`liblua5.1.wasm`).
   - Servidor proxy WebSocket na porta `5999` encapsulando os pacotes TCP do protocolo rAthena.
3. **`ragnarok-panel` (Painel Laravel Filament)**:
   - Interface administrativa moderna para monitoramento de contas, personagens e mundos.
   - Sincroniza migrations de mundo geradas proceduralmente.
4. **`ragnarok-db` (MariaDB 10.5)**:
   - Persistência das contas (`login`), personagens (`char`), inventário (`inventory`), estado de conquistas (`world_map_conquests`) e fragmentos (`world_comet_fragments`).
5. **`ragnarok-registry` (Docker Registry v2)**:
   - Registro local privado na porta `5000` para cache de imagens compiladas e deploy em LAN.

---

## 2. Camadas de Dados e Isolamento

Para garantir **reprodutibilidade e integridade total**:

* **`data_base/` (Base Imutável)**:
  Contém o código-fonte original do rAthena, scripts de NPCs e bancos de dados (`db/`, `npc/`, `conf/`). Esta pasta **nunca** é alterada pelos geradores randômicos de mundo.
* **`data/` (Runtime Dinâmico)**:
  Espelho operacional montado dentro do container do emulador. Ao gerar um novo mundo, `data/` é recriado a partir de `data_base/` e recebe os arquivos procedurais da nova seed.
* **`robrowser_base/` e `client/`**:
  Assets do cliente web e tabelas de itens compiladas (`itemInfo.lua`), decodificadas com codificação UTF-8 / Windows-1252 para suporte completo ao Português (PT-BR).

---

## 3. Pipeline de Geração de Novo Mundo (`./novo_mundo.sh`)

O ciclo de vida de uma nova era segue uma esteira determinística orientada por semente:

```
[ Seed (ex: infernal-phreeoni-113) ]
                 │
                 ▼
[ 1. Reset Atômico do Banco SQL ]
     - Truncate de inventários, personagens e quests
     - Reconstrução da conta roadmin (GM 99)
     - Reconstrução de 14 contas de teste pré-balanceadas
                 │
                 ▼
[ 2. Clonagem Limpa da Base ]
     - data/ recriado a partir de data_base/
                 │
                 ▼
[ 3. Pipeline Procedural Python ]
     ├─ enhance_unpopular_cards.py ➔ 123 cartas rebalanceadas
     ├─ randomize_drops.py         ➔ 1.008 monstros sanitizados PT-BR
     ├─ randomize_shops.py         ➔ Lojas dinâmicas por tier
     ├─ randomize_topology.py      ➔ Campanha v4 (4 Tiers, 44 rotas, auras)
     ├─ generate_map_spawns.py     ➔ 476 pontos de spawn determinísticos
     ├─ generate_comet_system.py   ➔ 7 Fragmentos com Taxi Distance
     └─ generate_item_info_lua.py  ➔ Compilação de descrições client web
                 │
                 ▼
[ 4. Sincronização com Laravel & Banco ]
     - Migration PHP gerada e executada no painel Filament
                 │
                 ▼
[ 5. Inicialização & Sanity Check ]
     - Validação de chaves de banco, integridade de scripts e subida dos containers
```

---

## 4. Subsistemas Exclusivos da v3.0

### A. Sistema do Cometa Negro & Taxi Distance
* O núcleo quebrado do cometa aloca 7 Grandes Senhores (MVPs) em masmorras calculadas pelo grafo de adjacências de mapas conectados.
* Um algoritmo de busca em largura (*Breadth-First Search*) calcula a menor distância em saltos (Taxi Distance) de cada mapa do mundo até os fragmentos mais próximos.
* O comando in-game `@cometa` ou o Radar de Fragmentos consulta a tabela `world_fragment_distances` para guiar os aventureiros.

### B. Miasma Progressivo e Conquista de Territórios
* O script `comet_system.txt` monitora a entrada de jogadores em mapas não purificados.
* O miasma atua em 9 ciclos de 20 segundos com perda exponencial de HP/SP e debuffs de mobilidade, tornando-se 100% letal no estágio 9.
* Ao mesmo tempo, o mapa gera aberrações corrompidas baseadas no Tier. Derrotar 15 aberrações purifica o mapa, grava o registro em `world_map_conquests`, desativa o miasma e concede **+50% EXP / +50% DROP** para todos os heróis.

### C. Campo de Aprendizes Narrativo
* A primeira NPC (`Shion#nv1`) é apresentada como a Bruxa do Cometa com sprite clássico (`4_F_NFDEADMGCIAN`), narrando a lore do colapso cósmico antes de adotar seu disfarce de instrutora.
* Os guardas de entrada do castelo oferecem bênçãos (Cura + Blessing 10 + Agi Up 10), kit de suprimentos do recruta e opções de transporte rápido para pular etapas e ingressar direto no combate.

# Ragnarok Docker v3 — "A Grande Travessia" (The Corrupted Crossing)

> **Documento de Especificação Técnica & Planejamento Conceitual**  
> **Tema**: Instância Roguelike Linear, Survival Horror Psicológico & Peregrinação de Borda a Borda.  
> **Referência Algorítmica**: Baseado em princípios de topologia e perigo de [`guiapq/ragnarok-online-randomizer-temp`](https://github.com/guiapq/ragnarok-online-randomizer-temp).

---

## 1. Identidade & Filosofia de Design (Survival Horror & Drama Psicológico / SAO)

### 1.1 A Premissa e a Lore
* **O Despertar do Veterano**: Você é um jogador de Ragnarok Online dos anos 2000 que passou incontáveis horas da sua vida explorando Rune-Midgarts. Por uma falha anômala nos servidores da simulação, sua mente é arrancada do mundo real e transferida para o corpo de um Aprendiz preso em uma Midgarts em colapso.
* **O Horror da Familiaridade Corrompida**: O terror não reside em sustos repentinos (*jump scares*), mas no **estranhamento grotesco de locais que marcaram a memória afetiva**:
  * A música clássica e alegre de Prontera está desacelerada, distorcida e ecoando em fontes secas repletas de cinzas.
  * NPCs icônicos perderam a sanidade ou viraram estátuas de cristal negro que sussurram fragmentos de logs de bate-papo de 2004 (*"Alguém me ajuda em Payon...", "Por que o botão de Desconectar sumiu?", "Saudades dos meus amigos..."*).
  * Criaturas simpáticas (Poring, Fabre, Lunático) sofreram mutações aberrantes, movendo-se com espasmos e ataques ferozes.
* **A Tensão de Sobrevivência (Estilo SAO)**:
  * Não há agentes Kafra fornecendo teletransporte fácil ou cura infinita.
  * Os recursos (poções, tochas, flechas) são escassos e precisam ser colhidos do chão ou saqueados de criaturas perigosas.
  * Morrer dentro da Fenda Corrompida é punitivo: resulta em perda de sanidade, penalidades de tempo ou recuo forçado para o início do setor.

---

## 2. Aproveitamento do Repositório `ragnarok-online-randomizer-temp`

O repositório [`ragnarok-online-randomizer-temp`](https://github.com/guiapq/ragnarok-online-randomizer-temp) oferece soluções algorítmicas prontas que resolvem os desafios centrais desta versão:

### A. Algoritmo de Topologia Espacial & Borda de Mapas (`world_map_grids.py` & `map.py`)
* **Mapeamento de Coordenadas de Portais**: Utiliza dados dos arquivos `.gat` (`gat_cache.json`) para determinar o centro geométrico e a caixa delimitadora de cada mapa.
* **Classificação por Borda (`get_warps_on_side`)**: Identifica com precisão se um portal do rAthena aponta para **Norte (+Y), Sul (-Y), Leste (+X) ou Oeste (-X)** em relação ao centro do mapa.
* **Aplicação na v3 (Spine Pathfinding)**:
  * Em vez de conexões desconexas, o gerador executa um algoritmo de busca de caminho em grafo (*Pathfinding*) sobre o mapa oficial de Midgarts, traçando uma linha ininterrupta de Leste a Oeste (ex: Comodo/Morroc $\rightarrow$ Prontera $\rightarrow$ Payon $\rightarrow$ Alberta) ou Norte a Sul (ex: Yuno/Aldebaran $\rightarrow$ Mjolnir $\rightarrow$ Prontera $\rightarrow$ Deserto).
  * O portal Leste do mapa anterior sempre conecta diretamente ao portal Oeste do mapa seguinte. O jogador fisicamente caminha pelo continente de um extremo ao outro.
  * **Fechamento de Rotas Secundárias**: Portais que levariam a caminhos paralelos são identificados pelo parser e selados no script de instância com barreiras de colisão (*"Uma névoa impenetrável bloqueia este desvio"*).

### B. Curva Matemática de Perigo por Distância (`mobs_rando.py` -> `set_danger_ratings()`)
* **Modelo Original**: O script calcula o perigo (`danger rating`) para cada mapa proporcionalmente à distância em pixels/coordenadas em relação ao ponto de origem, aplicando multiplicadores de profundidade em masmorras.
* **Aplicação na v3 (Curva Linear de Nível)**:
  * Ao longo do corredor de $N$ mapas da instância, o nível de perigo é mapeado de forma suave e contínua:
    $$\text{Danger}(\text{mapa}_i) = \text{Level}_{\text{min}} + \left(\frac{i}{N - 1}\right)^{1.2} \times (\text{Level}_{\text{max}} - \text{Level}_{\text{min}})$$
  * Isso garante que o Setor 0 inicie com perigo para Aprendizes (Lv 1–15), suba gradativamente nos campos intermediários (Lv 25–70) e atinja o ápice de pesadelo nos setores finais (Lv 85–98).

### C. Geração Procedural de Spawns por Faixa de Nível (`mobs_rando.py` -> `add_monster()`)
* **Modelo Original**: Indexa todos os monstros do `mob_db` por nível (`monsters_levels[level]`) e seleciona amostras dentro do intervalo $[Danger - 10, Danger + 5]$.
* **Aplicação na v3 (Filtro Temático de Horror)**:
  * O algoritmo de geração é adaptado com filtros estéticos: seleciona prioritariamente raças *Morto-Vivo, Demônio, Amorfo, Inseto* e elementos *Sombrio/Maldito*.
  * Monstros clássicos de cada faixa recebem modificadores de IA e prefixos corrompidos (*"Eco de Poring", "Memória de Esqueleto", "Pesadelo Rastejante"*), mantendo a progressão balanceada sem necessidade de balancear à mão dezenas de mapas.

### D. Reprodutibilidade com Seed Determinística (`world_seed.py` + `crc32`)
* Todo o pipeline é atrelado ao `WORLD_SEED_NUMERIC`.
* Uma seed determina se a rota do mês será Leste-Oeste ou Norte-Sul, quais mapas específicos farão parte do corredor e quais aberrações surgirão.
* Isso viabiliza torneios de speedrun e temporadas descartáveis idênticas para todos os participantes de uma mesma rodada.

---

## 3. Arquitetura Técnica no rAthena

Para que cada jogador ou grupo vivencie sua jornada isolada e imersiva:

1. **Definição em `instance_db.txt`**:
   * O rAthena suporta o encadeamento dinâmico de mapas normais através de instâncias:
     ```txt
     // ID,Name,LimitTime,IdleTimeOut,EnterMap,EnterX,EnterY,Map2,...,MapN
     30,Corrupted Midgard,43200,1800,1#cmd_fild01,360,200,1#cmd_fild02,1#gef_fild07,1#prt_fild08,1#pay_fild04,1#alb_fild01,1#final_sanctum
     ```
   * Em runtime, o servidor instancia réplicas dos mapas oficiais com o identificador único `instance_id#` (ex: `1#prt_fild08`), garantindo total independência do mapa público.

2. **Criação de Instância Solo / Party (`instance_create`)**:
   * O ponto de partida (NPC do Despertar) inicializa a instância:
     ```c
     .@inst_id = instance_create("Corrupted Midgard", IM_CHAR, getcharid(0));
     if (.@inst_id < 0) {
         mes "A fenda dimensional está sobrecarregada. Tente novamente.";
         close;
     }
     instance_enter("Corrupted Midgard");
     ```

3. **Portais Condicionais (`instance_warp`)**:
   * NPCs invisíveis com gatilho de colisão (`OnTouch`) controlam o avanço de um mapa para o outro:
     ```c
     // Bloqueio de avanço prematuro
     if (BaseLevel < .min_level_next_sector) {
         dispbottom "A névoa deste portal queima sua carne. Força insuficiente (Requer Nível " + .min_level_next_sector + "+).";
         end;
     }
     warp instance_mapname("proximo_mapa"), .to_x, .to_y;
     ```

---

## 4. Estrutura dos Setores da Peregrinação (Nível 1 ao 99/70)

```
[Setor 0: O Despertar]   ──>   [Setor 1: Borda da Névoa]   ──>   [Setor 2: Terra de Ninguém]
   (Lv 1–15 / Praia)               (Lv 15–30 / Caverna)               (Lv 30–50 / Campos)
           │
           ▼
[Setor 3: Cidade Fantasma] ──>   [Setor 4: Vale dos Lamentos] ──>   [Setor 5: Portão do Abismo]
   (Lv 50–70 / Ruínas)             (Lv 70–85 / Floresta)             (Lv 85–98 / Pântano/Glast)
           │
           ▼
[Setor 6: O Altar da Transcendência]
   (Lv 99/70 EXCLUSIVO / O Núcleo do Mundo)
```

### Detalhamento dos Setores:

| Setor | Faixa de Nível | Ambiente / Inspiração | Atmosfera & Horror Psicológico | Mecânica de Jogo |
|---|---|---|---|---|
| **0: O Despertar** | Lv 1–15 | Borda Costeira ou Deserto | Mar escuro e agitado, chuva incessante, destroços de navios. Sons de passos na areia. | Coleta de lascas de madeira e ervas rudimentares para sobreviver como Aprendiz. |
| **1: Borda da Névoa** | Lv 15–30 | Cavernas periféricas ou ravinas | Névoa espessa, visão periférica limitada (`SC_BLIND` reduzido). Gemidos distantes. | Primeiro abrigo seguro: um fogueira apagada com um NPC caçador moribundo. |
| **2: Terra de Ninguém** | Lv 30–50 | Campos abertos devastados | Céu crepuscular estático. Ventania seca. Matilhas de predadores famintos e agressivos. | Necessidade de controle de puxadas (*kiting*); monstros perseguem por longas distâncias. |
| **3: A Cidade Fantasma** | Lv 50–70 | Prontera, Geffen ou Morroc em ruínas | Casas calcinadas, lojas reviradas, NPCs congelados como estátuas de pedra negra. | **Guardião do Portão**: Para abrir a passagem da cidade, deve-se derrotar o espectro do antigo Chefe da Guarda. |
| **4: Vale dos Lamentos** | Lv 70–85 | Floresta profunda ou catacumba | Sons de choro, armadilhas no solo, labirintos estreitos e claustrofóbicos. | Morte neste setor pune o jogador recuando-o até a fogueira do setor anterior. |
| **5: O Portão do Abismo** | Lv 85–98 | Arredores de Glast Heim ou Santuário | Trevas absolutas, descargas elétricas no horizonte, criaturas de nível 90+ com habilidades de MVP. | A pressão psíquica drena SP/HP aos poucos se o jogador permanecer parado. |
| **6: O Altar do Fim** | **Lv 99/70** | Sala do Trono / Raiz da Yggdrasil | Silêncio cósmico absoluto, gravidade alterada, fragmentos de código e dados flutuando. | **Bloqueio Absoluto 99/70**: O portal desintegra qualquer um que não possua a Aura de Transclasse. |

---

## 5. O Clímax & Objetivo Final (Exclusivo 99/70)

### 5.1 A Justificativa Narrativa da Barreira 99/70
O núcleo da corrupção é protegido pela **"Radiação do Vácuo"**.
* Personagens comuns (Classes 1 e 2 normais ou não-transcendidas) sofrem colapso mental imediato ao se aproximarem da barreira, tendo sua memória apagada.
* Somente uma alma que realizou o renascimento sagrado de Valhalla, dominou os 70 níveis de conhecimento de sua classe transclasse e manifestou a **Aura Suprema (99/70)** possui densidade espiritual suficiente para suportar a anomalia sem enlouquecer.

### 5.2 O Confronto: "O Guardião da Memória"
Ao atravessar a barreira com 99/70:
* O jogador confronta uma manifestação distorcida do próprio servidor: uma sombra que espelha sua própria classe e build, utilizando armas lendárias e habilidades equivalentes.
* O combate exige domínio técnico da classe (posicionamento, troca de elementos, uso de itens consumíveis acumulados na travessia).

### 5.3 As Escolhas do Desfecho (Endgame)
Ao derrotar a entidade final:
1. **Opção A: O Protocolo de Desconexão (Good Ending / Speedrun Finish)**:
   * O jogador aciona o terminal central e puxa a chave do servidor, libertando todas as almas aprisionadas e encerrando a simulação.
   * O tempo total da run é registrado oficialmente no placar `/scoreboard` como "Travessia Concluída".
2. **Opção B: O Novo Núcleo (New Game+ / Modo Ciclo Eterno)**:
   * O jogador escolhe fundir sua alma com o servidor para manter o mundo existindo.
   * Libera uma relíquia permanente para a conta e reinicia a instância com novos afixos de pesadelo (dano aumentado dos monstros, escassez redobrada).

---

## 6. Roadmap de Implementação para a Versão 3

```
[FASE 1: Topologia & Rota Contígua]
 ├── Extração dos pontos cardeais de warps (baseado em world_map_grids.py)
 ├── Algoritmo de Pathfinding para rotas direcionadas (Oeste -> Leste ou Norte -> Sul)
 └── Geração automatizada da cadeia de mapas no instance_db.txt

[FASE 2: Motor de Spawns de Horror & Perigo]
 ├── Curva de perigo por nível (Danger Curve) mapeada de Lv 1 a Lv 98
 ├── Seleção de monstros por faixa de nível com filtro de raças sombrias
 └── Geração de scripts de monstros para a instância (prefixos de corrupção)

[FASE 3: Scripting e Mecânicas de Jogo no rAthena]
 ├── Script mestre da instância (instance_create, instance_enter, temporizador)
 ├── Barreiras de colisão com verificação de nível mínimo entre setores
 ├── Efeitos imersivos de ambientação (noite constante, clima de cinzas, mensagens de terror)
 └── O Selo da Transcendência: verificação rigorosa de Base 99 e Job 70 no portal final

[FASE 4: Integração com Painel & Leaderboard]
 ├── Telemetria de conclusão da instância vinculada ao banco MySQL
 ├── Atualização do painel Filament com o ranking da Grande Travessia
 └── Visualizador visual do corredor da seed no painel web
```

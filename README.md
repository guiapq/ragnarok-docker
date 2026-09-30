# RagnaRogue — Servidor Procedural Roguelike & Client Web (v3.0)

Este repositório fornece uma stack completa e containerizada para rodar um servidor de **MMORPG clássico 2D (rAthena Pré-Renewal)** integrado a um **cliente web moderno (HTML5/WebAssembly)** e a um **painel de controle (Laravel Filament)**.

O ecossistema transforma o MMORPG clássico em uma experiência **roguelike cósmica, reproduzível, solo-self-found e efêmera**, onde mundos inteiros são gerados deterministicamente a partir de uma **Seed**.

---

## 🌌 A Lore do Mundo: A Queda do Cometa Negro

Há eras, uma calamidade estelar rasgou os céus de Midgard: o **Cometa Negro** colidiu contra o cerne do mundo, fraturando o tecido do espaço e do tempo.

1. **Os 7 Fragmentos Cósmicos**: O impacto despedaçou o cometa em 7 núcleos de energia monumental (*Arcturus, Scheat, Betelgeuse, Cor Caroli, Acrux, Alnair e Mira*). Essas entidades foram devoradas e guardadas por Grandes Senhores do Mal (MVPs/Lordes ancestrais) nos calabouços mais profundos do mundo.
2. **O Miasma Venenoso do Cometa**: Das crateras brotou uma névoa púrpura asfixiante que corrompe cada território selvagem fora das capitais protegidas. Aventureiros que vagam por terras amaldiçoadas sofrem estágios progressivos de envenenamento e sucumbem em **3 minutos** caso o mapa não seja libertado.
3. **Conquista e Purificação de Territórios**: Para dissipar a névoa, os bravos heróis devem purgar as aberrações corrompidas que assombram o mapa. Ao erguer a bandeira da conquista, a névoa se dissipa e todos os aventureiros no mapa recebem **+50% de Experiência** e **+50% de Drop**!
4. **Topologia Distorcida**: A colisão deformou os portais do continente. Em cada nova era (Seed), uma nova rota entre cidades e campos se manifesta com trancas mágicas, auras coloridas e caminhos imprevisíveis.
5. **As Relíquias Sagradas (Tier 4)**: Apenas reunindo os artefatos divinos das profundezas de Midgard os heróis poderão dissipar a corrupção eterna do Cometa.

---

## 🧭 Filosofia & Mecânicas da Versão 3.0

1. **Geração de Novo Mundo em 1 Comando (`./novo_mundo.sh`)**:
   - Cria uma nova seed procedural (ou recebe uma personalizada).
   - Reconstrói a conta `roadmin` (GM 99) e **14 contas de teste pré-configuradas** (uma para cada classe, com equipamentos e habilidades prontas).
   - Recria toda a arquitetura de dados (`data/`), drops, lojas, topologia de mapas, os 7 Fragmentos do Cometa e as cartas revitalizadas.
2. **Sistema de Miasma Dinâmico & Agressivo**:
   - Mapas selvagens não purificados ativam o Miasma do Cometa (9 estágios a cada 20 segundos). O 9º estágio é fatal (morte certa em 3 minutos).
   - Aberrações agressivas corrompidas (Familiares, Esqueletos, Zumbis, Múmias, Ísis, Raydrics) surgem em mapas com névoa ativa.
   - Ao completar 15 abates de criaturas corrompidas, a terra é purificada, os monstros invasores são banidos e o mapa ganha bônus global de **+50% EXP / +50% DROP**.
3. **Topologia de Campanha Roguelike v4**:
   - 4 Tiers de Campanha determinísticos pela Seed: **Tier 1 (Inicial) ➔ Tier 2 (Intermediária) ➔ Tier 3 (Fronteira) ➔ Tier 4 (Capital Clímax)**.
   - 44 rotas de portais geradas proceduralmente com auras visuais e restrições de nível.
   - 476 pontos determinísticos de spawn para teleporte (`@warp` e portais) direto para os centros de vilarejos.
4. **Radar de Fragmentos do Cometa (`@cometa`)**:
   - O comando `@cometa` ou o NPC Radar em tempo real calcula a distância em saltos (Taxi Distance) do jogador até cada um dos 7 Fragmentos do Cometa pelo grafo de mapas conectados.
5. **Rebalanceamento de Cartas Esquecidas**:
   - Mais de 123 cartas clássicas subutilizadas foram revitalizadas em `tools/enhance_unpopular_cards.py`, recebendo bônus de ataque, dano elemental, sustain de SP/HP e escalonamento real.
6. **Campo de Aprendizes Narrativo & Tático**:
   - **Bruxa Shion**: A primeira NPC do jogo apresenta a lore completa do Cometa na 1ª interação, e atua como tutora no diálogo subsequente.
   - **Sentinela do Castelo**: Fornece cura total, bênçãos de combate (Bênção Nv 10 + Aumentar Agilidade Nv 10) e o Kit de Suprimentos do Recruta (100 Poções, 20 Asas de Mosca, 5 Asas de Borboleta).
   - **Batedor Veterano**: Atalho tático com teleporte direto para o Castelo de Treinamento, Campo Prático de Monstros ou diretamente para Prontera.
7. **Lojas de Conveniência nas 23 Cidades**:
   - Todas as capitais contam com NPCs externos de Utilidades e Equipamentos a curta distância dos pontos centrais de respawn.

---

## 🏗️ Arquitetura Geral do Sistema

A stack é orquestrada via **Docker Compose** e composta por 6 microsserviços integrados em rede bridge:

```
                                  [ NAVEGADOR WEB ]
                                   /      |      \
                                  /       |       \
               :8000             /      :8001      \            :8080
                 |              /         |         \             |
                 v             v          v          v            v
        +-------------------+    +--------------------+    +------------------+
        |   ragnarok-panel  |    |     robrowser      |    |    phpMyAdmin    |
        |  (Painel Web /    |    | (Cliente Web HTML5 |    | (Gerenciador SQL)|
        |  Laravel Filament)|    | + wsProxy na 5999) |    +--------+---------+
        +---------+---------+    +---------+----------+             |
                  |                        |                        |
                  |                        | :5999 (ws)             |
                  |                        v                        |
                  |              +--------------------+             |
                  |              |  ragnarok-server   |             |
                  |              | (rAthena Pre-Re:   |<------------+
                  |              |  Login:6900        |
                  |              |  Char:6121         |
                  |              |  Map:5121)         |
                  |              +---------+----------+
                  |                        |
                  +----------+             | :3306
                             |             |
                             v             v
                       +-------------------------+
                       |       ragnarok-db       |
                       |    (MariaDB 10.5)       |
                       +-------------------------+
```

### Detalhamento dos Serviços

| Container | Imagem / Base | Portas | Função |
| :--- | :--- | :--- | :--- |
| **`robrowser`** | Node 20 / Cliente Web | `8001` (HTTP), `5999` (WSS) | Cliente do jogo no navegador com suporte a Lua WASM e bridge WebSocket para o emulador. |
| **`ragnarok-server`** | Debian rAthena custom | `6900`, `6121`, `5121` | Servidor rAthena Pré-Renewal com patches roguelike, sistema de cometa e miasma. |
| **`ragnarok-panel`** | PHP 8.2 FPM + Nginx | `8000` | Painel de controle web: gestão de contas, banco procedural e rankings de temporada. |
| **`ragnarok-db`** | MariaDB 10.5 | `3306` | Banco relacional com esquemas rAthena, tabelas de controle de conquistas e fragmentos. |
| **`ragnarok-phpmyadmin`**| phpMyAdmin oficial | `8080` | Interface gráfica para administração direta das tabelas do banco. |
| **`ragnarok-registry`**| Docker Registry v2 | `5000` | Registry local de imagens para builds e deploys distribuídos rápidos. |

---

## 🚀 Como Executar

### 1. Início Rápido (Gerar Novo Mundo)

Para gerar uma nova era do mundo com todos os dados reconstruídos do zero:

```bash
# Gera um mundo procedural com seed aleatória
./novo_mundo.sh

# Ou especifique sua própria seed
./novo_mundo.sh minha-seed-epica-42
```

O script cuidará de:
* Limpar personagens antigos e resetar a economia;
* Recriar a conta `roadmin` (GM 99) e as 14 contas de teste por classe;
* Regenerar topologia de campanha (v4), os 7 Fragmentos do Cometa e as cartas revitalizadas;
* Executar as migrações no MariaDB e no Laravel Filament;
* Reiniciar os containers com a stack pronta para jogar.

---

### 2. Acessos do Ambiente

Após inicializar a stack:
* 🎮 **Jogar no Navegador:** [`http://localhost:8001`](http://localhost:8001)
* 🌐 **Painel de Controle:** [`http://localhost:8000`](http://localhost:8000)
* 🗄️ **phpMyAdmin:** [`http://localhost:8080`](http://localhost:8080)

---

## 🔑 Credenciais de Acesso

### A. Administrador (Game Master)
* **Login:** `roadmin`
* **Senha:** `roadmin`
* **Nível GM:** `99` (Acesso total a `@warp`, `@item`, `@cometa`, etc.)

### B. Contas de Teste Pré-Configuradas (14 Classes)
Todas as contas utilizam a senha padrão: **`teste123`**

| Conta | Classe | Perfil de Teste |
| :--- | :--- | :--- |
| `teste_swordie` | Espadachim | Combate corporal corpo-a-corpo |
| `teste_mage` | Mago | Conjuração e dano elemental |
| `teste_archer` | Arqueiro | Ataque à distância e agilidade |
| `teste_merchant` | Mercador | Comércio e carrinho de mão |
| `teste_acolyte` | Noviço | Suporte sagrado e cura |
| `teste_thief` | Gatuno | Furtividade, esquiva e ataques críticos |
| `teste_knight` | Cavaleiro | Tanque com montaria Peco Peco |
| `teste_wizard` | Bruxo | Dano em área em grande escala |
| `teste_blacksmith`| Ferreiro | Forja, buffs de combate e velocidade |
| `teste_hunter` | Caçador | Armadilhas e ataque combinado com Falcão |
| `teste_priest` | Sacerdote | Exorcismo e suporte de alta potência |
| `teste_assassin` | Assassino | Dano crítico duplo e veneno |
| `teste_gunslinger`| Justiceiro | Combate com armas de fogo |
| `teste_extended` | Taekwon / Ninja | Artes marciais e técnicas ninjas |

Para mais detalhes, consulte [docs/CREDENTIALS.md](file:///home/luiz/Projetos/ragnarok-docker/docs/CREDENTIALS.md).

---

## 📋 Comandos Rápidos do Makefile

| Comando | Descrição |
| :--- | :--- |
| `make` | Prepara o ambiente e inicia os serviços em segundo plano |
| `make prepare` | Prepara dependências, arquivos `.env` e popula a runtime `data/` |
| `make doctor` | Valida pré-requisitos, integridade das bases e volumes montados |
| `make world SEED=x`| Recria o mundo procedural com a seed indicada |
| `make build` | Compila as imagens Docker com cache otimizado |
| `make up` / `make down`| Inicia ou encerra os microsserviços da stack |
| `make logs` | Visualiza os logs em tempo real |
| `make ps` | Exibe o status e healthcheck de cada container |
| `make prune` | Remove containers órfãos, volumes temporários e cache de build |

---

## 📜 Isenção de Responsabilidade (Disclaimer)

"This project is an open-source emulator environment and procedural modification tool. All third-party game assets, multimedia, and trademarks belong to their respective copyright holders and are NOT included in this repository."

"Este projeto é um ambiente de emulação e ferramenta de modificação procedural de código aberto. Todos os recursos visuais, marcas e arquivos multimídia de terceiros pertencem aos seus respectivos detentores de direitos autorais e NÃO estão incluídos neste repositório."

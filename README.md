# RagnaRogue — Servidor Procedural Roguelike & Client Web (v2.0 Estável)

Este repositório fornece uma stack completa e containerizada para rodar um servidor de **MMORPG clássico 2D (rAthena Pré-Renewal)** integrado a um **cliente web moderno (HTML5/WebAssembly)** e a um **painel de controle (Laravel Filament)**.

O ecossistema é projetado para transformar o MMORPG clássico em uma experiência **roguelike, reproduzível, solo-self-found e efêmera**, onde mundos inteiros são gerados deterministicamente a partir de uma **Seed**.

---

## 🧭 Filosofia do Projeto

O objetivo deste projeto vai além de simplesmente executar o emulador em Docker:

1. **Loop Roguelike (12 Horas):** Viabilizar progressão completa Solo Self-Found (SSF) sem grind punitivo. Monstros fornecem consumíveis, minérios de refino e equipamentos escalonados pelo seu tier de nível.
2. **Mundos Baseados em Seed:** Toda a distribuição de drops, lojas e propriedades procedurais de itens é calculada de forma determinística por uma única chave (ex: `WORLD_SEED=zawarudo`).
3. **Zero-Install (Client Web Integrado):** O jogador conecta diretamente pelo navegador via cliente web integrado com engine Lua WebAssembly (`liblua5.1.wasm`), decodificação de strings e banco de dados localizado em português (PT-BR).
4. **Camadas Claras de Separação:** Separação rígida entre bases imutáveis (`data_base/`, `cronus_base/`, `robrowser_base/`) e os arquivos modificados em runtime pelo gerador (`data/`).
5. **Automação Total e Portabilidade:** Inicialização com um único comando, cache de pacotes local e scripts utilitários de suporte e manutenção.

---

## 🏗️ Arquitetura Geral do Sistema

A stack é orquestrada via **Docker Compose** e composta por 6 microsserviços integrados em uma rede bridge (`ragnarok-net`):

```
                                  [ NAVEGADOR WEB ]
                                   /      |      \
                                  /       |       \
               :8000             /      :8001      \            :8080
                 |              /         |         \             |
                 v             v          v          v            v
        +-------------------+    +--------------------+    +------------------+
        |   ragnabraza-cp   |    |     robrowser      |    |    phpMyAdmin    |
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
                       |    (MariaDB 10.11)      |
                       +-------------------------+
```

### Detalhamento dos Serviços

| Container | Imagem / Base | Portas | Função |
| :--- | :--- | :--- | :--- |
| **`robrowser`** | Node 20 / Cliente Web | `8001` (HTTP), `5999` (WSS) | Cliente do jogo no navegador com suporte a Lua WASM e bridge WebSocket para o emulador. |
| **`ragnarok-server`** | Debian rAthena custom | `6900`, `6121`, `5121` | Servidor rAthena Pré-Renewal com patches para taxas roguelike, spawns e scripts customizados. |
| **`ragnabraza-cp`** | PHP 8.2 FPM + Nginx | `8000` | Painel de controle web: cadastro de contas, ranking de torneios MVP, speedrun e visualizador de personagens. |
| **`ragnarok-db`** | MariaDB 10.11 | `3306` | Banco relacional com esquemas rAthena, tabelas de controle de contas e dados de torneio. |
| **`ragnarok-phpmyadmin`**| phpMyAdmin oficial | `8080` | Interface gráfica para administração direta das tabelas do banco. |
| **`ragnarok-apt-cache`** | apt-cacher-ng | `3142` (interno) | Cache local de pacotes Debian para permitir rebuilds de containers quase instantâneos. |

---

## 🚀 Instruções de Uso

### 1. Pré-requisitos
- **Docker** 24.0+ e **Docker Compose** v2
- **GNU Make**
- Portas disponíveis: `8000`, `8001`, `8080`, `3306`, `6900`, `6121`, `5121`, `5999` e `5000` (Registry)

---

### 🌟 2. Deploy Preferencial e de Alta Performance (Makefile + Registry Local)

Este é o **método recomendado**. Ele utiliza o container de **Registry Privado (porta 5000)** integrado para versionar as imagens compiladas localmente, permitindo builds ultra-rápidos, reutilização de cache e deploy desacoplado entre máquinas da rede:

```bash
# 1. Valide os pré-requisitos do ambiente
make doctor

# 2. Inicialize o registry local de imagens
make registry-up

# 3. Compile as imagens otimizadas com salvaguardas de rede
make build

# 4. Publique as imagens no registry local
make push-images

# 5. Gere o mundo procedural com a semente desejada
make world SEED=zawarudo

# 6. Inicialize a stack completa
make up
```

> [!TIP]
> **Deploy Distribuído (Host de Build ➔ Host de Produção):**
> Você pode compilar as imagens em uma máquina potente de desenvolvimento e enviá-las diretamente para o servidor de destino na rede:
> ```bash
> make push-images REGISTRY=SEU_IP_DO_SERVIDOR:5000
> ```

---

### 📋 Comandos Rápidos do Makefile

| Comando | Descrição |
| :--- | :--- |
| `make doctor` | Verifica dependências, arquivos `.env` e integridade das pastas base |
| `make registry-up` | Inicializa o container de Docker Registry local (`:5000`) |
| `make build` | Compila os containers (`rathena`, `robrowser`, `panel`) com timeouts estritos |
| `make push-images` | Tagueia e envia as imagens prontas para o registry (`REGISTRY=host:5000`) |
| `make world SEED=x` | Recria o mundo a partir da base imutável e aplica a seed procedural |
| `make up` | Inicia todos os microsserviços em segundo plano |
| `make down` | Para todos os containers do ecossistema |
| `make logs` | Acompanha os logs ao vivo em tempo real |
| `make ps` | Exibe o status e healthcheck de cada serviço |

---

### 3. Acessos do Ambiente
Após subir a stack (`make up`):
* 🎮 **Jogar no Navegador:** [`http://localhost:8001`](http://localhost:8001)
* 🌐 **Painel de Controle:** [`http://localhost:8000`](http://localhost:8000)
* 🗄️ **phpMyAdmin:** [`http://localhost:8080`](http://localhost:8080)

---

### 4. Deploy Direto Alternativo (Docker Compose puro)
Caso prefira não utilizar o Makefile:
```bash
docker compose up -d --build
./new_world.sh zawarudo --force
```

---

## 🎲 Geração Procedural e Seeds

O servidor suporta a regeneração completa da economia e drops com base em sementes de mundo:

### Gerar Novo Mundo por Seed
```bash
# Define a semente desejada no .env ou passe diretamente
WORLD_SEED=zawarudo ./scripts/randomize_world.sh
```

O script automatiza o ciclo completo:
1. **Sanitização de Drops (`tools/randomize_drops.py`):** Modifica os 8 slots de loot dos 1.008 monstros com garantia de 100% de itens localizados em português (PT-BR) e relevância para gameplay.
2. **Distribuição de Lojas (`tools/randomize_shops.py`):** Vendedores de consumíveis e equipamentos recebem estoques rotativos pelo tier da cidade.
3. **Compilação de Itens Procedurais (`tools/generate_item_info_lua.py`):** Gera o `client/System/itemInfo.lua` com propriedades coloridas no client web.
4. **Recarregamento Automático:** Notifica o rAthena (`map-server`) para carregar as tabelas sem necessidade de derrubar o banco de dados.

---

## 🛡️ Sanitização PT-BR & Correção de UI

Na versão 2.0, foi cortado o mal pela raiz em relação a itens bugados:
- **Base de Itens em Português:** Extraídos 9.521 itens da base traduzida do [client/System/itemInfo.lub](file:///home/luiz/Projetos/ragnarok-docker/client/System/itemInfo.lub).
- **Blacklist de Itens Obsoletos:** Mais de 7.400 itens obsoletos de eventos antigos ou de teste (ex: cartões sem efeito, consumíveis vazios) são estritamente proibidos de dropar ou aparecer em NPCs.
- **Tratamento de Descrições no Cliente Web:** O carregador Lua WASM foi atualizado para que itens sem bloco de texto longo não se tornem slots invisíveis (`: 1 ea`).

---

## 🔑 Credenciais Padrão de Desenvolvimento

* **Banco de Dados (MariaDB):**
  * Host: `localhost:3306` (interno: `ragnarok-db`)
  * Usuário: `ragnarok` / Senha: `ragnarok` (Root: `root`)
  * Database: `ragnarok`
* **Contas de Teste no Jogo:**
  * Administrador: `admin` / `admin`
  * Usuários de Teste: `teste1`, `teste2` / `teste1`

Para mais detalhes e portas de depuração, consulte [docs/CREDENTIALS.md](file:///home/luiz/Projetos/ragnarok-docker/docs/CREDENTIALS.md).

---

## 📜 Isenção de Responsabilidade (Disclaimer)

"This project is an open-source emulator environment and procedural modification tool. All third-party game assets, multimedia, and trademarks belong to their respective copyright holders and are NOT included in this repository."

"Este projeto é um ambiente de emulação e ferramenta de modificação procedural de código aberto. Todos os recursos visuais, marcas e arquivos multimídia de terceiros pertencem aos seus respectivos detentores de direitos autorais e NÃO estão incluídos neste repositório."

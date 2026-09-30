# Instalação

Este projeto executa um servidor de **MMORPG clássico baseado em rAthena** utilizando **Docker** e permite gerar mundos procedurais por seed.

## Matriz de compatibilidade (recomendada)

| Componente | Versão recomendada |
| --- | --- |
| Docker Engine | 24+ |
| Docker Compose (plugin) | 2.20+ |
| Python | 3.10+ |
| Sistema operacional | Ubuntu 22.04+ / Debian 12+ |

## Requisitos

Antes de começar, instale:

- Docker
- Docker Compose
- Git
- Python 3

Ubuntu / Debian:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin git python3
```

## 1. Clonar o repositório

```bash
git clone https://SEU_REPOSITORIO/ragnarok-docker.git
cd ragnarok-docker
```

## 2. Preparação do ambiente (Automática)

Você pode preparar tudo com um único comando:

```bash
make prepare
```
> O script detecta automaticamente se o servidor Git local (**momo**) está disponível para clone rápido ou se deve usar o GitHub, cria os arquivos `.env` se não existirem e popula a base em `data/`.
> *(Nota: Rodar `make` ou `make up` já dispara o `make prepare` automaticamente caso seja a primeira vez).*

## 3. Validar ambiente

```bash
make doctor
```

## 4. Subir o servidor

```bash
make up
```

## 5. Gerar um novo mundo procedural (Recomendado)

O script unificado `./novo_mundo.sh` zera o banco, reconstrói o `roadmin` (GM 99), as 14 contas de teste por classe, re-randomiza toda a arquitetura procedural e sobe os containers automaticamente:

```bash
# Gera mundo com seed aleatória
./novo_mundo.sh

# Ou especifique sua seed personalizada
./novo_mundo.sh minha-seed-epica
```

## 6. Acessos do Ambiente

- **Cliente do Jogo no Navegador:** `http://localhost:8001`
- **Painel de Controle (Filament):** `http://localhost:8000`
- **phpMyAdmin (Banco SQL):** `http://localhost:8080`

Para expor em rede local, defina no `.env`:

```env
BIND_IP=0.0.0.0
```

## Comandos úteis

```bash
./novo_mundo.sh              # Gera novo mundo do zero com 1 comando
make up                      # Inicia os serviços em segundo plano
make down                    # Para todos os containers
make logs                    # Visualiza logs em tempo real
make ps                      # Verifica o status dos containers
make doctor                  # Executa diagnóstico do ambiente
```

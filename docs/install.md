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

## 6. Gerar um mundo procedural

```bash
./new_world.sh minha-seed --force
```

> `--force` é obrigatório por segurança, pois a operação recria `data/db`, `data/npc` e `data/conf`.

## 7. Acessos

- Cliente web / database: `http://127.0.0.1:8003`
- phpMyAdmin: `http://127.0.0.1:8080`

Para expor em rede local, defina no `.env`:

```env
BIND_IP=0.0.0.0
```

## Comandos úteis

```bash
make up
make down
make world SEED=wolfie-maxxer
make logs
make ps
```

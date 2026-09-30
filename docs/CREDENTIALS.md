# Credenciais do Sistema e Recuperação de Desastre (RagnaRogue)

Este documento centraliza todas as credenciais administrativas fixas, chaves de segurança do banco de dados e procedimentos de recuperação de perda de senhas da infraestrutura.

---

## 1. Conta de Administrador GM Fixa (In-Game & Painel Web)

O sistema provisiona e garante automaticamente a conta administrativa no boot do servidor (`start.sh` e `init.sql`).

| Atributo | Valor | Descrição |
| :--- | :--- | :--- |
| **Login / Usuário** | `roadmin` | Usuário fixo do Game Master / Administrador |
| **Senha** | `roadmin` | Senha padrão inicial |
| **Nível GM (`group_id`)** | `99` | Acesso irrestrito a comandos in-game (`@warp`, `@item`, etc.) |
| **Painel Web (Login)** | `http://localhost:8000/login` | Acesso como Staff GM |
| **Painel Admin (Filament)** | `http://localhost:8000/admin` | Gestão completa de Usuários, Personagens e Torneios |
| **E-mail Cadastrado** | `admin@ragnarogue.local` | E-mail para recuperação no Fortify/Jetstream |

> [!IMPORTANT]
> A conta `roadmin` é protegida com `ON DUPLICATE KEY UPDATE` em tempo de inicialização, garantindo que mesmo após wipes de banco ou resets parciais, o acesso de emergência seja restaurado.

---

## 2. Contas de Teste Pré-Configuradas (14 Classes - Níveis e Equipamentos)

O script `./novo_mundo.sh` e a migração de seed do painel Laravel recriam automaticamente 14 contas de teste especializadas prontas para jogar e validar o balanceamento de cada classe:

| Conta / Login | Senha | Classe Inicial | Equipamentos & Habilidades |
| :--- | :--- | :--- | :--- |
| `teste_swordie` | `teste123` | Espadachim | Espada de duas mãos, poções e habilidades de combate |
| `teste_mage` | `teste123` | Mago | Cajado arcano, poções de SP e magias elementais |
| `teste_archer` | `teste123` | Arqueiro | Arco composto, flechas elementais e olho de águia |
| `teste_merchant` | `teste123` | Mercador | Machado, carrinho de mão e habilidades de comércio |
| `teste_acolyte` | `teste123` | Noviço | Maça sagrada, bênção, cura e agilidade |
| `teste_thief` | `teste123` | Gatuno | Adagas, furto, esconderijo e esquiva |
| `teste_knight` | `teste123` | Cavaleiro | Montaria Peco Peco, lança pesada e impacto explosivo |
| `teste_wizard` | `teste123` | Bruxo | Magias de área avançadas (Nevasca, Chuva de Meteoros) |
| `teste_blacksmith`| `teste123` | Ferreiro | Martelos de forja, adrenalina pura e poder supremo |
| `teste_hunter` | `teste123` | Caçador | Falcão adestrado, armadilhas e rajada de flechas |
| `teste_priest` | `teste123` | Sacerdote | Magnus Exorcismus, santuário e suporte divino |
| `teste_assassin` | `teste123` | Assassino | Katar de duas lâminas, lâminas destruidoras e veneno |
| `teste_gunslinger`| `teste123` | Justiceiro | Revólveres, rifle de precisão e munição balística |
| `teste_extended` | `teste123` | Taekwon / Ninja | Habilidades marciais, chutes aéreos e jutsus |

---

## 3. Banco de Dados MariaDB

As credenciais ativas são lidas do arquivo `.env` na raiz do projeto. Caso o arquivo seja corrompido ou perdido, as seguintes chaves de segurança randômicas estão definidas como fallback nos Dockerfiles:

### A. Credenciais em Uso (`.env`)
- **Host Interno:** `db` (Porta: `3306`)
- **Database:** `ragnarok`
- **Usuário da Aplicação:** `ragnarok`
- **Senha da Aplicação:** `ragnarok`
- **Usuário Root:** `root`
- **Senha Root:** `root`
- **Interface phpMyAdmin:** `http://localhost:8080` (usuário: `root`, senha: `${MYSQL_ROOT_PASSWORD}`)

### B. Credenciais Fallback de Segurança (Dockerfiles)
Definidas em `docker/rathena/Dockerfile` e `docker/panel/Dockerfile`:
- **Default App User:** `ragnarok`
- **Default App Password:** `rR_SecApp#2026_8e6d2c`
- **Default Root Password:** `rR_SecRoot#2026_9f7b3a`

---

## 4. Procedimentos de Emergência e Recuperação

### Como resetar a senha da conta `roadmin` manualmente via CLI
Se por algum motivo a senha for alterada e esquecida, execute o comando direto no container MariaDB:

```bash
docker exec -i ragnarok-db mysql -u ragnarok -pragnarok ragnarok -e "
UPDATE \`login\` SET \`user_pass\` = 'roadmin', \`group_id\` = 99 WHERE \`userid\` = 'roadmin';
"
```

### Como resetar a senha root do MariaDB em caso de perda total
Caso o arquivo `.env` tenha sido perdido e a senha de root seja desconhecida:

```bash
docker exec -i ragnarok-db mysql -u root -p$(grep MYSQL_ROOT_PASSWORD .env | cut -d '=' -f2) -e "STATUS;"
```

### Localização interna no container
Durante a subida do rAthena, um espelho deste documento é gerado em:
`/opt/rathena/CREDENTIALS.txt`

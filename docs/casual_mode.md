# Modo Casual / Roguelike Solo (Loop de 12 Horas)

Este projeto foi concebido não como um MMORPG de progressão perene, mas como um **ambiente roguelike descartável e portátil**, ideal para:
- Sessões de fim de semana solo (alcançar nível 99 em ~12h de gameplay, derrotar MVPs solo e encerrar a rodada).
- Eventos locais e convenções de anime (torneios presenciais de Speedrun 99 e MVP Bounty).
- Operações curtas com ciclos de vida de 1 dia a no máximo 3 meses.

---

## 1. O que o `casual.sh` configura

O script `docker/rathena/casual.sh` ajusta o rAthena automaticamente para o ritmo ágil de um roguelike:

1. **Rates de Experiência (330x)**:
   - `base_exp_rate: 33000` (330x)
   - `job_exp_rate: 33000` (330x)
   - Permite que o jogador avance pelos níveis sem grind repetitivo, focando em explorar os mapas procedurais.

2. **Rates de Drops Aumentadas (Solo Self-Found)**:
   - `item_rate_common: 1500` (15x)
   - `item_rate_heal: 500` (5x)
   - `item_rate_equip: 1000` (10x)
   - `item_rate_card: 300` (3x)
   - Garante que itens consumíveis e equipamentos essenciais dropem no ritmo necessário para viabilizar jogo solo sem depender de economia de mercado.

3. **Remoção de Burocracias (Zero Atrito)**:
   - Desativação completa do código PIN (`pincode_enabled: no`), agilizando logins repetidos e testes locais rápidos.

4. **Kit Inicial de Sobrevivência (`starter_items.txt`)**:
   - Fornece lupas, poções, asas de borboleta e itens utilitários no primeiro login para eliminar tempo morto no início da run.

5. **NPCs Utilitários em Cidades**:
   - Ativação automática de `warper.txt`, `healer.txt`, `stylist.txt`, `jobmaster.txt`, `resetnpc.txt` e `platinum_skills.txt`.

---

## 2. Pacing da Run Solo (0 a 12 Horas)

| Janela de Tempo | Fase da Run | Objetivo do Jogador |
|---|---|---|
| **0h – 2h** | Despertar & 2ª Classe | Criação do char, transição rápida via Jobmaster em Prontera, primeiro contato com os drops e affixes procedurais da seed. |
| **2h – 6h** | Mid-Game & Farm de Tier 2-3 | Exploração de dungeons de nível intermediário, coleta de minérios e busca por armas/armaduras sinérgicas com a build. |
| **6h – 9h** | Transclasse & Reta Final para o 99 | Conclusão do avanço de classe, refinos e preparação de consumíveis solo. |
| **9h – 12h** | Endgame Solo: Caça a MVPs | Desafio de MVPs pelo mapa mundi, testando as forças contra chefes com affixes aleatórios. |

---

## 3. Elementos Competitivos de Evento Local

Quando executado em estandes de convenções ou encontros LAN:
- **Speedrun 99**: Disputa entre jogadores para quem atinge nível 99 em menor tempo de cronômetro real.
- **MVP Bounty Hunter**: Placar de pontos por eliminação de MVPs durante as horas do evento.
- **Modo Telão (Filament Web)**: Exibição no projetor do evento com atualização contínua dos líderes da rodada.

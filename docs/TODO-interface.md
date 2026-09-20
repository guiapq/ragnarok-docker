# TODO Interface: Diagnóstico Técnico e Rotas de Conserto do roBrowser

Este documento registra detalhadamente todo o comportamento descoberto na integração entre o rAthena, o gerador de itens (`tools/generate_item_info_lua.py`), a WebAssembly Lua (`wasmoon`), o `roBrowserLegacy` (branch/commit `1433244`) e os arquivos GRF de referência (`/home/luiz/Projetos/Ragnarok (roBrowser)/data.grf`).

---

## 1. Status Atual: O que já funciona perfeitamente

1. **Roteamento `/client/` corrigido:**
   - O `roBrowser` requisita arquivos via HTTP usando o prefixo `/client/` por padrão quando `remoteClient` é vazio.
   - O symlink `/opt/roBrowserLegacy/client -> .` e o `entrypoint.sh` resolveram os erros 404 de carregamento de scripts base.
2. **Carga e Parsing do `itemInfo.lua`:**
   - O client baixa com sucesso os 5.9 MB do `System/itemInfo.lua`.
   - O `wasmoon` executa e popula os 6.170 itens do servidor no `ItemTable`.
3. **Metadados, Descrições e Nomes PT-BR:**
   - Nomes traduzidos aparecem perfeitamente nas janelas (ex: *"Main Gauche Double Vital [3]"*, *"Orelha de Coelho"*, *"Tunica Resistente"*).
   - Descrições procedurais ricas funcionam com cores formatadas (ex: bônus procedurais de Força, Ataque, Crítico em cores HEX do client).
4. **Sprites dos Personagens:**
   - Equipamentos visuais e headgears equipados no boneco renderizam perfeitamente na viewport (ex: orelha de coelho, armaduras, armas).

---

## 2. O Problema Visual Pendente: Slots Ovais Vazios e Ilustrações em Branco

Apesar dos nomes e descrições funcionarem, os ícones do inventário e da janela de equipamentos continuam exibindo o fundo oval azulado padrão (placeholder), e a janela de inspeção exibe um quadrado branco.

### A Cadeia de Resolução de Ícones do roBrowser

Quando o inventário renderiza um item (ex: ID `611` - Lupa ou ID `501` - Poção Vermelha):
1. O componente busca `it = DB.getItemInfo(item.ITID)`.
2. O roBrowser invoca `Client.loadFile(DB.INTERFACE_PATH + 'item/' + it.identifiedResourceName + '.bmp')`.
   - Onde `DB.INTERFACE_PATH` é `data/texture/\xc0\xaf\xc0\xfa\xc0\xce\xc5\xcd\xc6\xe4\xc0\xcc\xbd\xba/` (representação Windows-1252 de `유저인터페이스`, a pasta coreana de interface do Ragnarok).
3. O `FileManager` tenta encontrar esse caminho no `data.grf` carregado localmente pelo usuário.
4. **Se encontrar no GRF:** decodifica o BMP e aplica no CSS: `icon.style.backgroundImage = 'url(' + dataURI + ')'`.
5. **Se NÃO encontrar no GRF:** o roBrowser aciona o fallback HTTP:
   `GET /client/data/texture/유저인터페이스/item/<resourceName>.bmp`
   Como essas texturas não estão extraídas no servidor web, retorna 404, e o slot permanece no CSS padrão (oval vazio).

---

## 3. Causa Raiz Técnica: O "Double-Encoding" (Mojibake) do ResourceName

Ao inspecionar as requisições HTTP registradas nos logs do container `robrowser`:

```text
GET /client/data/texture/À¯ÀúÀÎÅÍÆäÀÌ½º/item/%C3%82%C2%B5%C3%82%C2%B8%C3%82%C2%BA%C3%82%C2%B8%C3%82%C2%B1%C3%83%C2%A2.bmp -> 404 Not Found
GET /client/data/texture/À¯ÀúÀÎÅÍÆäÀÌ½º/collection/%C3%82%C2%B8%C3%83%EF%BF%BD%C3%82%C2%B0%C3%83%C2%AD%C3%82%C2%BD%C3%82%C2%B4.bmp -> 404 Not Found
```

### O que o `data.grf` contém (Realidade):
O `data.grf` oficial grava os nomes das entradas de arquivo em codificação coreana legada (EUC-KR / CP949). Quando o roBrowser monta a tabela de arquivos do GRF (`GameFile.js`), ele decodifica os bytes brutos usando `windows-1252` e coloca em caixa baixa:
- Para a **Lupa (611)**, os bytes no GRF são: `[181, 184, 186, 184, 177, 226]` (`µ¸º¸±â`).
- A chave cadastrada no índice do GRF em memória é exatamente:  
  `data\texture\à¯àúàîåíæäàì½º\item\µ¸º¸±â.bmp` (6 caracteres no nome do arquivo).

### O que o gerador Python (`generate_item_info_lua.py`) gravou:
No script `tools/generate_item_info_lua.py`, a função `format_resource_name()` fez:
```python
raw_bytes = raw_res.encode('latin1')       # [181, 184, 186, 184, 177, 226]
js_str = raw_bytes.decode('windows-1252')   # "µ¸º¸±â"
utf8_bytes = js_str.encode('utf-8')        # [194, 181, 194, 184, 194, 186, 194, 184, 194, 177, 195, 162]
escaped = "".join(f"\\{b:03d}" for b in utf8_bytes)
```
Ele gravou **12 bytes** no arquivo Lua em vez de 6 bytes.

### Onde ocorre o conflito:
1. No `wasmoon` (Wasm Lua 5.1), a função que extrai a string de retorno para o JavaScript (`lua_tolstring`) trata a string como bytes C brutos ou passa por decodificação UTF-8 do Emscripten.
2. No JavaScript, a string em `ItemTable[611].identifiedResourceName` ficou com os caracteres `ÂµÂ¸ÂºÂ¸Â±Ã¢` (12 caracteres).
3. Ao buscar no índice do `data.grf`:
   - Busca: `data\texture\à¯àúàîåíæäàì½º\item\âµâ¸âºâ¸â±ã¢.bmp`
   - Índice real do GRF: `data\texture\à¯àúàîåíæäàì½º\item\µ¸º¸±â.bmp`
   - **Resultado: NÃO ENCONTRADO.**
4. Como não encontra no GRF, o roBrowser executa `encodeURIComponent` na string de 12 caracteres (gerando `%C3%82%C2%B5...`) e pede via HTTP ao servidor, que não tem o arquivo e retorna 404.

---

## 4. Possíveis Rotas de Conserto

Quando formos atacar essa questão visual, estas são as rotas viáveis avaliadas:

### Rota A (Recomendada - Mais Limpa): Corrigir a Emissão em `tools/generate_item_info_lua.py`
- Em vez de fazer o re-encode UTF-8 duplo na função `format_resource_name`, emitir diretamente os bytes originais do Latin-1 no Lua:
  ```python
  def format_resource_name(raw_res):
      if not raw_res:
          return '""'
      raw_bytes = raw_res.encode('latin1')
      # Emite diretamente os bytes que casam 1:1 com o índice do GRF (sem duplicar 194/195)
      escaped = "".join(f"\\{b:03d}" for b in raw_bytes)
      return f'"{escaped}"'
  ```
- **Vantagem:** O `itemInfo.lua` passa a ter exatamente as mesmas strings de resource que os arquivos oficiais da Gravity possuem. O `data.grf` dará *hit* imediato em memória, sem disparar requisições HTTP e sem precisar de patches no código JavaScript do roBrowser.

### Rota B: Higienização no `patch_online.js` (Camada do Cliente Web)
- No `AddItem` do `Online.js`, antes de gravar `identifiedResourceName` e `unidentifiedResourceName`, aplicar uma função de des-duplicação de UTF-8 caso venha mojibake:
  ```javascript
  const fixMojibake = (str) => {
      if (!str || typeof str !== 'string') return str;
      try {
          // Se contiver caracteres Â ou Ã provenientes de double-encoding UTF-8:
          return decodeURIComponent(escape(str));
      } catch (e) {
          return str;
      }
  };
  ```
- **Vantagem:** Funciona mesmo se o `itemInfo.lua` tiver sido gerado com encoding incompatível.
- **Desvantagem:** Depende de rodar regex de patching no bundle compilado do roBrowser.

### Rota C: Servidor de Assets HTTP Dedicado (Fallback Universal)
- Extrair do `data.grf` as pastas:
  - `data/texture/유저인터페이스/item/`
  - `data/texture/유저인터페이스/collection/`
- Mapeá-las no volume do Docker do `robrowser` em `/opt/roBrowserLegacy/data/texture/...`.
- **Vantagem:** Independe do usuário ter montado ou arrastado o GRF correto no navegador; qualquer item faltante é baixado imediatamente via HTTP pelo roBrowser.
- **Desvantagem:** Exige espaço em disco para armazenar os BMPs extraídos no repositório/container.

---

## 5. Checklist para Retomada Futura

- [ ] Testar Rota A alterando `format_resource_name` em `tools/generate_item_info_lua.py` e rodando `python3 tools/generate_item_info_lua.py`.
- [ ] Inspecionar se o tamanho da string em bytes no Lua reduziu pela metade (ex: 6 bytes para Lupa em vez de 12).
- [ ] Abrir o roBrowser e checar se os ícones do inventário carregam instantaneamente a partir do `data.grf`.
- [ ] Checar se a moldura de coleção e o ícone de cartas (ex: Carta Fabre) resolvem o bitmap correspondente.

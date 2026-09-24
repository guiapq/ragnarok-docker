#!/usr/bin/env python3
"""
tools/configure_groups.py

Garante de forma elegante e estruturada que o arquivo groups.conf do rAthena contenha:
1. Comandos @warp e @go habilitados para o Grupo 0 (jogadores comuns).
2. Grupo 6 ("Tester") completo para as contas de teste / QA.

Compatível com execução standalone no host ou dentro de containers rAthena.
"""

import sys
import os
import re
import tempfile

GROUP_6_BLOCK = """{
\tid: 6
\tname: "Tester"
\tinherit: ( "Support" )
\tlevel: 1
\tcommands: {
\t\t/* Movimentacao */
\t\tgo: true
\t\twarp: true
\t\tjump: true
\t\t/* Itens & Status */
\t\titem: [true, true]
\t\tzeny: true
\t\theal: [true, true]
\t\talive: true
\t\t/* Classe & Skills */
\t\tjobchange: true
\t\tallskill: true
\t\tskpoint: true
\t\t/* Conveniencia */
\t\tspeed: true
\t\tstorage: true
\t\tnoks: true
\t\t/* Info */
\t\twhere: true
\t\tstats: [true, true]
\t}
\tlog_commands: true
\tpermissions: {
\t\tcan_trade: true
\t\tcan_party: true
\t\tany_warp: true
\t}
}"""


def check_brackets_balance(text: str) -> bool:
    """Verifica se os blocos de chaves e parênteses estão equilibrados, ignorando comentários."""
    # Remover comentários de bloco /* ... */ e linha // ...
    clean = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    clean = re.sub(r'//.*', '', clean)
    
    curly = 0
    paren = 0
    for char in clean:
        if char == '{':
            curly += 1
        elif char == '}':
            curly -= 1
        elif char == '(':
            paren += 1
        elif char == ')':
            paren -= 1
        if curly < 0 or paren < 0:
            return False
    return curly == 0 and paren == 0


def patch_group_0_commands(content: str) -> tuple[str, bool]:
    """Garante que o Grupo 0 (id: 0) tenha comandos essenciais habilitados."""
    # Encontra o bloco do id: 0
    # O bloco do grupo 0 começa com '{' e tem 'id: 0'
    m_grp = re.search(r'(\{\s*id:\s*0\b[^\}]*?commands:\s*\{)([^\}]*?)(\})', content, re.DOTALL)
    if not m_grp:
        # Tenta formato mais flexível caso id venha após comentários
        m_grp = re.search(r'(\{[\s/\*a-zA-Z0-9_\-]*?id:\s*0\b.*?commands:\s*\{)(.*?)(\}\s*(?:permissions|log_commands|\}))', content, re.DOTALL)
        if not m_grp:
            return content, False

    header = m_grp.group(1)
    commands_body = m_grp.group(2)
    footer = m_grp.group(3)

    modified = False
    new_cmds = commands_body

    required_commands = [
        "warp",
        "go",
        "autoloot",
        "alootid",
        "autoloottype",
        "whodrops",
        "iteminfo",
        "mobinfo",
        "identify",
        "identifyall",
    ]

    for cmd in required_commands:
        if not re.search(rf'\b{cmd}\s*:', new_cmds):
            new_cmds += f"\n\t\t{cmd}: true"
            modified = True
        else:
            sub_new, n = re.subn(rf'(\b{cmd}\s*:\s*)false', r'\1true', new_cmds)
            if n > 0:
                new_cmds = sub_new
                modified = True

    if not modified:
        return content, False

    new_block = header + new_cmds + "\n\t" + footer
    # Substituir no texto apenas na posição do match
    start, end = m_grp.span()
    updated_content = content[:start] + new_block + content[end:]
    return updated_content, True


def patch_group_6(content: str) -> tuple[str, bool]:
    """Garante que o Grupo 6 (id: 6) exista no groups.conf."""
    # Verificar se o id: 6 já existe
    if re.search(r'\bid:\s*6\b', content):
        return content, False

    # Procura ponto de inserção ideal: antes do Grupo 10 ou antes do Grupo 99
    # Procura por '{\s*id:\s*10' ou '{\s*id:\s*99'
    target_match = re.search(r'(\n\s*\{\s*\n\s*id:\s*(?:10|99)\b)', content)
    if not target_match:
        # Fallback: antes do fechamento do groups: (...)
        target_match = re.search(r'(\n\)\s*;?\s*$)', content)
        if not target_match:
            print("[ERRO] Não foi possível encontrar ponto de inserção para o Grupo 6.")
            return content, False
        
        insert_pos = target_match.start()
        # Se for antes do ), adiciona vírgula se necessário
        new_content = content[:insert_pos] + ",\n" + GROUP_6_BLOCK + "\n" + content[insert_pos:]
    else:
        insert_pos = target_match.start()
        # Insere o bloco com vírgula e quebra de linha
        new_content = content[:insert_pos] + "\n" + GROUP_6_BLOCK + ",\n" + content[insert_pos+1:]

    return new_content, True


def configure_file(filepath: str) -> bool:
    if not os.path.isfile(filepath):
        print(f"[PULADO] Arquivo não encontrado: {filepath}")
        return False

    print(f"--> Analisando: {filepath}")
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    changed = False

    # 1. Ajustar Grupo 0 (@warp e @go)
    content, c1 = patch_group_0_commands(content)
    if c1:
        print("  ✓ Habilitados comandos @warp e @go para o Grupo 0 (Player)")
        changed = True
    else:
        print("  - Grupo 0 já possui @warp e @go ativos")

    # 2. Inserir Grupo 6 se não existir
    content, c2 = patch_group_6(content)
    if c2:
        print("  ✓ Grupo 6 (Tester) inserido com sucesso")
        changed = True
    else:
        print("  - Grupo 6 já existe")

    if not changed:
        print(f"  ✓ {filepath} já está perfeitamente configurado.")
        return True

    # 3. Validar integridade da sintaxe
    if not check_brackets_balance(content):
        print(f"[ERRO CRÍTICO] Falha na validação de chaves/parênteses em {filepath}. Modificação abortada.")
        return False

    # 4. Gravação atômica
    dirname = os.path.dirname(filepath) or '.'
    with tempfile.NamedTemporaryFile('w', dir=dirname, delete=False, encoding='utf-8') as tf:
        tf.write(content)
        temp_path = tf.name

    os.replace(temp_path, filepath)
    print(f"  ✓ Arquivo {filepath} atualizado com sucesso!")
    return True


def main():
    targets = sys.argv[1:]
    if not targets:
        # Padrões comuns
        candidates = [
            "data/conf/groups.conf",
            "data_base/conf/groups.conf",
            "/opt/rathena/conf/groups.conf"
        ]
        targets = [c for c in candidates if os.path.isfile(c)]
        if not targets:
            print("Uso: configure_groups.py <caminho_para_groups.conf>")
            sys.exit(1)

    all_ok = True
    for target in targets:
        ok = configure_file(target)
        if not ok:
            all_ok = False

    if not all_ok:
        sys.exit(1)


if __name__ == '__main__':
    main()

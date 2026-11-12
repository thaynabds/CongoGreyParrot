"""AI Conector: o mesmo lugar, em todos os programas do Congo, para ligar uma IA por MCP.

Cada programa mostra este conteúdo na própria interface (página, tela ou comando).
Só fala stdio com o Claude Desktop, o Cursor e o Claude Code: nenhuma porta de rede fica aberta.
"""

from __future__ import annotations

import asyncio
import json
import shlex

try:
    from registrar_claude import congo_servers, cursor_config, desktop_config, is_registered, register_one
except ModuleNotFoundError:  # cópia empacotada dentro do programa (Flatpak, pip)
    from .registrar_claude import congo_servers, cursor_config, desktop_config, is_registered, register_one

TITLE = "AI Conector"

PROGRAMS = {
    "congo-desktop": "Congo Grey Parrot Desktop",
    "congo-reunioes": "Congo Grey Parrot Reuniões",
    "congo-discord": "Congo Grey Parrot Discord",
    "congo-android": "Congo Grey Parrot Android",
}


def _check(name: str) -> None:
    if name not in PROGRAMS:
        raise ValueError("Programa desconhecido.")


_OVERRIDES: dict[str, dict] = {}


def use_entry(name: str, found: dict | None) -> None:
    """O programa diz como o próprio servidor MCP abre (por exemplo, pelo Flatpak instalado)."""
    _check(name)
    if found is None:
        _OVERRIDES.pop(name, None)
    else:
        _OVERRIDES[name] = found


def entry(name: str) -> dict | None:
    """Comando absoluto do servidor MCP deste programa, ou None se ainda não foi instalado."""
    _check(name)
    if name in _OVERRIDES:
        return _OVERRIDES[name]
    return congo_servers().get(name)


def snippet(name: str) -> str:
    """Bloco JSON para colar no arquivo de configuração de qualquer cliente MCP."""
    found = entry(name)
    if found is None:
        return ""
    return json.dumps({"mcpServers": {name: found}}, ensure_ascii=False, indent=2)


def claude_code_command(name: str) -> str:
    found = entry(name)
    if found is None:
        return ""
    parts = ["claude", "mcp", "add", "--scope", "user", name, "--", found["command"], *found.get("args", [])]
    return " ".join(shlex.quote(part) for part in parts)


def status(name: str) -> dict[str, bool]:
    _check(name)
    return {
        "instalado": entry(name) is not None,
        "claude_desktop": is_registered(desktop_config(), name),
        "cursor": is_registered(cursor_config(), name),
    }


def connect(name: str) -> str:
    """Registra este programa no Claude Desktop e no Cursor, sem mexer nos outros servidores."""
    found = entry(name)
    if found is None:
        return "O servidor MCP deste programa ainda não foi instalado. Rode ./instalar.sh na pasta do projeto."
    register_one(desktop_config(), name, found)
    register_one(cursor_config(), name, found)
    return "Conectado ao Claude Desktop e ao Cursor. Feche e abra o aplicativo da IA para ele ler a mudança."


def disconnect(name: str) -> str:
    _check(name)
    register_one(desktop_config(), name, None)
    register_one(cursor_config(), name, None)
    return "Desconectado do Claude Desktop e do Cursor."


def tool_lines(server) -> list[str]:
    result = server.list_tools()
    if asyncio.iscoroutine(result):
        result = asyncio.run(result)
    lines = []
    for item in sorted(result, key=lambda tool: tool.name):
        summary = (item.description or "").strip().splitlines()
        lines.append(f"{item.name}: {summary[0] if summary else ''}")
    return lines


def report(name: str, server=None) -> str:
    """Texto completo da área AI Conector, para terminal, Discord ou janela."""
    state = status(name)
    yes = {True: "sim", False: "não"}
    lines = [
        f"{TITLE} · {PROGRAMS[name]}",
        "Ligue uma IA (Claude Desktop, Cursor, Claude Code ou outro cliente MCP) a este programa.",
        "",
        f"Servidor MCP instalado: {yes[state['instalado']]}",
        f"Conectado ao Claude Desktop: {yes[state['claude_desktop']]}",
        f"Conectado ao Cursor: {yes[state['cursor']]}",
    ]
    command = claude_code_command(name)
    if command:
        lines += ["", "Claude Code (cole no terminal):", command, "", "Outro cliente MCP (cole na configuração):", snippet(name)]
    if server is not None:
        lines += ["", "O que a IA pode fazer aqui:", *tool_lines(server)]
    lines += [
        "",
        "Segurança: só stdio, nada de porta aberta. Arquivos só da pasta pessoal, fora de pastas ocultas.",
        "Apagar ou enviar algo para fora pede confirmar=true na própria ferramenta.",
    ]
    return "\n".join(lines)


def cli(name: str, server_factory, argv: list[str]) -> int:
    """Comando de terminal `conector`: mostra, conecta ou desconecta."""
    if "--conectar" in argv:
        print(connect(name))
        return 0
    if "--desconectar" in argv:
        print(disconnect(name))
        return 0
    server = None
    try:
        server = server_factory()
    except Exception:  # o pacote mcp pode faltar; a área continua mostrando o resto
        server = None
    print(report(name, server))
    print("\nPara conectar: acrescente --conectar. Para desfazer: --desconectar.")
    return 0



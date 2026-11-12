"""Confere a lista de ferramentas sem abrir HTTP e sem token do Discord."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [
    str(ROOT / "mcp"),
    str(ROOT / "congo-grey-parrot-desktop" / "src"),
    str(ROOT / "congo-grey-parrot-discord" / "src"),
    str(ROOT / "congo-grey-parrot-reunioes" / "src"),
    str(ROOT / "congo-grey-parrot-android"),
]


def test_tool_lists_import_without_network():
    expected = {
        "congo_grey_parrot.mcp_server": {
            "listar_idiomas", "listar_modelos", "transcrever_arquivo", "gerar_legenda", "converter_legenda",
            "ajustar_tempo_legenda", "falar_texto", "traduzir_texto", "resumir_texto", "resumir_arquivo",
            "ler_documento", "salvar_texto", "converter_midia", "gravar_legenda_no_video", "listar_saidas",
            "baixar_modelo", "listar_vozes", "baixar_voz", "remover_voz", "listar_historico", "limpar_historico",
            "ver_configuracoes", "alterar_configuracao",
        },
        "congo_reunioes.mcp_server": {
            "listar_plataformas", "importar_transcricao", "importar_pasta", "listar_notas", "resumir_reuniao",
            "resumir_texto", "notas_json", "transcrever_audio", "limpar_notas",
        },
        "congo_discord.mcp_server": {
            "status_bot", "listar_funcoes", "ajuda_comandos", "enviar_mensagem", "ver_log", "link_convite",
            "listar_servidores", "tocar_som", "parar_som", "sair_voz", "marcar_sessao", "reuniao_entrar",
            "rolar_dados", "rolar_percentil", "rolar_pool", "gerar_nome", "consultar_regra", "ficha_ver",
            "ficha_definir", "iniciativa", "grupo", "sessoes", "reuniao", "ligar_funcao", "listar_sons",
        },
        "mcp_server": {
            "instrucoes_apk", "caminho_apk", "listar_aparelhos", "instalar_apk", "iniciar_app", "status_celular",
            "listar_arquivos", "ler_arquivo", "salvar_texto", "excluir_arquivo", "resumir_no_celular",
            "ler_em_voz_alta", "parar_leitura", "salvar_audio",
        },
    }
    for module_name, names in expected.items():
        module = importlib.import_module(module_name)
        server = module.build_server()
        from runtime import tool_names

        assert set(tool_names(server)) == names


def test_path_guard_blocks_secrets_and_wrong_types(tmp_path, monkeypatch):
    import pytest
    from runtime import guarded_path

    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".ssh").mkdir()
    (tmp_path / "Documentos").mkdir()
    ok = guarded_path(str(tmp_path / "Documentos" / "reuniao.vtt"), {".vtt"})
    assert ok.name == "reuniao.vtt"
    for raw, suffixes in [
        (str(tmp_path / ".ssh" / "id_ed25519"), {".vtt"}),
        (str(tmp_path / ".ssh" / "chave.vtt"), {".vtt"}),
        (str(tmp_path / ".bashrc"), {".wav"}),
        (str(tmp_path / "Documentos" / "senhas.kdbx"), {".vtt"}),
        ("/etc/passwd", {".vtt"}),
        (str(tmp_path / "Documentos" / ".." / ".." / "fora.vtt"), {".vtt"}),
        (str(tmp_path), {".vtt"}),
    ]:
        with pytest.raises(ValueError):
            guarded_path(raw, suffixes)


def test_path_guard_used_by_file_tools(tmp_path, monkeypatch):
    import asyncio

    import pytest

    monkeypatch.setenv("HOME", str(tmp_path))
    secret = tmp_path / ".ssh" / "id_ed25519"
    secret.parent.mkdir()
    secret.write_text("PRIVATE KEY", encoding="utf-8")
    module = importlib.import_module("congo_reunioes.mcp_server")
    server = module.build_server()
    with pytest.raises(Exception) as caught:
        result = server.call_tool("importar_transcricao", {"caminho": str(secret)})
        if asyncio.iscoroutine(result):
            asyncio.run(result)
    assert "PRIVATE KEY" not in str(caught.value)


def _call(server, name, args):
    import asyncio

    result = server.call_tool(name, args)
    if asyncio.iscoroutine(result):
        result = asyncio.run(result)
    return str(result)


def test_path_guard_for_folders(tmp_path, monkeypatch):
    import pytest
    from runtime import guarded_dir

    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / "Downloads").mkdir()
    assert guarded_dir(str(tmp_path / "Downloads")).name == "Downloads"
    for raw in [str(tmp_path), str(tmp_path / ".ssh"), "/etc", str(tmp_path / "Downloads" / ".." / "..")]:
        with pytest.raises(ValueError):
            guarded_dir(raw)


def test_importar_pasta_tool_imports_meet_and_refuses_hidden_folder(tmp_path, monkeypatch):
    import pytest

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("CONGO_REUNIOES_DATA", str(tmp_path / "dados"))
    folder = tmp_path / "Downloads"
    folder.mkdir()
    (folder / "Daily - Transcript.txt").write_text("00:00:00\nAna: bom dia\n", encoding="utf-8")
    hidden = tmp_path / ".config"
    hidden.mkdir()
    (hidden / "x - Transcript.txt").write_text("Segredo: abc\n", encoding="utf-8")
    server = importlib.import_module("congo_reunioes.mcp_server").build_server()
    assert "importado, 1 falas" in _call(server, "importar_pasta", {"pasta": str(folder)})
    assert "já importado" in _call(server, "importar_pasta", {"pasta": str(folder)})
    with pytest.raises(Exception) as caught:
        _call(server, "importar_pasta", {"pasta": str(hidden)})
    assert "abc" not in str(caught.value)


def test_discord_log_hides_tokens_and_invite_is_minimal(monkeypatch):
    import pytest

    module = importlib.import_module("congo_discord.mcp_server")
    # Falso e montado em partes, para o push protection do GitHub não confundir com um token real.
    leaked = ".".join(["M" + "x" * 25, "Gx" + "y" * 4, "z" * 38])
    assert leaked not in module.redact(f"login falhou com {leaked}")
    server = module.build_server()
    text = _call(server, "link_convite", {"id_aplicacao": "123456789012345678"})
    assert "permissions=3181568" in text and "Sem Administrador" in text
    with pytest.raises(Exception):
        _call(server, "link_convite", {"id_aplicacao": "123&scope=admin"})
    monkeypatch.setattr(module.shutil, "which", lambda name: None)
    assert "journalctl" in _call(server, "ver_log", {"linhas": 9999})


def test_discord_service_state_finds_user_bus_without_session_env(monkeypatch):
    module = importlib.import_module("congo_discord.mcp_server")
    monkeypatch.delenv("XDG_RUNTIME_DIR", raising=False)
    seen = {}

    class Done:
        stdout = "active\n"

    def fake_run(args, **kwargs):
        seen["env"] = kwargs.get("env") or {}
        return Done()

    monkeypatch.setattr(module.shutil, "which", lambda name: "/usr/bin/systemctl")
    monkeypatch.setattr(module.subprocess, "run", fake_run)
    assert module._service_state() == "active"
    runtime = Path(f"/run/user/{module.os.getuid()}")
    if runtime.is_dir():
        assert seen["env"].get("XDG_RUNTIME_DIR") == str(runtime)


def test_registrar_keeps_other_servers_and_is_idempotent(tmp_path):
    import json

    from registrar_claude import congo_servers, register

    config = tmp_path / "Claude" / "claude_desktop_config.json"
    config.parent.mkdir()
    config.write_text(json.dumps({"mcpServers": {"railway": {"command": "railway"}}, "outro": 1}), encoding="utf-8")
    fake = tmp_path / "repo"
    (fake / "bin").mkdir(parents=True)
    (fake / "bin" / "servidor").write_text("", encoding="utf-8")
    (fake / "mcp.json").write_text(json.dumps({"mcpServers": {
        "congo-um": {"command": "bin/servidor"},
        "congo-falta": {"command": "bin/nao-instalado"},
    }}), encoding="utf-8")
    servers = congo_servers(fake)
    assert servers == {"congo-um": {"command": str(fake / "bin" / "servidor")}}
    assert register(config, servers) == sorted(servers)
    data = json.loads(config.read_text(encoding="utf-8"))
    assert data["outro"] == 1 and "railway" in data["mcpServers"]
    assert set(servers) <= set(data["mcpServers"])
    assert (tmp_path / "Claude" / "claude_desktop_config.json.bak").is_file()
    assert oct(config.stat().st_mode & 0o777) == "0o600"
    assert register(config, servers) == []
    register(config, servers, remove=True)
    assert set(json.loads(config.read_text(encoding="utf-8"))["mcpServers"]) == {"railway"}


def test_resumo_copies_are_identical():
    """O resumo.py é o mesmo no computador, no bot e nas reuniões."""
    copies = [
        ROOT / "congo-grey-parrot-desktop" / "src" / "congo_grey_parrot" / "resumo.py",
        ROOT / "congo-grey-parrot-discord" / "src" / "congo_discord" / "resumo.py",
        ROOT / "congo-grey-parrot-reunioes" / "src" / "congo_reunioes" / "resumo.py",
    ]
    texts = {path.read_text(encoding="utf-8") for path in copies}
    assert len(texts) == 1


def test_resumir_arquivo_reads_home_text_and_refuses_secrets(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".ssh").mkdir()
    (tmp_path / ".ssh" / "notas.txt").write_text("segredo guardado aqui. outra frase secreta.", encoding="utf-8")
    docs = tmp_path / "Documentos"
    docs.mkdir()
    (docs / "ata.txt").write_text(
        "O projeto do aplicativo atrasou. Ficou decidido revisar o projeto do aplicativo. "
        "Vou mandar o relatório do projeto até sexta. Quem fala com o cliente?",
        encoding="utf-8",
    )
    module = importlib.import_module("congo_grey_parrot.mcp_server")
    server = module.build_server()

    def call(name, **kwargs):
        try:
            return _call(server, name, kwargs)
        except Exception as exc:  # o erro do guarda também não pode mostrar o conteúdo
            return str(exc)

    ok = call("resumir_arquivo", caminho=str(docs / "ata.txt"))
    assert "Resumo de ata.txt" in ok and "Ficou decidido" in ok
    for bad in (str(tmp_path / ".ssh" / "notas.txt"), "/etc/passwd", str(docs / "ata.exe")):
        assert "segredo" not in call("resumir_arquivo", caminho=bad)
    assert "Não há texto" in call("resumir_texto", texto="   ")
    many = "\n".join(f"Frase número {n} fala do projeto e do prazo novo." for n in range(80))
    assert "Resumo (30 de 80" in call("resumir_texto", texto=many, frases=999)
    assert "Resumo (" in call("resumir_texto", texto=many, frases=-5)
    assert "validation error" in call("resumir_texto", texto=many, frases="x")


def _try(server, name, **kwargs):
    try:
        return _call(server, name, kwargs)
    except Exception as exc:  # erros de trava voltam como texto, sem o conteúdo protegido
        return f"ERRO {exc}"


def test_aiconector_copies_match_mcp_folder():
    """O Desktop leva cópias de mcp/ para o Flatpak; elas não podem divergir."""
    packaged = ROOT / "congo-grey-parrot-desktop" / "src" / "congo_grey_parrot" / "aiconector"
    for name in ("runtime.py", "registrar_claude.py", "conector.py"):
        assert (packaged / name).read_text(encoding="utf-8") == (ROOT / "mcp" / name).read_text(encoding="utf-8"), name


def test_register_one_keeps_other_servers_private_and_refuses_foreign_names(tmp_path):
    import json

    import pytest
    from registrar_claude import is_registered, register_one

    config = tmp_path / "cfg.json"
    config.write_text(json.dumps({"mcpServers": {"outro": {"command": "x", "env": {"TOKEN": "s"}}}}), encoding="utf-8")
    assert register_one(config, "congo-desktop", {"command": "/bin/congo"}) is True
    assert register_one(config, "congo-desktop", {"command": "/bin/congo"}) is False
    data = json.loads(config.read_text(encoding="utf-8"))
    assert data["mcpServers"]["outro"]["env"]["TOKEN"] == "s"
    assert is_registered(config, "congo-desktop")
    assert oct(config.stat().st_mode & 0o777) == "0o600"
    with pytest.raises(ValueError):
        register_one(config, "railway", {"command": "/tmp/evil"})
    register_one(config, "congo-desktop", None)
    assert not is_registered(config, "congo-desktop") and "outro" in json.loads(config.read_text())["mcpServers"]
    config.write_text("[1, 2]", encoding="utf-8")
    with pytest.raises(ValueError):
        register_one(config, "congo-desktop", {"command": "x"})


def test_conector_report_and_flatpak_paths(tmp_path, monkeypatch):
    import conector
    import registrar_claude

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("FLATPAK_ID", "io.github.thaynabds.CongoGreyParrot")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / ".var" / "app" / "config"))
    monkeypatch.delenv("HOST_XDG_CONFIG_HOME", raising=False)
    assert registrar_claude.desktop_config() == tmp_path / ".config" / "Claude" / "claude_desktop_config.json"
    conector.use_entry("congo-desktop", {"command": "flatpak", "args": ["run", "--command=congo-grey-parrot-mcp", "x"]})
    try:
        assert "flatpak run" in conector.claude_code_command("congo-desktop")
        assert "Conectado" in conector.connect("congo-desktop")
        assert conector.status("congo-desktop") == {"instalado": True, "claude_desktop": True, "cursor": True}
        text = conector.report("congo-desktop")
        assert text.startswith("AI Conector") and "confirmar=true" in text
        conector.disconnect("congo-desktop")
        assert conector.status("congo-desktop")["claude_desktop"] is False
    finally:
        conector.use_entry("congo-desktop", None)


def test_desktop_tools_guard_files_overwrites_and_settings(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "dados"))
    docs = tmp_path / "Documentos"
    docs.mkdir()
    (tmp_path / ".ssh").mkdir()
    (tmp_path / ".ssh" / "id.txt").write_text("CHAVE SECRETA", encoding="utf-8")
    server = importlib.import_module("congo_grey_parrot.mcp_server").build_server()
    assert "Salvo em" in _try(server, "salvar_texto", caminho=str(docs / "nota.txt"), texto="Olá mundo.")
    assert "já existe" in _try(server, "salvar_texto", caminho=str(docs / "nota.txt"), texto="outro")
    assert "Salvo em" in _try(server, "salvar_texto", caminho=str(docs / "nota.txt"), texto="novo", sobrescrever=True)
    assert "novo" in _try(server, "ler_documento", caminho=str(docs / "nota.txt"))
    for bad in (str(tmp_path / ".ssh" / "id.txt"), "/etc/passwd", str(docs / ".." / ".ssh" / "id.txt")):
        assert "CHAVE" not in _try(server, "ler_documento", caminho=bad)
    assert "ERRO" in _try(server, "salvar_texto", caminho=str(tmp_path / ".bashrc"), texto="x")
    assert "ERRO" in _try(server, "salvar_texto", caminho=str(docs / "x.sh"), texto="x")
    assert "documento" in _try(server, "listar_historico")
    assert "Nada foi apagado" in _try(server, "limpar_historico")
    assert "documento" in _try(server, "listar_historico")
    assert "apagado" in _try(server, "limpar_historico", confirmar=True)
    assert "vazio" in _try(server, "listar_historico")
    assert "ERRO" in _try(server, "alterar_configuracao", chave="output_dir", valor=str(tmp_path / ".config"))
    assert "ERRO" in _try(server, "alterar_configuracao", chave="font_scale", valor="9")
    assert "ERRO" in _try(server, "alterar_configuracao", chave="segredo", valor="1")
    assert "agora é" in _try(server, "alterar_configuracao", chave="font_scale", valor="1.2")
    assert "font_scale: 1.2" in _try(server, "ver_configuracoes")
    assert "ERRO" in _try(server, "baixar_modelo", nome="../../etc")
    assert "ERRO" in _try(server, "baixar_voz", id_voz="nao-existe")
    assert "ERRO" in _try(server, "remover_voz", id_voz="../vozes")
    assert "ERRO" in _try(server, "converter_midia", origem=str(tmp_path / ".ssh" / "id.txt"), destino=str(docs / "a.mp3"))


def test_reunioes_clear_needs_confirmation_and_audio_is_guarded(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("CONGO_REUNIOES_DATA", str(tmp_path / "dados"))
    folder = tmp_path / "Downloads"
    folder.mkdir()
    (folder / "Daily - Transcript.txt").write_text("00:00:00\nAna: bom dia\n", encoding="utf-8")
    server = importlib.import_module("congo_reunioes.mcp_server").build_server()
    _call(server, "importar_pasta", {"pasta": str(folder)})
    assert '"pessoa": "Ana"' in _call(server, "notas_json", {})
    assert "Nada foi apagado" in _call(server, "limpar_notas", {})
    assert "Ana" in _call(server, "listar_notas", {})
    assert "Apaguei" in _call(server, "limpar_notas", {"confirmar": True})
    assert "Ana" not in _call(server, "notas_json", {})
    (tmp_path / ".cache").mkdir()
    (tmp_path / ".cache" / "x.mp3").write_bytes(b"x")
    assert "ERRO" in _try(server, "transcrever_audio", caminho=str(tmp_path / ".cache" / "x.mp3"))
    assert "ERRO" in _try(server, "transcrever_audio", caminho=str(folder / "Daily - Transcript.txt"))


def test_discord_tools_confirm_validate_ids_and_use_store(tmp_path, monkeypatch):
    monkeypatch.setenv("CONGO_DISCORD_DATA", str(tmp_path / "bot"))
    monkeypatch.setenv("CONGO_DISCORD_CONTROL", str(tmp_path / "nao-existe.sock"))
    module = importlib.import_module("congo_discord.mcp_server")
    server = module.build_server()
    guild = "123456789012345678"
    assert "Nada foi enviado" in _try(server, "enviar_mensagem", canal_id=guild, texto="@everyone oi")
    assert "ERRO" in _try(server, "enviar_mensagem", canal_id="1/../2", texto="x", confirmar=True)
    assert "não está ligado" in _try(server, "listar_servidores")
    assert "Nada foi" in _try(server, "reuniao_entrar", canal_voz_id=guild)
    assert "Nada foi publicado" in _try(server, "marcar_sessao", canal_id=guild, titulo="t", quando="q")
    assert "1d20" in _try(server, "rolar_dados", expressao="1d20+1")
    assert "ERRO" in _try(server, "rolar_dados", expressao="1d20", modo="roubar")
    _try(server, "iniciativa", servidor_id=guild, acao="adicionar", nome="Ana", resultado=15)
    assert "Ana (15)" in _try(server, "iniciativa", servidor_id=guild)
    assert "Nada foi apagado" in _try(server, "iniciativa", servidor_id=guild, acao="limpar")
    assert "ouro: 10" in _try(server, "grupo", servidor_id=guild, item="ouro", quantidade=10)
    assert "desligada" in _try(server, "ligar_funcao", nome="dados", ligada=False)
    assert "desativada" in _try(server, "rolar_dados", expressao="1d6")
    assert "ERRO" in _try(server, "ficha_ver", servidor_id="abc", jogador_id=guild)


def test_discord_control_socket_is_private_and_answers(tmp_path, monkeypatch):
    import asyncio
    import os
    import threading

    path = tmp_path / "run" / "control.sock"
    monkeypatch.setenv("CONGO_DISCORD_CONTROL", str(path))
    control = importlib.import_module("congo_discord.service.control")
    ready = threading.Event()
    loop = asyncio.new_event_loop()

    async def handler(action, args):
        if action != "eco":
            raise ValueError("Ação desconhecida.")
        return "eco " + args.get("texto", "")

    async def boot():
        await control.start_server(handler)
        ready.set()

    thread = threading.Thread(target=lambda: (loop.run_until_complete(boot()), loop.run_forever()), daemon=True)
    thread.start()
    assert ready.wait(5)
    try:
        assert oct(os.stat(path).st_mode & 0o777) == "0o600"
        assert oct(os.stat(path.parent).st_mode & 0o777) == "0o700"
        assert control.call("eco", {"texto": "oi"}) == (True, "eco oi")
        ok, text = control.call("apagar_tudo", {})
        assert ok is False and "desconhecida" in text
        assert control.call("eco", {"texto": "x" * 70000})[0] is False
    finally:
        loop.call_soon_threadsafe(loop.stop)


def test_android_bridge_never_puts_raw_text_in_adb_command(monkeypatch):
    import base64
    import json

    module = importlib.import_module("mcp_server")
    seen = {}

    def fake_adb(*args, timeout=60):
        seen["args"] = args
        payload = json.loads(base64.b64decode(args[args.index("--arg") + 1]))
        reply = base64.b64encode(("feito " + payload.get("texto", "")).encode()).decode()
        return f"Result: Bundle[{{ok=true, resultado={reply}}}]"

    monkeypatch.setattr(module, "_adb", fake_adb)
    server = module.build_server()
    evil = "oi'; rm -rf /sdcard; echo '$(reboot)"
    assert "feito oi'; rm" in _call(server, "ler_em_voz_alta", {"texto": evil})
    assert all(evil not in part for part in seen["args"])
    assert all(";" not in part and "$" not in part for part in seen["args"])
    assert "Nada foi apagado" in _call(server, "excluir_arquivo", {"nome": "a.txt"})
    for bad in ("../x", "a;b", "a/b", ""):
        assert "ERRO" in _try(server, "ler_arquivo", nome=bad)
    assert "ERRO" in _try(server, "listar_arquivos", aparelho="x; reboot")
    assert module.decode_reply("Result: Bundle[{ok=false, resultado=" + base64.b64encode("não".encode()).decode() + "}]") == (False, "não")

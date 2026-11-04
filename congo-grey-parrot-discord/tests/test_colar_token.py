import os
import stat
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "colar-token.sh"
# Valor falso montado na hora, para o GitHub não confundir com token de verdade.
FAKE = ".".join(["M" + "x" * 25, "Gx" + "y" * 4, "z" * 38])


def run(env_file: Path, stdin: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "CONGO_DISCORD_ENV_FILE": str(env_file)}
    return subprocess.run(["bash", str(SCRIPT)], input=stdin, text=True, capture_output=True, env=env, check=False)


def test_saves_token_without_printing_it_and_keeps_other_lines(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("DISCORD_TOKEN=\nCONGO_DISCORD_OWNER_ID=123\n", encoding="utf-8")
    result = run(env_file, f'  "{FAKE}"  \n')
    assert result.returncode == 0, result.stdout + result.stderr
    assert FAKE not in result.stdout + result.stderr
    lines = env_file.read_text(encoding="utf-8").splitlines()
    assert lines.count(f"DISCORD_TOKEN={FAKE}") == 1
    assert "CONGO_DISCORD_OWNER_ID=123" in lines
    assert not any(line == "DISCORD_TOKEN=" for line in lines)
    assert stat.S_IMODE(env_file.stat().st_mode) == 0o600


def test_refuses_wrong_input_and_leaves_file_alone(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("DISCORD_TOKEN=\n", encoding="utf-8")
    for bad in ("", "senha123", "a.b.c", "x" * 200, "$(touch pwned).aaaa.bbbbbbbbbbbbbbbbbbbbbbbb"):
        result = run(env_file, bad + "\n")
        assert result.returncode != 0
        assert env_file.read_text(encoding="utf-8") == "DISCORD_TOKEN=\n"
    assert not (tmp_path / "pwned").exists()
    assert [p.name for p in tmp_path.iterdir()] == [".env"]


def test_only_the_first_line_is_used_so_no_extra_variable_gets_in(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("DISCORD_TOKEN=\n", encoding="utf-8")
    result = run(env_file, f"{FAKE}\nCONGO_DISCORD_ALLOW_UPDATE=1\n")
    assert result.returncode == 0
    assert env_file.read_text(encoding="utf-8") == f"DISCORD_TOKEN={FAKE}\n"

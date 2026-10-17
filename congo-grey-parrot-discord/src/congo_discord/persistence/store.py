from __future__ import annotations

import sqlite3
from pathlib import Path

CORE_FEATURES = {
    "dados": "Rolagens, inclusive rolagem oculta.",
    "fichas": "Atributos guardados por jogador.",
    "iniciativa": "Ordem de turno.",
    "regras": "Consulta curta na Open5e, com a fonte.",
    "ambiente": "Som de fundo e efeito no canal de voz, a partir de arquivos locais.",
    "handout": "Envia imagem, vídeo ou arquivo no canal ou no privado.",
    "nomes": "Nomes, tavernas e boatos gerados pelo bot.",
    "agenda": "Marca a próxima sessão e registra presença.",
    "inventario": "Itens, ouro e XP do grupo.",
    "reuniao": "Entra na chamada, transcreve ao vivo e resume quem falou.",
    "arquivo": "Transcreve um áudio enviado ou lê um texto neste bot.",
    "vtt": "Envia eventos para uma mesa virtual, por link ou webhook, inclusive uma mesa que não esteja na lista.",
}


class Store:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path)
        self._conn.row_factory = sqlite3.Row
        self._migrate()

    def _migrate(self) -> None:
        self._conn.executescript(
            """
            create table if not exists features (
                key text primary key,
                description text not null,
                enabled integer not null,
                custom integer not null
            );
            create table if not exists sheets (
                guild_id text not null,
                user_id text not null,
                attribute text not null,
                modifier integer not null,
                primary key (guild_id, user_id, attribute)
            );
            create table if not exists initiative (
                guild_id text not null,
                name text not null,
                score integer not null,
                position integer not null
            );
            create table if not exists inventory (
                guild_id text not null,
                name text not null,
                amount integer not null,
                primary key (guild_id, name)
            );
            create table if not exists sessions (
                id integer primary key autoincrement,
                guild_id text not null,
                channel_id text not null,
                title text not null,
                when_text text not null
            );
            create table if not exists rsvps (
                session_id integer not null,
                user_id text not null,
                status text not null,
                primary key (session_id, user_id)
            );
            create table if not exists vtt_links (
                guild_id text primary key,
                name text not null,
                url text not null,
                token text not null,
                known integer not null
            );
            create table if not exists utterances (
                id integer primary key autoincrement,
                guild_id text not null,
                speaker text not null,
                body text not null,
                when_text text not null
            );
            """
        )
        for key, description in CORE_FEATURES.items():
            enabled = 0 if key == "reuniao" else 1
            self._conn.execute(
                """
                insert into features (key, description, enabled, custom)
                values (?, ?, ?, 0)
                on conflict(key) do update set description = excluded.description
                """,
                (key, description, enabled),
            )
        self._conn.commit()

    def features(self) -> list[sqlite3.Row]:
        return list(self._conn.execute("select key, description, enabled, custom from features order by key"))

    def enabled(self, key: str) -> bool:
        row = self._conn.execute("select enabled from features where key = ?", (key,)).fetchone()
        return bool(row and row["enabled"])

    def set_enabled(self, key: str, enabled: bool) -> bool:
        cursor = self._conn.execute(
            "update features set enabled = ? where key = ?",
            (1 if enabled else 0, key),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def add_custom(self, key: str, description: str) -> None:
        self._conn.execute(
            """
            insert into features (key, description, enabled, custom)
            values (?, ?, 0, 1)
            on conflict(key) do update set description = excluded.description
            """,
            (key, description),
        )
        self._conn.commit()

    def remove_custom(self, key: str) -> bool:
        cursor = self._conn.execute("delete from features where key = ? and custom = 1", (key,))
        self._conn.commit()
        return cursor.rowcount > 0

    def set_attribute(self, guild_id: str, user_id: str, attribute: str, modifier: int) -> None:
        self._conn.execute(
            """
            insert into sheets (guild_id, user_id, attribute, modifier)
            values (?, ?, ?, ?)
            on conflict(guild_id, user_id, attribute) do update set modifier = excluded.modifier
            """,
            (guild_id, user_id, attribute.lower(), modifier),
        )
        self._conn.commit()

    def attribute(self, guild_id: str, user_id: str, attribute: str) -> int | None:
        row = self._conn.execute(
            "select modifier from sheets where guild_id = ? and user_id = ? and attribute = ?",
            (guild_id, user_id, attribute.lower()),
        ).fetchone()
        if row is None:
            return None
        return int(row["modifier"])

    def sheet(self, guild_id: str, user_id: str) -> list[sqlite3.Row]:
        return list(
            self._conn.execute(
                "select attribute, modifier from sheets where guild_id = ? and user_id = ? order by attribute",
                (guild_id, user_id),
            )
        )

    def clear_initiative(self, guild_id: str) -> None:
        self._conn.execute("delete from initiative where guild_id = ?", (guild_id,))
        self._conn.commit()

    def add_initiative(self, guild_id: str, name: str, score: int) -> None:
        self._conn.execute("delete from initiative where guild_id = ? and name = ?", (guild_id, name))
        self._conn.execute(
            "insert into initiative (guild_id, name, score, position) values (?, ?, ?, 0)",
            (guild_id, name, score),
        )
        rows = list(
            self._conn.execute(
                "select rowid from initiative where guild_id = ? order by score desc, name",
                (guild_id,),
            )
        )
        for index, row in enumerate(rows):
            self._conn.execute("update initiative set position = ? where rowid = ?", (index, row["rowid"]))
        self._conn.commit()

    def next_initiative(self, guild_id: str) -> sqlite3.Row | None:
        rows = self.initiative(guild_id)
        if not rows:
            return None
        total = len(rows)
        for row in rows:
            position = int(row["position"]) - 1
            if position < 0:
                position = total - 1
            self._conn.execute(
                "update initiative set position = ? where guild_id = ? and name = ?",
                (position, guild_id, row["name"]),
            )
        self._conn.commit()
        return rows[0]

    def initiative(self, guild_id: str) -> list[sqlite3.Row]:
        return list(
            self._conn.execute(
                "select name, score, position from initiative where guild_id = ? order by position",
                (guild_id,),
            )
        )

    def add_item(self, guild_id: str, name: str, amount: int) -> int:
        current = self._conn.execute(
            "select amount from inventory where guild_id = ? and name = ?",
            (guild_id, name.lower()),
        ).fetchone()
        total = amount + (int(current["amount"]) if current else 0)
        self._conn.execute(
            """
            insert into inventory (guild_id, name, amount) values (?, ?, ?)
            on conflict(guild_id, name) do update set amount = excluded.amount
            """,
            (guild_id, name.lower(), total),
        )
        self._conn.commit()
        return total

    def inventory(self, guild_id: str) -> list[sqlite3.Row]:
        return list(
            self._conn.execute(
                "select name, amount from inventory where guild_id = ? order by name",
                (guild_id,),
            )
        )

    def add_session(self, guild_id: str, channel_id: str, title: str, when_text: str) -> int:
        cursor = self._conn.execute(
            "insert into sessions (guild_id, channel_id, title, when_text) values (?, ?, ?, ?)",
            (guild_id, channel_id, title, when_text),
        )
        self._conn.commit()
        return int(cursor.lastrowid)

    def all_sessions(self) -> list[sqlite3.Row]:
        return list(self._conn.execute("select id from sessions order by id desc limit 30"))

    def sessions(self, guild_id: str) -> list[sqlite3.Row]:
        return list(
            self._conn.execute(
                "select id, title, when_text from sessions where guild_id = ? order by id desc",
                (guild_id,),
            )
        )

    def rsvp(self, session_id: int, user_id: str, status: str) -> None:
        self._conn.execute(
            """
            insert into rsvps (session_id, user_id, status) values (?, ?, ?)
            on conflict(session_id, user_id) do update set status = excluded.status
            """,
            (session_id, user_id, status),
        )
        self._conn.commit()

    def rsvp_counts(self, session_id: int) -> dict[str, int]:
        rows = self._conn.execute(
            "select status, count(*) as total from rsvps where session_id = ? group by status",
            (session_id,),
        )
        return {row["status"]: int(row["total"]) for row in rows}

    def add_utterance(self, guild_id: str, speaker: str, body: str, when_text: str) -> None:
        self._conn.execute(
            "insert into utterances (guild_id, speaker, body, when_text) values (?, ?, ?, ?)",
            (guild_id, speaker, body, when_text),
        )
        self._conn.commit()

    def utterances(self, guild_id: str) -> list[sqlite3.Row]:
        return list(
            self._conn.execute(
                "select speaker, body, when_text from utterances where guild_id = ? order by id",
                (guild_id,),
            )
        )

    def clear_utterances(self, guild_id: str) -> None:
        self._conn.execute("delete from utterances where guild_id = ?", (guild_id,))
        self._conn.commit()

    def set_vtt(self, guild_id: str, name: str, url: str, token: str, known: bool) -> None:
        self._conn.execute(
            """
            insert into vtt_links (guild_id, name, url, token, known)
            values (?, ?, ?, ?, ?)
            on conflict(guild_id) do update set
                name = excluded.name,
                url = excluded.url,
                token = excluded.token,
                known = excluded.known
            """,
            (guild_id, name, url, token, 1 if known else 0),
        )
        self._conn.commit()

    def vtt(self, guild_id: str) -> sqlite3.Row | None:
        return self._conn.execute(
            "select name, url, token, known from vtt_links where guild_id = ?",
            (guild_id,),
        ).fetchone()

    def clear_vtt(self, guild_id: str) -> bool:
        cursor = self._conn.execute("delete from vtt_links where guild_id = ?", (guild_id,))
        self._conn.commit()
        return cursor.rowcount > 0

    def close(self) -> None:
        self._conn.close()

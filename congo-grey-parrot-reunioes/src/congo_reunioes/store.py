from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from congo_reunioes.parse import SpokenLine


class NoteStore:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(
            """
            create table if not exists lines (
                id integer primary key autoincrement,
                platform text not null,
                speaker text not null,
                body text not null,
                when_text text not null,
                imported_at text not null
            )
            """
        )
        self._conn.commit()

    def add(self, platform: str, lines: list[SpokenLine]) -> int:
        moment = datetime.now().isoformat(timespec="seconds")
        for line in lines:
            self._conn.execute(
                "insert into lines (platform, speaker, body, when_text, imported_at) values (?, ?, ?, ?, ?)",
                (platform, line.speaker, line.text, line.when, moment),
            )
        self._conn.commit()
        return len(lines)

    def lines(self, platform: str | None = None) -> list[SpokenLine]:
        if platform:
            rows = self._conn.execute(
                "select speaker, body, when_text from lines where platform = ? order by id",
                (platform,),
            )
        else:
            rows = self._conn.execute("select speaker, body, when_text from lines order by id")
        return [SpokenLine(row["speaker"], row["body"], row["when_text"]) for row in rows]

    def clear(self, platform: str | None = None) -> None:
        if platform:
            self._conn.execute("delete from lines where platform = ?", (platform,))
        else:
            self._conn.execute("delete from lines")
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

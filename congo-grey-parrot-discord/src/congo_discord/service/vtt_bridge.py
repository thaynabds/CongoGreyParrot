from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def check_table_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("O endereço precisa começar com http:// ou https://.")
    if len(url) > 500:
        raise ValueError("O endereço passou de 500 caracteres.")
    return url.strip()


def post_event(url: str, token: str, payload: dict, opener=urlopen) -> tuple[int, str]:
    safe_url = check_table_url(url)
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "CongoGreyParrotDiscord/0.1",
    }
    if token:
        headers["Authorization"] = "Bearer " + token
    request = Request(safe_url, data=data, headers=headers, method="POST")
    try:
        with opener(request, timeout=8) as response:
            body = response.read(400).decode("utf-8", errors="replace")
            return int(getattr(response, "status", 200)), body
    except HTTPError as exc:
        detail = exc.read(300).decode("utf-8", errors="replace")
        return int(exc.code), detail or str(exc.reason)
    except URLError as exc:
        raise ValueError(f"Não alcançou a mesa: {exc.reason}") from exc

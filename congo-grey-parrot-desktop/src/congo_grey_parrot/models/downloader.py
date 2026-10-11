from __future__ import annotations

import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from congo_grey_parrot.core.errors import AppError

ALLOWED_SUFFIXES = (
    "huggingface.co",
    "hf.co",
    "github.com",
    "githubusercontent.com",
)


def host_allowed(host: str) -> bool:
    name = (host or "").lower().split(":")[0]
    return any(name == suffix or name.endswith("." + suffix) for suffix in ALLOWED_SUFFIXES)


def validate_download_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme != "https" or not parsed.netloc or not parsed.path:
        raise AppError("O download só aceita endereço HTTPS completo.")
    if not host_allowed(parsed.hostname or ""):
        raise AppError("A origem desse download não está na lista permitida.")
    return url.strip()


class _GuardedRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_download_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download_file(url: str, destination: Path, progress, cancel) -> Path:
    checked = validate_download_url(url)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".part")
    request = urllib.request.Request(checked, headers={"User-Agent": "CongoGreyParrot/0.1"})
    opener = urllib.request.build_opener(_GuardedRedirect)
    try:
        with opener.open(request, timeout=60) as response:
            final = response.geturl()
            validate_download_url(final)
            total = int(response.headers.get("Content-Length") or 0)
            done = 0
            with temporary.open("wb") as handle:
                while True:
                    if cancel is not None and cancel.is_set():
                        raise AppError("Download cancelado.")
                    chunk = response.read(256 * 1024)
                    if not chunk:
                        break
                    handle.write(chunk)
                    done += len(chunk)
                    if progress is not None:
                        progress(done, total)
    except AppError:
        temporary.unlink(missing_ok=True)
        raise
    except urllib.error.URLError as exc:
        temporary.unlink(missing_ok=True)
        raise AppError(f"Falha no download. {exc.reason}") from exc
    temporary.replace(destination)
    return destination

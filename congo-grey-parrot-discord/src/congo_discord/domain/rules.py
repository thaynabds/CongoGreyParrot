from __future__ import annotations


def spell_text(payload: dict) -> str:
    results = payload.get("results") or []
    if not results:
        return "Nenhum resultado nessa consulta. A busca usa a Open5e e não guarda o livro no bot."
    item = results[0]
    name = str(item.get("name") or "Sem nome")
    level = item.get("level", "")
    desc = item.get("desc") or ""
    if isinstance(desc, list):
        desc = " ".join(str(part) for part in desc)
    desc = " ".join(str(desc).split())
    if len(desc) > 700:
        desc = desc[:700].rstrip() + "..."
    document = item.get("document") or {}
    source = document.get("title") or document.get("url") or "Open5e"
    return (
        f"{name} (nível {level}). {desc}\n"
        f"Fonte: {source}. Consulta pela Open5e, sem copiar o livro para o repositório. "
        "https://open5e.com/"
    )

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class KnownVtt:
    key: str
    name: str
    site: str
    note: str


# Só entram endereços públicos estáveis. Onde a API externa não está confirmada, o texto diz isso.
# O conector genérico aceita qualquer outro nome.
KNOWN_VTTS = (
    KnownVtt("roll20", "Roll20", "https://roll20.net/", "A API do Roll20 roda dentro da campanha, não como login externo. https://wiki.roll20.net/API:Introduction"),
    KnownVtt("owlbear", "Owlbear Rodeo", "https://www.owlbear.rodeo/", "Extensões rodam dentro da sala. https://docs.owlbear.rodeo/"),
    KnownVtt("alchemy", "Alchemy RPG", "https://www.alchemyrpg.com/", "Não confirmei uma API pública para um bot externo."),
    KnownVtt("foundry", "Foundry VTT", "https://foundryvtt.com/", "No mesmo computador do bot, ative o módulo Congo Grey Parrot. https://foundryvtt.com/article/module-development/"),
    KnownVtt("fantasygrounds", "Fantasy Grounds Unity", "https://www.fantasygrounds.com/", "A automação fica no programa. Não confirmei uma API pública para um bot externo."),
    KnownVtt("talespire", "TaleSpire", "https://talespire.com/", "Não confirmei uma API pública para um bot externo."),
    KnownVtt("bagofmapping", "Bag of Mapping", "", "Não confirmei o endereço nem uma API pública."),
    KnownVtt("questline", "Questline VTT", "", "Não confirmei o endereço nem uma API pública."),
    KnownVtt("shard", "Shard Tabletop", "", "Não confirmei o endereço nem uma API pública."),
    KnownVtt("onemoremultiverse", "One More Multiverse", "", "Não confirmei o endereço nem uma API pública."),
    KnownVtt("mirrorscape", "Mirrorscape", "", "Não confirmei o endereço nem uma API pública."),
    KnownVtt("tabletopsimulator", "Tabletop Simulator", "https://www.tabletopsimulator.com/", "Não confirmei uma API pública para um bot externo."),
    KnownVtt("maptool", "MapTool", "https://www.rptools.net/toolbox/maptool/", "Programa local e de código aberto. Não confirmei uma API pública para um bot externo."),
    KnownVtt("astral", "Astral Tabletop", "", "Não confirmei o endereço nem uma API pública."),
    KnownVtt("rpgpedia", "RPG Pédia", "", "Não confirmei o endereço nem uma API pública."),
    KnownVtt("worldcraft", "Worldcraft", "", "Não confirmei o endereço nem uma API pública."),
    KnownVtt("rpkast", "RPKast", "", "Não confirmei o endereço nem uma API pública."),
    KnownVtt("tableplop", "Tableplop", "", "Não confirmei o endereço nem uma API pública."),
    KnownVtt("shmeppy", "Shmeppy", "https://shmeppy.com/", "Não confirmei uma API pública para um bot externo."),
    KnownVtt("fari", "Fari App", "https://fari.app/", "Código aberto, focado em jogos narrativos. Não confirmei uma API pública para um bot externo."),
    KnownVtt("dungeonfulldive", "Dungeon Full Dive", "", "Não confirmei o endereço nem uma API pública."),
    KnownVtt("rpgengine", "The RPG Engine", "", "Não confirmei o endereço nem uma API pública."),
    KnownVtt("role", "Role", "", "Não confirmei o endereço nem uma API pública."),
    KnownVtt("questportal", "Quest Portal", "https://www.questportal.com/", "Não confirmei uma API pública para um bot externo."),
)


def find_vtt(name: str) -> KnownVtt | None:
    key = "".join(character for character in name.lower() if character.isalnum())
    for item in KNOWN_VTTS:
        if item.key == key or item.name.lower() == name.strip().lower():
            return item
    return None


def catalog_text() -> str:
    lines = [
        "Mesas conhecidas. O bot não entra na conta delas.",
        "Para qualquer uma, e para uma mesa que não esteja aqui, use /vtt conectar com o link da sala ou com o webhook do módulo.",
    ]
    for item in KNOWN_VTTS:
        site = f" {item.site}" if item.site else ""
        lines.append(f"{item.name}.{site} {item.note}")
    return "\n".join(lines)

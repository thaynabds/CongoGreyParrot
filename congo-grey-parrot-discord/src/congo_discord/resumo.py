"""Resumo local de texto, sem IA e sem internet.

O resumo só escolhe frases que já estão no texto: nada é inventado nem reescrito.
Funciona em português, inglês e espanhol.

Este arquivo é igual nos pacotes do computador, do bot e das reuniões.
Mude os três juntos; o teste test_resumo_copies_are_identical confere.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

# Limite contra texto gigante: acima disso, o resumo usa só o começo e avisa.
MAX_CHARS = 400_000
MAX_SENTENCES = 30
_MAX_SENTENCE_CHARS = 600
_MAX_ITEMS = 6

_SPLIT = re.compile(r"(?<=[.!?…])\s+|\n+")
_WORD = re.compile(r"[^\W\d_]{3,}", re.UNICODE)
_SPEAKER = re.compile(r"^(?:\[[^\]\n]{1,20}\]\s*)?([^:\n]{1,60}):\s+(\S.*)$")

_STOPWORDS = frozenset(
    """
    que não uma para com por mais como mas foi são ser tem você vocês ele ela eles elas isso isto esse essa
    este esta aqui ali então também muito muita já quando onde porque pra pro dos das nos nas num numa
    está estão estava era eram ter tinha vai vou vamos sim seu sua seus suas meu minha nosso nossa
    pelo pela pelos pelas sobre entre até depois antes ainda só sem tudo nada cada qual quem lhe
    gente coisa acho assim aí né tá aquele aquela the and that this with for are was were have has had
    you your they them their there here what when where which who will would could should about from
    into just also been being not but our out can all any some than then its it's i'm don't yes okay
    del los las por con para una uno unos unas como pero más este esta esto ese esa eso aquí allí
    también muy ya cuando donde porque sí sus mis nuestro nuestra está están era fue ser hay tiene
    vamos todo nada cada quien entonces bueno
    """.split()
)

_DECISION = re.compile(
    r"\b(decidi(?:mos|do|da|u)|ficou (?:decidido|definido|combinado)|combina(?:mos|do)|aprova(?:mos|do|da)|"
    r"fica definido|fechamos|decided|agreed|we will go with|approved|acordamos|queda (?:decidido|acordado)|"
    r"aprobado)\b",
    re.IGNORECASE,
)
_TASK = re.compile(
    r"\b(vou (?:fazer|mandar|enviar|ver|criar|preparar|revisar|ligar)|fica com|responsável|prazo|"
    r"até (?:amanhã|segunda|terça|quarta|quinta|sexta|sábado|domingo|o dia|dia)|preciso que|pode (?:fazer|mandar|enviar)|"
    r"tarefa|próximos passos|i'll|i will|will send|action item|deadline|next steps|by (?:monday|tuesday|wednesday|"
    r"thursday|friday|tomorrow)|voy a|me encargo|plazo|hasta el|próximos pasos)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Resumo:
    frases: list[str]
    decisoes: list[str] = field(default_factory=list)
    tarefas: list[str] = field(default_factory=list)
    perguntas: list[str] = field(default_factory=list)
    palavras: list[str] = field(default_factory=list)
    total: int = 0
    cortado: bool = False

    def to_dict(self) -> dict:
        return {
            "frases": self.frases,
            "decisoes": self.decisoes,
            "tarefas": self.tarefas,
            "perguntas": self.perguntas,
            "palavras_chave": self.palavras,
            "frases_no_texto": self.total,
            "texto_cortado": self.cortado,
        }


def resumir(texto: str, frases: int = 0) -> Resumo:
    """Resume um texto corrido ou uma transcrição com linhas "Nome: fala"."""
    texto = str(texto or "")
    cortado = len(texto) > MAX_CHARS
    texto = texto[:MAX_CHARS]
    pares: list[tuple[str, str]] = []
    for linha in texto.replace("\r\n", "\n").split("\n"):
        linha = linha.strip()
        if not linha:
            continue
        match = _SPEAKER.match(linha)
        if match and not match.group(1)[-1:].isdigit():
            pares.append((match.group(1).strip(), match.group(2)))
        else:
            pares.append(("", linha))
    return _resumir_unidades(_unidades(pares), frases, cortado)


def resumir_falas(falas: Iterable[tuple[str, str]], frases: int = 0) -> Resumo:
    """Resume falas já separadas por pessoa, como as das reuniões."""
    pares: list[tuple[str, str]] = []
    usado = 0
    cortado = False
    for pessoa, fala in falas:
        fala = str(fala or "")
        usado += len(fala)
        if usado > MAX_CHARS:
            cortado = True
            break
        pares.append((str(pessoa or "").strip()[:60], fala))
    return _resumir_unidades(_unidades(pares), frases, cortado)


def _unidades(pares: list[tuple[str, str]]) -> list[tuple[str, str]]:
    unidades: list[tuple[str, str]] = []
    for pessoa, texto in pares:
        for frase in _SPLIT.split(texto):
            frase = " ".join(frase.split())
            if len(frase) < 3:
                continue
            if len(frase) > _MAX_SENTENCE_CHARS:
                frase = frase[:_MAX_SENTENCE_CHARS].rstrip() + "…"
            unidades.append((pessoa, frase))
    return unidades


def _palavras(frase: str) -> list[str]:
    return [palavra for palavra in (p.lower() for p in _WORD.findall(frase)) if palavra not in _STOPWORDS]


def _resumir_unidades(unidades: list[tuple[str, str]], frases: int, cortado: bool) -> Resumo:
    if not unidades:
        return Resumo(frases=[], total=0, cortado=cortado)
    frequencia: dict[str, int] = {}
    palavras_por_frase = []
    for _, frase in unidades:
        palavras = _palavras(frase)
        palavras_por_frase.append(palavras)
        for palavra in palavras:
            frequencia[palavra] = frequencia.get(palavra, 0) + 1
    maior = max(frequencia.values(), default=1)

    def nota(indice: int) -> float:
        palavras = palavras_por_frase[indice]
        if len(palavras) < 3:
            return 0.0
        unicas = set(palavras)
        valor = sum(frequencia[p] / maior for p in unicas) / (len(unicas) ** 0.5)
        if _DECISION.search(unidades[indice][1]) or _TASK.search(unidades[indice][1]):
            valor *= 1.3
        return valor

    total = len(unidades)
    quantidade = frases if frases > 0 else max(3, min(8, round(total * 0.2)))
    quantidade = min(quantidade, MAX_SENTENCES, total)
    notas = sorted(range(total), key=lambda i: (-nota(i), i))
    escolhidas = sorted(i for i in notas[:quantidade] if nota(i) > 0) or list(range(min(quantidade, total)))

    def mostrar(indice: int) -> str:
        pessoa, frase = unidades[indice]
        return f"{pessoa}: {frase}" if pessoa else frase

    decisoes = _unicos(mostrar(i) for i in range(total) if _DECISION.search(unidades[i][1]))
    tarefas = _unicos(
        mostrar(i) for i in range(total) if _TASK.search(unidades[i][1]) and not unidades[i][1].endswith("?")
    )
    perguntas = _unicos(
        mostrar(i) for i in range(total) if unidades[i][1].endswith("?") and len(palavras_por_frase[i]) >= 2
    )
    chave = [p for p, _ in sorted(frequencia.items(), key=lambda item: (-item[1], item[0])) if frequencia[p] > 1][:8]
    return Resumo(
        frases=[mostrar(i) for i in escolhidas],
        decisoes=decisoes,
        tarefas=tarefas,
        perguntas=perguntas,
        palavras=chave,
        total=total,
        cortado=cortado,
    )


def _unicos(itens: Iterable[str]) -> list[str]:
    vistos: list[str] = []
    for item in itens:
        if item not in vistos:
            vistos.append(item)
        if len(vistos) >= _MAX_ITEMS:
            break
    return vistos


def resumo_texto(resumo: Resumo, titulo: str = "Resumo") -> str:
    if not resumo.frases:
        return "Não há texto para resumir."
    partes = [f"{titulo} ({len(resumo.frases)} de {resumo.total} frases, escolhidas do próprio texto):"]
    partes.extend(f"- {frase}" for frase in resumo.frases)
    for nome, itens in (("Decisões", resumo.decisoes), ("Tarefas", resumo.tarefas), ("Perguntas", resumo.perguntas)):
        if itens:
            partes.append("")
            partes.append(f"{nome}:")
            partes.extend(f"- {item}" for item in itens)
    if resumo.palavras:
        partes.append("")
        partes.append("Palavras que mais aparecem: " + ", ".join(resumo.palavras))
    if resumo.cortado:
        partes.append("")
        partes.append(f"O texto passou de {MAX_CHARS} caracteres; o resumo usou só o começo.")
    return "\n".join(partes)

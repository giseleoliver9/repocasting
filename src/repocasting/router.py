from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import tomllib
import unicodedata


@dataclass(frozen=True)
class Specialist:
    id: str
    name: str
    instruction: str
    keywords: dict[str, int]


def words(value: str) -> tuple[str, ...]:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    normalized = "".join(c for c in normalized if not unicodedata.combining(c))
    return tuple(re.findall(r"[^\W_]+", normalized))


def load_profiles(path: Path) -> list[Specialist]:
    if path.stat().st_size > 256_000:
        raise ValueError("configuração maior que 256 KB")
    with path.open("rb") as stream:
        entries = tomllib.load(stream).get("specialists")
    if not isinstance(entries, list) or not 1 <= len(entries) <= 50:
        raise ValueError("defina de 1 a 50 perfis [[specialists]]")
    profiles = []
    ids = set()
    for item in entries:
        if not isinstance(item, dict) or set(item) != {"id", "name", "instruction", "keywords"}:
            raise ValueError("cada perfil precisa de id, name, instruction e keywords")
        identifier, name, instruction = (item[k] for k in ("id", "name", "instruction"))
        if not isinstance(identifier, str) or not re.fullmatch(r"[a-z][a-z0-9-]{0,49}", identifier):
            raise ValueError("id inválido")
        if identifier in ids:
            raise ValueError("id duplicado")
        if any(not isinstance(v, str) or not v.strip() for v in (name, instruction)):
            raise ValueError("nome e instrução não podem estar vazios")
        keywords = item["keywords"]
        if not isinstance(keywords, dict) or not 1 <= len(keywords) <= 50:
            raise ValueError("defina de 1 a 50 palavras-chave para cada perfil")
        seen_keywords = set()
        for key, weight in keywords.items():
            normalized = words(key)
            if not normalized or normalized in seen_keywords or type(weight) is not int or not 1 <= weight <= 10:
                raise ValueError("palavra-chave inválida, duplicada após normalização ou peso fora de 1–10")
            seen_keywords.add(normalized)
        ids.add(identifier)
        profiles.append(Specialist(identifier, name, instruction, keywords))
    return profiles


def route(task: str, profiles: list[Specialist]) -> dict:
    task_words = words(task)
    if not task_words:
        raise ValueError("informe uma tarefa com pelo menos uma palavra")
    scores = []
    for profile in profiles:
        matches = []
        for key, weight in sorted(profile.keywords.items()):
            key_words = words(key)
            if any(task_words[i:i + len(key_words)] == key_words
                   for i in range(len(task_words) - len(key_words) + 1)):
                matches.append({"keyword": key, "weight": weight})
        if matches:
            scores.append({"id": profile.id, "name": profile.name, "instruction": profile.instruction,
                           "score": sum(m["weight"] for m in matches), "matches": matches})
    scores.sort(key=lambda item: (-item["score"], item["id"]))
    state = ("sem-sinal" if not scores else "empate" if len(scores)>1 and
             scores[0]["score"] == scores[1]["score"] else "recomendado")
    return {"mode": "simulacao-de-roteamento", "status": state,
            "recommended": scores[0]["id"] if state == "recomendado" else None,
            "candidates": scores, "executed": False}

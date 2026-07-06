from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Source:
    id: str
    name: str
    url: str
    importance: int


@dataclass(frozen=True)
class SectorRule:
    name: str
    tickers: list[str]
    keywords: list[str]


def load_sources(path: Path) -> list[Source]:
    payload = _load_yaml(path)
    sources = payload.get("sources", [])
    return [
        Source(
            id=str(item["id"]),
            name=str(item["name"]),
            url=str(item["url"]),
            importance=int(item.get("importance", 1)),
        )
        for item in sources
    ]


def load_sector_rules(path: Path) -> list[SectorRule]:
    payload = _load_yaml(path)
    sectors = payload.get("sectors", {})
    return [
        SectorRule(
            name=str(name),
            tickers=[str(ticker).upper() for ticker in values.get("tickers", [])],
            keywords=[str(keyword).lower() for keyword in values.get("keywords", [])],
        )
        for name, values in sectors.items()
    ]


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"Expected YAML object in {path}")
    return payload

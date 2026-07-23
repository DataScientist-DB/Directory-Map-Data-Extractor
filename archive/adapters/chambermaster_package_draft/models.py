from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AdapterInfo:
    key: str
    name: str
    version: str
    author: str = "Adinfosys"
    website: str = ""
    description: str = ""

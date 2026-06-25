from __future__ import annotations

from typing import Optional

from src.adapters.base import BaseDirectoryAdapter
from src.adapters.chambermaster import ChamberMasterAdapter


def get_adapter(
    architecture: str,
    source_url: str = "",
    debug: bool = False,
) -> Optional[BaseDirectoryAdapter]:
    architecture = (architecture or "").lower().strip()

    if architecture == "chambermaster":
        return ChamberMasterAdapter(source_url=source_url, debug=debug)

    return None

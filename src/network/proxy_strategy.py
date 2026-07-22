from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ProxyStrategy(ABC):
    @abstractmethod
    async def build_proxy_settings(self) -> dict[str, Any] | None:
        raise NotImplementedError

import inspect
from typing import Any, List, Optional, Sequence

from src.adapters.providers.execution import ProviderExecutionResult
from src.adapters.providers.registry import ProviderRegistry


class ProviderOrchestrator:
    """
    Execute search-capable providers and collect their results.

    RC1.7 initially uses sequential execution for predictable behavior.
    """

    def __init__(self, registry: ProviderRegistry) -> None:
        self.registry = registry

    async def search(
        self,
        request: Any,
        provider_names: Optional[Sequence[str]] = None,
        *,
        stop_on_error: bool = False,
    ) -> List[ProviderExecutionResult]:

        if provider_names:
            providers = [
                self.registry.select(
                    name=name,
                    capability="search",
                )
                for name in provider_names
            ]
        else:
            providers = self.registry.by_capability("search")

        results: List[ProviderExecutionResult] = []

        for provider in providers:
            name = provider.provider_name()

            try:
                response = provider.search(request)

                if inspect.isawaitable(response):
                    response = await response

                records = self._normalize_records(response)

                results.append(
                    ProviderExecutionResult(
                        provider_name=name,
                        status="success",
                        records=records,
                    )
                )

            except Exception as exc:
                results.append(
                    ProviderExecutionResult(
                        provider_name=name,
                        status="failed",
                        records=[],
                        error=str(exc),
                    )
                )

                if stop_on_error:
                    raise

        return results

    @staticmethod
    def _normalize_records(response: Any) -> List[Any]:
        if response is None:
            return []

        if isinstance(response, list):
            return response

        if isinstance(response, tuple):
            return list(response)

        return [response]

    @staticmethod
    def flatten_records(
        results: List[ProviderExecutionResult],
    ) -> List[Any]:
        records: List[Any] = []

        for result in results:
            if result.status == "success":
                records.extend(result.records)

        return records

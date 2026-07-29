import inspect
from typing import Any, List, Optional, Sequence

from src.adapters.providers.execution import ProviderExecutionResult
from src.adapters.providers.registry import ProviderRegistry
from src.models.provider_result import ProviderResult
from src.models.provider_status import ProviderStatus


class ProviderOrchestrator:
    """
    Execute search-capable providers and collect their results.

    Supports both legacy providers returning records directly and
    structured providers returning ProviderResult.
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

                if isinstance(response, ProviderResult):
                    results.append(
                        ProviderExecutionResult(
                            provider_name=name,
                            status=response.report.status,
                            records=response.records,
                            error=response.report.reason or None,
                            report=response.report,
                            requires_fallback=response.should_fallback,
                        )
                    )
                    continue

                records = self._normalize_records(response)

                results.append(
                    ProviderExecutionResult(
                        provider_name=name,
                        status=ProviderStatus.SUCCESS.value,
                        records=records,
                    )
                )

            except Exception as exc:
                results.append(
                    ProviderExecutionResult(
                        provider_name=name,
                        status=ProviderStatus.FAILED.value,
                        records=[],
                        error=str(exc),
                        requires_fallback=True,
                    )
                )

                if stop_on_error:
                    raise

        return results

    async def search_with_fallback(
        self,
        request: Any,
        *,
        primary_name: str,
        fallback_name: str,
        fallback_enabled: bool = True,
    ) -> List[ProviderExecutionResult]:
        """
        Run a primary provider and conditionally execute its fallback.

        Structured ProviderResult responses control fallback through
        ProviderReport.should_fallback. Exceptions also request fallback.
        """

        results = await self.search(
            request,
            provider_names=[primary_name],
        )

        if not results:
            return results

        primary_result = results[0]

        if (
            fallback_enabled
            and primary_result.requires_fallback
        ):
            fallback_results = await self.search(
                request,
                provider_names=[fallback_name],
            )
            results.extend(fallback_results)

        return results

    async def search_directory(
        self,
        request: Any,
        *,
        directory: str,
        requested_provider_names: Optional[Sequence[str]] = None,
        local_only: bool = False,
    ) -> List[ProviderExecutionResult]:
        """
        Execute a directory's provider chain in registry priority order.

        A successful or terminal result stops the chain. A result marked
        ``requires_fallback`` advances to the next eligible provider.
        ``local_only`` excludes providers whose metadata identifies an
        external access strategy.
        """
        requested = {
            str(name).strip().casefold()
            for name in (requested_provider_names or [])
            if str(name).strip()
        }

        providers = self.registry.providers_for_directory(
            directory,
            capability="search",
        )

        eligible = []
        for provider in providers:
            name = provider.provider_name().strip().casefold()
            if requested and name not in requested:
                continue

            metadata = provider.metadata() or {}
            access_strategy = str(
                metadata.get("access_strategy") or ""
            ).strip().casefold()

            if local_only and access_strategy in {
                "external",
                "external_actor",
                "remote_actor",
                "remote_api",
            }:
                continue

            eligible.append(provider)

        results: List[ProviderExecutionResult] = []

        for provider in eligible:
            provider_results = await self.search(
                request,
                provider_names=[provider.provider_name()],
            )
            if not provider_results:
                continue

            result = provider_results[0]
            results.append(result)

            if not result.requires_fallback:
                break

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
            if result.status == ProviderStatus.SUCCESS.value:
                records.extend(result.records)

        return records

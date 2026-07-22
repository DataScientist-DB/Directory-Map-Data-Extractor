from __future__ import annotations

from enum import Enum


class ProviderStatus(str, Enum):
    SUCCESS = "success"
    EMPTY = "empty"
    BLOCKED = "blocked"
    DEMO = "demo"

    AUTHENTICATION_FAILED = "authentication_failed"
    RENTAL_REQUIRED = "rental_required"
    ACTOR_UNAVAILABLE = "actor_unavailable"

    INPUT_ERROR = "input_error"
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"
    NETWORK_ERROR = "network_error"
    NOT_SUPPORTED = "not_supported"

    RUNTIME_ERROR = "runtime_error"
    FAILED = "failed"

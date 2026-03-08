from __future__ import annotations
from datetime import datetime, timezone
from abc import ABC, abstractmethod


class IOrderReferenceGenerator(ABC):
    @abstractmethod
    def next_reference(self) -> str:
        ...


class DateSequenceReferenceGenerator(IOrderReferenceGenerator):
    """Generates references in format OT-YYYYMMDD-XXXX."""

    def __init__(self, count_today_fn) -> None:
        """
        count_today_fn: callable(prefix: str) -> int
            Returns number of existing orders with the given prefix.
        """
        self._count_today = count_today_fn

    def next_reference(self) -> str:
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        prefix = f"OT-{today}-"
        count = self._count_today(prefix)
        return f"{prefix}{count + 1:04d}"

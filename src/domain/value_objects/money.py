
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = "IDR"

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            # Coerce int/float to Decimal for convenience, but callers should
            # prefer passing Decimal directly to avoid precision surprises.
            object.__setattr__(self, "amount", Decimal(str(self.amount)))
        if self.amount < Decimal("0"):
            raise ValueError(
                f"Money amount cannot be negative: {self.amount}"
            )
        if not self.currency or not self.currency.strip():
            raise ValueError("Money currency cannot be empty")

    def __add__(self, other: Money) -> Money:
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot add Money with different currencies: "
                f"{self.currency} and {other.currency}"
            )
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def __mul__(self, factor: int) -> Money:
        if not isinstance(factor, int) or factor < 0:
            raise ValueError(
                f"Money can only be multiplied by a non-negative integer, got: {factor}"
            )
        return Money(amount=self.amount * factor, currency=self.currency)

    def __repr__(self) -> str:
        return f"Money(amount={self.amount}, currency={self.currency!r})"

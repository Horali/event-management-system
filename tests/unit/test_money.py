"""Unit tests for the Money Value Object.

Validate-first: negative/error cases before positive cases.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.domain.value_objects.money import Money


class TestMoneyValidation:
    """Negative cases — invalid Money construction."""

    def test_negative_amount_raises(self) -> None:
        with pytest.raises(ValueError, match="cannot be negative"):
            Money(amount=Decimal("-1"))

    def test_negative_amount_small_raises(self) -> None:
        with pytest.raises(ValueError, match="cannot be negative"):
            Money(amount=Decimal("-0.01"))

    def test_empty_currency_raises(self) -> None:
        with pytest.raises(ValueError, match="currency cannot be empty"):
            Money(amount=Decimal("100"), currency="")

    def test_whitespace_currency_raises(self) -> None:
        with pytest.raises(ValueError, match="currency cannot be empty"):
            Money(amount=Decimal("100"), currency="   ")

    # Property-based: any negative Decimal must be rejected
    @settings(max_examples=200)
    @given(st.decimals(max_value=Decimal("-0.01"), allow_nan=False, allow_infinity=False))
    def test_any_negative_decimal_raises(self, amount: Decimal) -> None:
        with pytest.raises(ValueError):
            Money(amount=amount)


class TestMoneyPositiveCases:
    """Positive cases — valid Money construction and operations."""

    def test_zero_amount_is_allowed(self) -> None:
        m = Money(amount=Decimal("0"))
        assert m.amount == Decimal("0")

    def test_default_currency_is_idr(self) -> None:
        m = Money(amount=Decimal("50000"))
        assert m.currency == "IDR"

    def test_structural_equality(self) -> None:
        a = Money(amount=Decimal("100000"), currency="IDR")
        b = Money(amount=Decimal("100000"), currency="IDR")
        assert a == b

    def test_different_amounts_not_equal(self) -> None:
        a = Money(amount=Decimal("100000"), currency="IDR")
        b = Money(amount=Decimal("200000"), currency="IDR")
        assert a != b

    def test_different_currencies_not_equal(self) -> None:
        a = Money(amount=Decimal("100"), currency="IDR")
        b = Money(amount=Decimal("100"), currency="USD")
        assert a != b

    def test_addition_same_currency(self) -> None:
        a = Money(amount=Decimal("100000"), currency="IDR")
        b = Money(amount=Decimal("50000"), currency="IDR")
        result = a + b
        assert result.amount == Decimal("150000")
        assert result.currency == "IDR"

    def test_addition_different_currency_raises(self) -> None:
        a = Money(amount=Decimal("100"), currency="IDR")
        b = Money(amount=Decimal("100"), currency="USD")
        with pytest.raises(ValueError, match="different currencies"):
            _ = a + b

    def test_multiplication_by_positive_int(self) -> None:
        m = Money(amount=Decimal("50000"), currency="IDR")
        result = m * 3
        assert result.amount == Decimal("150000")

    def test_multiplication_by_zero(self) -> None:
        m = Money(amount=Decimal("50000"), currency="IDR")
        result = m * 0
        assert result.amount == Decimal("0")

    def test_multiplication_by_negative_raises(self) -> None:
        m = Money(amount=Decimal("50000"), currency="IDR")
        with pytest.raises(ValueError):
            _ = m * -1

    def test_immutability(self) -> None:
        m = Money(amount=Decimal("100"), currency="IDR")
        with pytest.raises(Exception):
            m.amount = Decimal("999")  # type: ignore[misc]

    # Property-based: any non-negative Decimal must be accepted
    @settings(max_examples=200)
    @given(
        st.decimals(
            min_value=Decimal("0"),
            max_value=Decimal("1000000000"),
            allow_nan=False,
            allow_infinity=False,
        )
    )
    def test_any_non_negative_decimal_accepted(self, amount: Decimal) -> None:
        m = Money(amount=amount)
        assert m.amount >= Decimal("0")

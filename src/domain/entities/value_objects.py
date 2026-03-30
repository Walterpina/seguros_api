"""Value objects: Money, Rate, PaymentSchedule for the domain layer."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import List


@dataclass(frozen=True)
class Money:
    """Immutable Money value object with Decimal precision."""

    amount: Decimal

    def __post_init__(self):
        """Validate money in __post_init__ (frozen dataclass)."""
        if self.amount < 0:
            raise ValueError(f"Money amount cannot be negative: {self.amount}")

    def __add__(self, other: "Money") -> "Money":
        """Add two Money values."""
        if not isinstance(other, Money):
            raise TypeError(f"Cannot add Money and {type(other).__name__}")
        return Money(self.amount + other.amount)

    def __sub__(self, other: "Money") -> "Money":
        """Subtract two Money values."""
        if not isinstance(other, Money):
            raise TypeError(f"Cannot subtract Money and {type(other).__name__}")
        result = self.amount - other.amount
        if result < 0:
            raise ValueError(f"Result would be negative: {result}")
        return Money(result)

    def __mul__(self, multiplier: Decimal) -> "Money":
        """Multiply Money by a scalar."""
        if not isinstance(multiplier, (Decimal, int, float)):
            raise TypeError(f"Cannot multiply Money by {type(multiplier).__name__}")
        return Money((self.amount * Decimal(str(multiplier))).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        ))

    def __truediv__(self, divisor: int) -> "Money":
        """Divide Money by an integer."""
        if not isinstance(divisor, int) or divisor <= 0:
            raise ValueError(f"Divisor must be positive integer: {divisor}")
        return Money((self.amount / divisor).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        ))

    def __str__(self) -> str:
        return f"R$ {self.amount:.2f}"

    def __repr__(self) -> str:
        return f"Money(amount={self.amount})"


@dataclass(frozen=True)
class Rate:
    """Immutable Rate value object (0.0 to 1.0 as Decimal)."""

    value: Decimal

    def __post_init__(self):
        """Validate rate in __post_init__."""
        if not (Decimal("0") <= self.value <= Decimal("1")):
            raise ValueError(f"Rate must be between 0 and 1: {self.value}")

    def apply_to(self, money: Money) -> Money:
        """Apply rate to a Money value."""
        if not isinstance(money, Money):
            raise TypeError(f"Cannot apply rate to {type(money).__name__}")
        result = money.amount * self.value
        return Money(result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    def __str__(self) -> str:
        percentage = self.value * 100
        return f"{percentage:.2f}%"

    def __repr__(self) -> str:
        return f"Rate(value={self.value})"


@dataclass
class MonthlyPayment:
    """Represents a single monthly payment in a schedule."""

    month: int
    amount: Decimal
    accumulated: Decimal

    def __str__(self) -> str:
        return f"Month {self.month}: R$ {self.amount:.2f} (Total: R$ {self.accumulated:.2f})"


@dataclass
class PaymentSchedule:
    """Immutable payment schedule for a quote."""

    total_amount: Decimal
    num_months: int
    monthly_payments: List[MonthlyPayment]

    def __post_init__(self):
        """Validate schedule."""
        if len(self.monthly_payments) != self.num_months:
            raise ValueError(
                f"Expected {self.num_months} payments, got {len(self.monthly_payments)}"
            )

        # Verify sum matches total (within 1 centavo due to rounding)
        total = sum(p.amount for p in self.monthly_payments)
        if abs(total - self.total_amount) > Decimal("0.01"):
            raise ValueError(
                f"Payment schedule sum {total} does not match total {self.total_amount}"
            )

    def __str__(self) -> str:
        lines = [f"Payment Schedule: {self.num_months} months"]
        for payment in self.monthly_payments:
            lines.append(f"  {payment}")
        return "\n".join(lines)

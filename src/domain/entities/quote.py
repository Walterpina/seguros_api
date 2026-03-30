"""Quote domain entity (business logic, no frameworks)."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import List
from uuid import UUID, uuid4

from .value_objects import Money, Rate, PaymentSchedule, MonthlyPayment


@dataclass
class Quote:
    """
    Quote aggregate root: Lending insurance quotation with calculated amounts.
    Contains all business logic for premium and brokerage calculations.
    Immutable after creation (call methods return new Quote).
    """

    loan_value: Decimal
    premium_rate: Decimal
    brokerage_rate: Decimal
    id: UUID = field(default_factory=uuid4)
    premium_amount: Decimal = field(init=False)
    brokerage_amount: Decimal = field(init=False)
    total_amount: Decimal = field(init=False)
    monthly_payment: Decimal = field(init=False)
    payment_schedule: PaymentSchedule = field(init=False, repr=False)
    status: str = "active"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate and calculate quote amounts."""
        # Convert to Decimal if necessary
        self.loan_value = Decimal(str(self.loan_value))
        self.premium_rate = Decimal(str(self.premium_rate))
        self.brokerage_rate = Decimal(str(self.brokerage_rate))

        # Validate inputs
        if self.loan_value <= 0:
            raise ValueError(f"loan_value must be > 0, got {self.loan_value}")
        if not (0 <= self.premium_rate <= 1):
            raise ValueError(f"premium_rate must be 0-1, got {self.premium_rate}")
        if not (0 <= self.brokerage_rate <= 1):
            raise ValueError(f"brokerage_rate must be 0-1, got {self.brokerage_rate}")

        # Calculate amounts using value objects for type safety
        loan_money = Money(self.loan_value)
        premium_rate_obj = Rate(self.premium_rate)
        brokerage_rate_obj = Rate(self.brokerage_rate)

        # Premium = loan_value * premium_rate
        self.premium_amount = premium_rate_obj.apply_to(loan_money).amount

        # Brokerage = premium_amount * brokerage_rate
        brokerage_money = Money(self.premium_amount)
        self.brokerage_amount = brokerage_rate_obj.apply_to(brokerage_money).amount

        # Total = loan_value + premium_amount + brokerage_amount
        self.total_amount = (
            self.loan_value + self.premium_amount + self.brokerage_amount
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Monthly = total / 12 (with last installment adjustment)
        self.monthly_payment = (
            self.total_amount / 12
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Generate payment schedule
        self.payment_schedule = self._generate_payment_schedule()

    def _generate_payment_schedule(self) -> PaymentSchedule:
        """Generate 12-month payment schedule with rounding adjustments."""
        payments: List[MonthlyPayment] = []
        accumulated = Decimal("0.00")

        for month in range(1, 13):
            if month < 12:
                amount = self.monthly_payment
            else:
                # Last payment: adjust for rounding errors
                amount = self.total_amount - accumulated

            accumulated += amount
            payments.append(
                MonthlyPayment(
                    month=month,
                    amount=amount,
                    accumulated=accumulated,
                )
            )

        return PaymentSchedule(
            total_amount=self.total_amount,
            num_months=12,
            monthly_payments=payments,
        )

    def __str__(self) -> str:
        return (
            f"Quote(id={self.id}, loan_value=R${self.loan_value:.2f}, "
            f"premium={self.premium_amount:.2f}, brokerage={self.brokerage_amount:.2f}, "
            f"total={self.total_amount:.2f}, monthly={self.monthly_payment:.2f})"
        )

    def __repr__(self) -> str:
        return self.__str__()

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": str(self.id),
            "loan_value": float(self.loan_value),
            "premium_rate": float(self.premium_rate),
            "premium_amount": float(self.premium_amount),
            "brokerage_rate": float(self.brokerage_rate),
            "brokerage_amount": float(self.brokerage_amount),
            "total_amount": float(self.total_amount),
            "monthly_payment": float(self.monthly_payment),
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

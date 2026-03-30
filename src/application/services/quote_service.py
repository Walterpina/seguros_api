"""Quote calculation service: Pure business logic for quote calculations."""

from decimal import Decimal, ROUND_HALF_UP
from typing import List, NamedTuple

from src.domain.entities.quote import Quote
from src.domain.entities.value_objects import Money, Rate


class ValidationResult(NamedTuple):
    """Result of quote validation."""

    is_valid: bool
    errors: List[str] = []


class MonthlyPaymentInfo(NamedTuple):
    """Monthly payment information."""

    month: int
    amount: Decimal
    accumulated: Decimal


class QuoteCalculationService:
    """Service for calculating quote amounts (no dependencies, pure logic)."""

    @staticmethod
    def calculate_premium(
        loan_value: Decimal, premium_rate: Decimal
    ) -> Decimal:
        """
        Calculate premium amount.

        Args:
            loan_value: Principal loan amount
            premium_rate: Premium rate (0.0 to 1.0)

        Returns:
            Decimal: Premium amount (loan_value * premium_rate)
        """
        loan_value = Decimal(str(loan_value))
        premium_rate = Decimal(str(premium_rate))

        result = loan_value * premium_rate
        return result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_brokerage(
        premium_amount: Decimal, brokerage_rate: Decimal
    ) -> Decimal:
        """
        Calculate brokerage amount.

        Args:
            premium_amount: Premium amount
            brokerage_rate: Brokerage rate (0.0 to 1.0)

        Returns:
            Decimal: Brokerage amount (premium_amount * brokerage_rate)
        """
        premium_amount = Decimal(str(premium_amount))
        brokerage_rate = Decimal(str(brokerage_rate))

        result = premium_amount * brokerage_rate
        return result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_total(
        loan_value: Decimal, premium_amount: Decimal, brokerage_amount: Decimal
    ) -> Decimal:
        """
        Calculate total amount.

        Args:
            loan_value: Principal loan amount
            premium_amount: Premium amount
            brokerage_amount: Brokerage amount

        Returns:
            Decimal: Total amount (loan_value + premium_amount + brokerage_amount)
        """
        loan_value = Decimal(str(loan_value))
        premium_amount = Decimal(str(premium_amount))
        brokerage_amount = Decimal(str(brokerage_amount))

        result = loan_value + premium_amount + brokerage_amount
        return result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_monthly_payment(
        total_amount: Decimal, num_months: int = 12
    ) -> Decimal:
        """
        Calculate monthly payment.

        Args:
            total_amount: Total amount to be paid
            num_months: Number of months for payment (default 12)

        Returns:
            Decimal: Monthly payment amount (total_amount / num_months)
        """
        if num_months <= 0:
            raise ValueError(f"num_months must be > 0, got {num_months}")

        total_amount = Decimal(str(total_amount))
        result = total_amount / num_months
        return result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def generate_payment_schedule(
        total_amount: Decimal, num_months: int = 12
    ) -> List[MonthlyPaymentInfo]:
        """
        Generate payment schedule.

        Args:
            total_amount: Total amount
            num_months: Number of months (default 12)

        Returns:
            List[MonthlyPaymentInfo]: List of monthly payments with accumulated total

        Note:
            Last payment may differ slightly due to rounding.
        """
        total_amount = Decimal(str(total_amount))
        monthly_payment = QuoteCalculationService.calculate_monthly_payment(
            total_amount, num_months
        )

        schedule: List[MonthlyPaymentInfo] = []
        accumulated = Decimal("0.00")

        for month in range(1, num_months + 1):
            if month < num_months:
                amount = monthly_payment
            else:
                # Last payment: adjust for rounding errors
                amount = total_amount - accumulated

            accumulated += amount
            schedule.append(
                MonthlyPaymentInfo(
                    month=month,
                    amount=amount,
                    accumulated=accumulated,
                )
            )

        return schedule

    @staticmethod
    def validate_quote_input(
        loan_value: Decimal, premium_rate: Decimal, brokerage_rate: Decimal
    ) -> ValidationResult:
        """
        Validate quote input values.

        Args:
            loan_value: Principal loan amount
            premium_rate: Premium rate (0.0 to 1.0)
            brokerage_rate: Brokerage rate (0.0 to 1.0)

        Returns:
            ValidationResult: (is_valid, errors_list)
        """
        errors = []

        try:
            loan_value = Decimal(str(loan_value))
        except Exception:
            errors.append(f"loan_value must be numeric, got {loan_value}")
            return ValidationResult(is_valid=False, errors=errors)

        try:
            premium_rate = Decimal(str(premium_rate))
        except Exception:
            errors.append(f"premium_rate must be numeric, got {premium_rate}")

        try:
            brokerage_rate = Decimal(str(brokerage_rate))
        except Exception:
            errors.append(f"brokerage_rate must be numeric, got {brokerage_rate}")

        if errors:
            return ValidationResult(is_valid=False, errors=errors)

        # Validate ranges
        if loan_value <= 0:
            errors.append(f"loan_value must be > 0, got {loan_value}")

        if not (Decimal("0") <= premium_rate <= Decimal("1")):
            errors.append(
                f"premium_rate must be between 0 and 1, got {premium_rate}"
            )

        if not (Decimal("0") <= brokerage_rate <= Decimal("1")):
            errors.append(
                f"brokerage_rate must be between 0 and 1, got {brokerage_rate}"
            )

        if errors:
            return ValidationResult(is_valid=False, errors=errors)

        return ValidationResult(is_valid=True, errors=[])

    @staticmethod
    def create_quote(
        loan_value: Decimal,
        premium_rate: Decimal,
        brokerage_rate: Decimal,
    ) -> Quote:
        """
        Create a Quote entity with calculated values.

        Args:
            loan_value: Principal loan amount
            premium_rate: Premium rate
            brokerage_rate: Brokerage rate

        Returns:
            Quote: Fully calculated Quote entity

        Raises:
            ValueError: If input validation fails
        """
        # Validate inputs
        validation = QuoteCalculationService.validate_quote_input(
            loan_value, premium_rate, brokerage_rate
        )
        if not validation.is_valid:
            raise ValueError(f"Invalid quote input: {', '.join(validation.errors)}")

        # Create and return Quote entity
        return Quote(
            loan_value=Decimal(str(loan_value)),
            premium_rate=Decimal(str(premium_rate)),
            brokerage_rate=Decimal(str(brokerage_rate)),
        )

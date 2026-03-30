"""Create Quote use case."""

from uuid import UUID

from src.application.dtos.mappers import quote_entity_to_response, request_dto_to_entity
from src.application.dtos.quote_dto import QuoteCreateRequest, QuoteResponse
from src.application.services.configuration_service import ConfigurationService
from src.application.services.quote_service import QuoteCalculationService
from src.infrastructure.repositories.quote_repository import QuoteRepository


class CreateQuoteUseCase:
    """Use case for creating a new quote."""

    def __init__(
        self,
        repository: QuoteRepository,
        calculation_service: QuoteCalculationService,
        config_service: ConfigurationService,
    ):
        """
        Initialize use case with dependencies.

        Args:
            repository: Quote repository for persistence
            calculation_service: Service for calculations
            config_service: Service for rate configuration
        """
        self.repository = repository
        self.calculation_service = calculation_service
        self.config_service = config_service

    def execute(
        self,
        request: QuoteCreateRequest,
        user_id: UUID,
        organization_id: UUID,
    ) -> QuoteResponse:
        """
        Execute quote creation.

        Args:
            request: Quote creation request
            user_id: User ID
            organization_id: Organization ID

        Returns:
            QuoteResponse: Created quote response

        Raises:
            ValueError: If input validation fails
        """
        # Get current rates (use default if not provided in request)
        current_rates = self.config_service.get_current_rates(organization_id)

        # Use request rates if provided, otherwise use configuration rates
        premium_rate = request.premium_rate or current_rates.premium_rate
        brokerage_rate = request.brokerage_rate or current_rates.brokerage_rate

        # Create quote entity with calculations
        quote_entity = self.calculation_service.create_quote(
            loan_value=request.loan_value,
            premium_rate=premium_rate,
            brokerage_rate=brokerage_rate,
        )

        # Persist to repository
        persisted_quote = self.repository.create(
            quote_entity=quote_entity,
            user_id=user_id,
            organization_id=organization_id,
        )

        # Convert to response
        return quote_entity_to_response(persisted_quote, user_id, organization_id)

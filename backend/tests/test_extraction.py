from app.core.config import Settings
from app.models.order import OrderStatus
from app.schemas.extraction import AIExtractionResult
from app.schemas.order import OrderItemCreate
from app.services.extraction import HybridOrderExtractionService
from app.services.order_parser import DeterministicTextOrderParser


class DisabledAIExtractor:
    is_configured = False

    def extract(self, content, deterministic):
        raise AssertionError("AI must not be called when it is disabled")


class ValidAIExtractor:
    is_configured = True

    def extract(self, content, deterministic):
        return AIExtractionResult(
            customer_name="AI Customer",
            delivery_address="Testowa 1, Katowice",
            delivery_date="2026-10-01",
            items=[OrderItemCreate(sku="AI-1", quantity=2)],
            warnings=[],
            confidence=0.91,
        )


class InvalidAIResult:
    def model_dump(self, **kwargs):
        return {
            "customer_name": "AI Customer",
            "delivery_address": "Testowa 1",
            "delivery_date": "not-a-date",
            "items": [{"sku": "AI-1", "quantity": -2}],
        }


class InvalidAIExtractor:
    is_configured = True

    def extract(self, content, deterministic):
        return InvalidAIResult()


def service(ai_extractor) -> HybridOrderExtractionService:
    return HybridOrderExtractionService(
        DeterministicTextOrderParser(), ai_extractor, confidence_threshold=0.85
    )


def test_fallback_without_langflow_keeps_deterministic_result() -> None:
    outcome = service(DisabledAIExtractor()).extract("Poproszę:\n2 x FILTR-X100")

    assert outcome.used_ai is False
    assert outcome.order.status == OrderStatus.NEEDS_REVIEW
    assert outcome.order.items[0].sku == "FILTR-X100"


def test_valid_ai_result_is_validated_and_used() -> None:
    outcome = service(ValidAIExtractor()).extract("Niejednoznaczne zamówienie")

    assert outcome.used_ai is True
    assert outcome.order.status == OrderStatus.NEW
    assert outcome.order.items[0].quantity == 2


def test_invalid_ai_result_falls_back_to_review() -> None:
    outcome = service(InvalidAIExtractor()).extract("Niejednoznaczne zamówienie")

    assert outcome.used_ai is False
    assert outcome.order.status == OrderStatus.NEEDS_REVIEW
    assert any("AI extraction unavailable" in warning for warning in outcome.warnings)


def test_langflow_is_disabled_without_flow_id() -> None:
    from app.services.extraction import LangflowExtractor

    extractor = LangflowExtractor(Settings(langflow_enabled=True, langflow_flow_id=None))
    assert extractor.is_configured is False

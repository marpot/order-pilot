import json
from typing import Protocol

import httpx
from pydantic import ValidationError

from app.core.config import Settings
from app.models.order import OrderSource, OrderStatus
from app.schemas.extraction import AIExtractionResult, ExtractionOutcome
from app.schemas.order import OrderCreate
from app.services.metrics import AI_REQUESTS
from app.services.order_parser import OrderParser


class AIExtractor(Protocol):
    @property
    def is_configured(self) -> bool: ...

    def extract(self, content: str, deterministic: OrderCreate) -> AIExtractionResult: ...


def missing_required_fields(order: OrderCreate) -> list[str]:
    missing: list[str] = []
    if not order.customer_name:
        missing.append("customer_name")
    if not order.delivery_address:
        missing.append("delivery_address")
    if not order.delivery_date:
        missing.append("delivery_date")
    if not order.items:
        missing.append("items")
    return missing


def extraction_confidence(order: OrderCreate) -> float:
    required_count = 4
    return (required_count - len(missing_required_fields(order))) / required_count


class LangflowExtractor:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def is_configured(self) -> bool:
        return bool(
            self.settings.langflow_enabled
            and self.settings.langflow_url
            and self.settings.langflow_flow_id
        )

    def extract(self, content: str, deterministic: OrderCreate) -> AIExtractionResult:
        if not self.is_configured:
            raise RuntimeError("Langflow is not configured")
        headers = {"Content-Type": "application/json"}
        if self.settings.langflow_api_key:
            headers["x-api-key"] = self.settings.langflow_api_key
        payload = {
            "input_value": content,
            "input_type": "chat",
            "output_type": "chat",
            "tweaks": {
                "OrderPilotContext": {
                    "deterministic_result": deterministic.model_dump(mode="json")
                }
            },
        }
        url = f"{self.settings.langflow_url.rstrip('/')}/api/v1/run/{self.settings.langflow_flow_id}"
        with httpx.Client(timeout=self.settings.langflow_timeout_seconds) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
        return AIExtractionResult.model_validate(self._structured_payload(response.json()))

    @staticmethod
    def _structured_payload(response: dict) -> dict:
        if isinstance(response.get("result"), dict):
            return response["result"]
        try:
            value = response["outputs"][0]["outputs"][0]["results"]["message"]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("Langflow response does not contain structured output") from exc
        if isinstance(value, dict):
            return value
        if not isinstance(value, str):
            raise ValueError("Langflow result must be a JSON object")
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError("Langflow result is not valid JSON") from exc
        if not isinstance(parsed, dict):
            raise ValueError("Langflow result must be a JSON object")
        return parsed


class HybridOrderExtractionService:
    def __init__(
        self,
        deterministic_parser: OrderParser,
        ai_extractor: AIExtractor,
        confidence_threshold: float,
    ) -> None:
        self.deterministic_parser = deterministic_parser
        self.ai_extractor = ai_extractor
        self.confidence_threshold = confidence_threshold

    def extract(self, content: str, source: OrderSource = OrderSource.EMAIL) -> ExtractionOutcome:
        deterministic = self.deterministic_parser.parse(content)
        deterministic.source = source
        confidence = extraction_confidence(deterministic)
        missing = missing_required_fields(deterministic)
        if not missing:
            deterministic.status = OrderStatus.NEW
            return ExtractionOutcome(order=deterministic, confidence=confidence)

        warnings = [f"Missing required field: {field}" for field in missing]
        deterministic.status = OrderStatus.NEEDS_REVIEW
        if not self.ai_extractor.is_configured:
            return ExtractionOutcome(order=deterministic, warnings=warnings, confidence=confidence)

        try:
            AI_REQUESTS.labels(result="attempted").inc()
            ai_result = self.ai_extractor.extract(content, deterministic)
            ai_order = OrderCreate(
                **ai_result.model_dump(exclude={"warnings", "confidence"}),
                source=source,
                status=OrderStatus.NEEDS_REVIEW,
                original_content=content,
            )
            ai_missing = missing_required_fields(ai_order)
            ai_order.status = (
                OrderStatus.NEW
                if not ai_missing and ai_result.confidence >= self.confidence_threshold
                else OrderStatus.NEEDS_REVIEW
            )
            AI_REQUESTS.labels(result="success").inc()
            return ExtractionOutcome(
                order=ai_order,
                warnings=ai_result.warnings
                + [f"Missing required field: {field}" for field in ai_missing],
                confidence=ai_result.confidence,
                used_ai=True,
            )
        except (httpx.HTTPError, ValidationError, ValueError, RuntimeError):
            AI_REQUESTS.labels(result="failure").inc()
            warnings.append("AI extraction unavailable; deterministic result requires review")
            return ExtractionOutcome(order=deterministic, warnings=warnings, confidence=confidence)

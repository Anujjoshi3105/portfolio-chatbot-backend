"""Service-layer safety middleware using LlamaGuard."""

import logging

from langchain_core.messages import AnyMessage

from agents.llama_guard import LlamaGuard, LlamaGuardOutput, SafetyAssessment
from core import settings

logger = logging.getLogger(__name__)

UNSAFE_RESPONSE = (
    "I'm sorry, but I can't process that request as it was flagged "
    "for safety concerns. Please rephrase your message."
)


class SafetyMiddleware:
    """Centralized safety middleware that wraps LlamaGuard for input/output checks.

    Used at the service layer to guard all agent interactions uniformly.
    Respects the ``ENABLE_SAFETY_GUARD`` setting – when disabled, all checks
    short-circuit to ``SAFE``.
    """

    def __init__(self) -> None:
        self._guard = LlamaGuard()

    @property
    def enabled(self) -> bool:
        """Whether the safety guard is active."""
        return (
            settings.ENABLE_SAFETY_GUARD
            and self._guard is not None
            and self._guard.model is not None
        )

    async def check_input(self, messages: list[AnyMessage]) -> LlamaGuardOutput:
        """Check user input messages before forwarding to an agent."""
        if not self.enabled:
            return LlamaGuardOutput(safety_assessment=SafetyAssessment.SAFE)
        result = await self._guard.ainvoke("User", messages)
        if result.safety_assessment == SafetyAssessment.UNSAFE:
            logger.warning(
                "Input blocked by LlamaGuard – categories: %s",
                ", ".join(result.unsafe_categories),
            )
        return result

    async def check_output(self, messages: list[AnyMessage]) -> LlamaGuardOutput:
        """Check agent output messages before returning to the user."""
        if not self.enabled:
            return LlamaGuardOutput(safety_assessment=SafetyAssessment.SAFE)
        result = await self._guard.ainvoke("Agent", messages)
        if result.safety_assessment == SafetyAssessment.UNSAFE:
            logger.warning(
                "Output blocked by LlamaGuard – categories: %s",
                ", ".join(result.unsafe_categories),
            )
        return result

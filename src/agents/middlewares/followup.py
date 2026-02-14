import logging
from typing import List

from pydantic import BaseModel, Field, field_validator

from langchain_core.messages import (
    AnyMessage,
    SystemMessage,
    HumanMessage,
    AIMessage,
    ChatMessage,
)
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnableConfig

from core import get_model, settings
from agents.prompts.followup import (
    DEFAULT_FOLLOWUP_PROMPTS,
    FOLLOWUP_GENERATION_PROMPT,
)

logger = logging.getLogger(__name__)


class FollowUpOutput(BaseModel):
    """Schema for follow-up generation response."""
    questions: List[str] = Field(min_length=1, max_length=5, description="List of 1-5 suggested follow-up questions for the user.",)

    @field_validator("questions")
    @classmethod
    def validate_questions(cls, value: List[str]) -> List[str]:
        cleaned = [q.strip() for q in value if q and q.strip()]
        if not cleaned:
            raise ValueError("Questions list cannot be empty")
        return cleaned


class FollowUpMiddleware:
    """Generates structured follow-up suggestions after an agent response."""

    async def generate(self, messages: List[AnyMessage], config: RunnableConfig) -> List[str]:
        try:
            model_name = config.get("configurable", {}).get("model", settings.DEFAULT_MODEL)

            model = get_model(model_name)
            parser = PydanticOutputParser(pydantic_object=FollowUpOutput)

            system_message = f"{FOLLOWUP_GENERATION_PROMPT}\n\n{parser.get_format_instructions()}"
            messages = [SystemMessage(content=system_message), messages[-1]]

            response = await model.ainvoke(messages, config)
            content = parser.parse(response.content)

            if not content or not content.questions:
                raise ValueError("Empty follow-up response")

            return content.questions

        except Exception as e:
            logger.warning("Follow-up generation failed, using defaults: %s", e, exc_info=True)

        return DEFAULT_FOLLOWUP_PROMPTS

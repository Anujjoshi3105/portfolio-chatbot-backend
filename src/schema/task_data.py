from typing import Any, Literal

from pydantic import BaseModel, Field


class TaskData(BaseModel):
    name: str | None = None
    run_id: str = ""
    state: Literal["new", "running", "complete"] | None = None
    result: Literal["success", "error"] | None = None
    data: dict[str, Any] = Field(default_factory=dict)

    def completed(self) -> bool:
        return self.state == "complete"

    def completed_with_error(self) -> bool:
        return self.completed() and self.result == "error"

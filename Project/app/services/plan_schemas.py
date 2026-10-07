from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, TypeAdapter

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Chart(StrictModel):
    type: Literal["bar", "line", "pie", "scatter"]
    x: Name
    y: Name
    title: Name


class AnalysisPlan(StrictModel):
    action: Literal["analyze"]
    dataset_id: UUID
    sql: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=10000)]
    explanation: Text
    assumptions: list[Text] = Field(max_length=10)
    chart: Chart | None


class ClarificationPlan(StrictModel):
    action: Literal["clarify"]
    question: Text


PLAN_ADAPTER = TypeAdapter(
    Annotated[AnalysisPlan | ClarificationPlan, Field(discriminator="action")]
)

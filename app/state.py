from pydantic import BaseModel, Field
from langchain_core.documents import Document
from typing import List, Optional

class Source(BaseModel):

    source: str
    page: int

    relevant_content: str


class Evaluation(BaseModel):

    answer_relevance: float = Field(ge=0, le=1)

    faithfulness: float = Field(ge=0, le=1)

    completeness: float = Field(ge=0, le=1)

class GraphState(BaseModel):

    original_question: str = Field(...)
    question: Optional[str] = Field(default=None)

    categories: List[str] = Field(default_factory=list)

    documents: List[Document] = Field(default_factory=list)
    context: str = Field(default="")

    grades: List[float] = Field(default_factory=list)
    relavance_score: float = Field(default=0.0)
    decision: str = Field(default="")

    retry: int = Field(default=0)

    generated_answer: str = Field(default="")
    overall_score: float = Field(default=0.0)

    source: List[Source] = Field(default_factory=list)
    evaluation: Optional[Evaluation] = Field(default=None)
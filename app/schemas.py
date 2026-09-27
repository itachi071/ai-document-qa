from pydantic import BaseModel


class DocumentCreate(BaseModel):
    title: str
    description: str
    author: str


class QuestionRequest(BaseModel):
    question: str
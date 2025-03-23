from pydantic import BaseModel, Field


class FirstQueryResponse(BaseModel):
    query: str = Field(..., description="The search query generated based on the topic provided.")

class SummarizerResponse(BaseModel):
    summary: str = Field(..., description="The summary generated based on the sources gathered.")

class ReflectionResponse(BaseModel):
    query: str = Field(..., description="The follow-up query generated based on the summary.")
    
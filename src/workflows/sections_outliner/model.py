from typing import Optional

from pydantic import BaseModel, Field


class BlogSection(BaseModel):
    title: str = Field(..., title="Title of the blog section")
    description: str = Field(
        ...,
        title="Description of the blog section. Briefly describe what the section is about, concepts covered and main topics.",
    )
    base_content: Optional[str] = Field(
        None,
        title="Base content of the blog section. This is part of the content the user has provided and its related to this section.",
    )
    research: str = Field(
        ...,
        title="Research content of the blog section. This is the content that the AI has generated and is related to this section.",
    )
    research_queries: list[str] = Field(
        ...,
        title="Research queries of the blog section. This is the list of queries that the AI will use to generate the research content.",
    )
    content: str = Field(
        ...,
        title="Content of the blog section. This is the final content that will be displayed in the blog section.",
    )


class ExpectedStructuredOutput(BaseModel):
    sections: list[BlogSection] = Field(
        ...,
        title="List of blog sections. Each section contains the title, description, base content, research content, research queries and final content.",
    )

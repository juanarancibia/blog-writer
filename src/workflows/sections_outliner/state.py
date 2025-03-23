import operator
from typing import Optional, TypedDict

from typing_extensions import Annotated

from workflows.sections_outliner.model import BlogSection


class InputState(TypedDict):
    topic: str
    base_file: Optional[str]


class OutputState(TypedDict):
    sections: Annotated[list[BlogSection], operator.add]
    markdown_sections: str


class OverallState(InputState, OutputState):
    user_feedback: Optional[str]

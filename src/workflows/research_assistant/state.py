

import operator

from typing_extensions import Annotated, TypedDict


class InputState(TypedDict):
    topic: str
    max_web_searchs: int


class OutputState(TypedDict):
    summary: str


class OverallState(InputState, OutputState):
    search_query: str
    research_loop_count: int
    sources_gathered: Annotated[list, operator.add]
    web_search_results: Annotated[list, operator.add]

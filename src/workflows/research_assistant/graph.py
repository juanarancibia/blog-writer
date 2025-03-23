
from langgraph.graph import END, START, StateGraph
from tavily import TavilyClient
from typing_extensions import Literal

from lib.utils import get_structured_output_with_retry
from workflows.research_assistant.models import FirstQueryResponse, ReflectionResponse, SummarizerResponse
from workflows.research_assistant.prompt import GENERATE_FIRST_QUERY_PROMPT, REFLECT_ON_SUMMARY_PROMPT, get_summary_prompt
from workflows.research_assistant.state import (InputState, OutputState,
                                                OverallState)


def tavily_search(query: str):
    print("Searching Tavily for:", query)
    tavily = TavilyClient()
    return tavily.search(query, max_results=2)


def get_response_str(search_response: dict):
    sources_list = search_response['results']

    # Deduplicate by URL
    unique_sources = {}
    for source in sources_list:
        if source['url'] not in unique_sources:
            unique_sources[source['url']] = source

    # Format output
    formatted_text = "Sources:\n\n"
    for i, source in enumerate(unique_sources.values(), 1):
        formatted_text += f"Source {source['title']}:\n===\n"
        formatted_text += f"URL: {source['url']}\n===\n"
        formatted_text += f"Most relevant content from source: {source['content']}\n===\n"

    return formatted_text.strip()


def get_sources_from_search_results(search_response: list):
    return '\n'.join(
        f"* {source['title']} : {source['url']}"
        for source in search_response['results']
    )


def generate_first_query(state: InputState):
    """
    Generate a search query based on the topic provided in the state.
    """

    prompt = GENERATE_FIRST_QUERY_PROMPT.format(topic=state.get("topic", ""))

    query = get_structured_output_with_retry(FirstQueryResponse, prompt).query

    return {"search_query": query}


def web_search_generator(state: OverallState):
    """
    Gather web search results based on the search query.
    """

    search_results = tavily_search(state['search_query'])

    return {
        "sources_gathered": [get_sources_from_search_results(search_results)],
        "web_search_results": [search_results],
        "research_loop_count": state["research_loop_count"] + 1 if "research_loop_count" in state else 1
    }


def summarize_sources(state: OverallState):
    """
    Generate a summary based on the sources gathered.
    """

    existing_summary = state.get("summary", "")

    last_web_search = state["web_search_results"][-1]

    prompt = get_summary_prompt(
        state["topic"], get_response_str(last_web_search), existing_summary
    )

    summary = get_structured_output_with_retry(SummarizerResponse, prompt).summary

    return {"summary": summary}


def reflect_on_suumary(state: OverallState):
    """
    Refelect on summary and generate a follow up query.
    """

    prompt = REFLECT_ON_SUMMARY_PROMPT.format(
        topic=state["topic"], summary=state["summary"]
    )
    query = get_structured_output_with_retry(ReflectionResponse, prompt).query

    query = query if len(
        query) <= 140 else f"Tell me more about {state['research_topic']}"
    
    return {"search_query": query}


def finalize_summary(state: OverallState):
    """ Finalize the summary """

    # Format all accumulated sources into a single bulleted list
    # Deduplicate sources
    unique_sources = list(set(state["sources_gathered"]))
    all_sources = "\n".join(source for source in unique_sources)

    final_summary = f"## Summary\n\n{state['summary']}\n\n ### Sources:\n{all_sources}"
    return {"summary": final_summary}


def reasearch_router(state: OverallState) -> Literal["finalize_summary", "web_research"]:
    """ 
    Route the research based on the follow-up query 
    """

    if state["research_loop_count"] < state["max_web_searchs"]:
        return "web_research"
    else:
        return "finalize_summary"


def get_workflow():
    builder = StateGraph(OverallState, input=InputState, output=OutputState)

    # Add nodes
    builder.add_node("generate_first_query", generate_first_query)
    builder.add_node("web_research", web_search_generator)
    builder.add_node("summarize_sources", summarize_sources)
    builder.add_node("reflect_on_summary", reflect_on_suumary)
    builder.add_node("finalize_summary", finalize_summary)

    # Add edges
    builder.add_edge(START, "generate_first_query")
    builder.add_edge("generate_first_query", "web_research")
    builder.add_edge("web_research", "summarize_sources")
    builder.add_edge("summarize_sources", "reflect_on_summary")
    builder.add_conditional_edges("reflect_on_summary", reasearch_router)
    builder.add_edge("finalize_summary", END)

    return builder.compile()

def invoke_graph(topic, callables):
    runnable = get_workflow()

    # Ensure the callables parameter is a list as you can have multiple callbacks
    if not isinstance(callables, list):
        raise TypeError("callables must be a list")

    # Invoke the graph with the current messages and callback configuration
    return runnable.invoke({"topic": topic, "max_web_searchs": 3}, config={"callbacks": callables})

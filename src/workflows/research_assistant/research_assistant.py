
from langgraph.graph import END, START, StateGraph
from tavily import TavilyClient
from typing_extensions import Literal

from src.utils import extract_result_from_tags, get_llm_reasoner_model
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

    prompt = (
        f"Your goal is to generate a targeted web search query."
        "The query will gather information related to a specific topic."
        "Do not give me extra information, all I need is a search query"
        f"The topic is: {state['topic']}"
        "Please return the query wrapped in <query> tags. For example: <query>Suggested query</query>"
    )

    reasoner_llm = get_llm_reasoner_model()
    response = reasoner_llm(prompt)
    query = extract_result_from_tags("query", response.content)

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

    prompt = (
        "Generate a high-quality summary of the web search results and keep it related to the topic."
        "Highlight the most relevant information related to the topic from the search results"
        "The topic is: {state['topic']}"
    )

    if existing_summary != "":
        prompt += (
            "Compare the new information with the existing summary. "
            "For each piece of new information:"
            "If it's related to existing points, integrate it into the relevant paragraph."
            "If it's entirely new but relevant, add a new paragraph with a smooth transition."
            "If it's not relevant to the user topic, skip it."
            f"\nPlease extend the existing summary with the new information from the latest search results."
            f"\nExisting summary: {existing_summary}"
            f"\nNew search results: {last_web_search}"
        )
    else:
        prompt += f"\nSearch results: {last_web_search}"

    prompt += "Please return the summary wrapped in <summary> tags. For example: <summary>Suggested summary</summary>"

    reasoner_llm = get_llm_reasoner_model()
    response = reasoner_llm(prompt)
    summary = extract_result_from_tags("summary", response.content)

    return {"summary": summary}


def reflect_on_suumary(state: OverallState):
    """
    Refelect on summary and generate a follow up query.
    """

    prompt = (
        "Identify knowledge gaps or areas that need deeper exploration"
        "Reflect on the summary and generate a follow-up question to deepen your understanding."
        "Focus on technical details, implementation specifics, or emerging trends that weren't fully covered"
        "The follow-up question should be concise enough to be a web search query"
        "The query should be at max 15 words"
        f"The topic is: {state['topic']}"
        f"The summary is: {state['summary']}"
        "Please return the query wrapped in <query> tags. For example: <query>Suggested query</query>"
    )

    reasoner_llm = get_llm_reasoner_model()
    response = reasoner_llm(prompt)
    query = extract_result_from_tags("query", response.content)

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

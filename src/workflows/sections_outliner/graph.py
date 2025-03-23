from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt
from typing_extensions import Literal

from lib.utils import get_structured_output_with_retry
from workflows.sections_outliner.model import ExpectedStructuredOutput
from workflows.sections_outliner.prompt import SECTIONS_PLANNER_PROMPT
from workflows.sections_outliner.state import InputState, OutputState, OverallState


def generate_blog_sections(state: OverallState):
    prompt = SECTIONS_PLANNER_PROMPT.format(
        topic=state["topic"],
        base_file=state.get("base_file", ""),
        feedback=state.get("feedback", ""),
        previous_sections=state.get("sections", ""),
    )

    sections = get_structured_output_with_retry(
        ExpectedStructuredOutput, prompt
    ).sections

    return {"sections": sections}


def get_feedback_from_sections(state: OverallState):
    # Get sections
    sections = state["sections"]
    sections_str = "\n\n".join(
        f"## {section.title} \n\n"
        f"{section.description}\n\n"
        f"- *Research queries: {section.research_queries if section.research_queries else ''}*\n"
        f"- *Base content: {section.base_content if section.base_content else ''}*\n"
        for section in sections
    )

    # Get feedback on the report plan from interrupt
    # feedback = interrupt(f"""Please provide feedback on the following report plan.\n
    #                      {sections_str}\n\n
    #                      Does the report plan meet your needs? \n
    #                      Say "yes" to approve the report plan or provide feedback to
    #                       regenerate the report plan:
    #                      """)
    feedback = "yes"

    return {"user_feedback": feedback, "markdown_sections": sections_str}


def human_feedback_router(state: OverallState) -> Literal["REGENERATE", "APPROVED"]:
    if state["user_feedback"].lower().startswith("yes"):
        return "APPROVED"

    return "REGENERATE"


def get_workflow():
    graph_builder = StateGraph(OverallState, input=InputState, output=OutputState)

    graph_builder.add_node("generate_blog_sections", generate_blog_sections)
    graph_builder.add_node("get_feedback_from_sections", get_feedback_from_sections)

    graph_builder.add_edge(START, "generate_blog_sections")
    graph_builder.add_edge("generate_blog_sections", "get_feedback_from_sections")
    graph_builder.add_conditional_edges(
        "get_feedback_from_sections",
        human_feedback_router,
        {"REGENERATE": "generate_blog_sections", "APPROVED": END},
    )

    return graph_builder.compile()


def invoke_graph(topic, callables):
    runnable = get_workflow()

    # Ensure the callables parameter is a list as you can have multiple callbacks
    if not isinstance(callables, list):
        raise TypeError("callables must be a list")

    # Invoke the graph with the current messages and callback configuration
    return runnable.invoke({"topic": topic}, config={"callbacks": callables})

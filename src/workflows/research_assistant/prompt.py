GENERATE_FIRST_QUERY_PROMPT = """
<|im_start|>system
You are a search query optimization assistant. Your task is to generate precise, targeted web search queries that will yield relevant information.
<|im_end|>

<|im_start|>user
I need a well-crafted search query to gather detailed information about the following topic: {topic}

Please provide just the search query without any explanation or additional text.
<|im_end|>

<|im_start|>assistant
"""

SUMMARIZE_SOURCES_PROMPT = """
<|im_start|>system
You are a research assistant specializing in creating comprehensive, accurate summaries from web search results.
<|im_end|>

<|im_start|>user
Generate a detailed, high-quality summary of the web search results related to this topic: {topic}

Guidelines:
- Capture all relevant information from the search results in depth
- Organize information logically with clear paragraph structure
- Include specific facts, data points, and expert opinions with proper context
- Explore multiple perspectives and approaches when available
- Cover technical details, implementation aspects, and practical applications
- Maintain neutrality and accuracy
- Use professional and clear language
- Aim for a comprehensive overview (at least 3-4 substantial paragraphs)
"""

def get_summary_prompt(topic, last_web_search, existing_summary=""):
    prompt = SUMMARIZE_SOURCES_PROMPT.format(topic=topic)
    
    if existing_summary != "":
        prompt += (
            "\nCompare the new information with the existing summary. "
            "For each piece of new information:"
            "- If it's related to existing points, integrate it into the relevant paragraph."
            "- If it's entirely new but relevant, add a new paragraph with a smooth transition."
            "- If it's not relevant to the user topic, skip it."
            f"\nPlease extend the existing summary with the new information from the latest search results."
            f"\nExisting summary: {existing_summary}"
            f"\nNew search results: {last_web_search}"
        )
    else:
        prompt += f"\nSearch results: {last_web_search}"
    
    prompt += """
<|im_end|>

<|im_start|>assistant
"""
    return prompt

REFLECT_ON_SUMMARY_PROMPT = """
<|im_start|>system
You are a research assistant specializing in identifying knowledge gaps and generating targeted follow-up questions.
<|im_end|>

<|im_start|>user
Review the following summary on the topic: {topic}

Summary:
{summary}

Identify knowledge gaps or areas that need deeper exploration. Generate a follow-up question that will:
- Target technical details, implementation specifics, or emerging trends not fully covered
- Deepen understanding of the topic
- Be concise enough to serve as a web search query (maximum 15 words)

Provide only the follow-up question without any explanation or additional text.
<|im_end|>

<|im_start|>assistant
"""
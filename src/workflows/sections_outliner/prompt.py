SECTIONS_PLANNER_PROMPT = """
<GOAL>
I want to create a blog post about the topic of "{topic}" and I need you to give the sections of the blog post.

Each section should have the fields:

- Title - Title of the blog section
- Description - Briefly describe what the section is about, concepts covered and main topics.
- Research queries - Research queries of the blog section. This is the list of queries that the AI will use to generate the research content.
- Base content - Base content of the blog section. This is part of the content the user has provided (if any) and its related to this section.

For example, introduction and conclusion will not require research because they will distill information from other parts of the report.


The user has provided the following base content (if any):
{base_file}

The user has provided this feedback (if any):
{feedback}

The feedback is about this previously generated sections (if any):
{previous_sections}
</GOAL> 
"""

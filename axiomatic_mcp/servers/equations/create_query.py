from langchain_core.messages import HumanMessage, SystemMessage

SYSTEM_PROMPT = """You know everything about physics and math. You also know the whole codebase of sympy
your job is simple. To help humanity solve their math and physcis problems by answering their questions.
Do your best, no excuses!

Specifically you will always recieve a query that contains a task and source document. The task will be always
to derive or compose expression from other equations in the source document and from your own knowlege."""

QUERY_TEMPLATE = """
TASK: {task}
SOURCE DOCUMENT: {source_document}
"""


def create_query(source_document: str, task: str) -> list:
    system_message = SystemMessage(content=SYSTEM_PROMPT)
    human_content = QUERY_TEMPLATE.format(task=task, source_document=source_document)
    human_message = HumanMessage(content=human_content)
    return [system_message, human_message]

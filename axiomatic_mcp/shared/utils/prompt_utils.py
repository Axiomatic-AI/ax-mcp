from textwrap import dedent


def get_feedback_prompt(tool_names: list[str]) -> str:
    tools_str = ", ".join(tool_names)
    return dedent(
        f"""
    After using the following tools: {tools_str}
    you must also call the `report_feedback` tool with:
        - previous_called_tool_name: the name of the previous tool called
        - previous_tool_parameters: the parameters/arguments that were provided to the previous tool
        - previous_tool_response: the response that was returned by the previous tool
        - feedback: it can be a short summary of how well the tool call went, and any issues encountered.
        - feedback_value: one of [positive, negative, neutral] indicating how well the tool call went.
    This is mandatory, even if the response is an error.
    """
    )

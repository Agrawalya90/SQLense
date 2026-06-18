import ast
from database import execute_sql


tools = [
    {
        "type": "function",
        "function": {
            "name": "execute_sql",
            "description": (
                "Execute a read-only SQL SELECT query on the e-commerce database "
                "and return the results. Use this whenever the user asks a question "
                "that requires querying data."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A valid SQLite SELECT query based on the schema provided."
                    }
                },
                "required": ["query"]
            }
        }
    }
]



def handle_tool_calls(message):
    """
    Processes all tool calls in an assistant message.
    Returns a list of tool-result dicts ready to append to messages[].
    """
    responses = []

    for tool_call in message.tool_calls:
        if tool_call.function.name == "execute_sql":
            arguments = ast.literal_eval(tool_call.function.arguments)
            query = arguments.get("query", "")

            try:
                columns, rows = execute_sql(query)

                if not rows:
                    content = "The query returned no results."
                else:
                    # Format as a simple text table
                    header = " | ".join(columns)
                    divider = "-" * len(header)
                    data_rows = "\n".join(" | ".join(str(v) for v in row) for row in rows)
                    content = f"{header}\n{divider}\n{data_rows}"

            except ValueError as e:
                content = f"Query blocked: {e}"
            except Exception as e:
                content = f"Query failed: {e}"

            responses.append({
                "role":        "tool",
                "content":     content,
                "tool_call_id": tool_call.id
            })

    return responses

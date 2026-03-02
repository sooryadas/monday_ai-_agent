import json
import groq
from src.config import GROQ_API_KEY, GROQ_MODEL, SYSTEM_PROMPT
from src.tools import TOOLS, resolve_board_id
import monday


client = groq.Groq(api_key=GROQ_API_KEY)


def execute_tool(tool_name: str, tool_input: dict) -> dict:
    """Execute a tool call and return the result."""
    try:
        if tool_name == "get_board_columns":
            board_id = resolve_board_id(tool_input["board"])
            return monday.get_board_columns(board_id)

        elif tool_name == "get_board_items":
            board_id = resolve_board_id(tool_input["board"])
            limit = min(tool_input.get("limit", 100), 500)
            return monday.get_board_items(board_id, limit=limit)

        elif tool_name == "search_board_items":
            board_id = resolve_board_id(tool_input["board"])
            return monday.search_board_items(board_id, tool_input["query"])

        elif tool_name == "get_item_details":
            return monday.get_item_details(tool_input["item_id"])

        else:
            return {"error": f"Unknown tool: {tool_name}"}

    except Exception as e:
        return {"error": str(e)}


def run_agent(user_message: str) -> dict:
    """
    Run the full agent loop using Groq (OpenAI-compatible API).
    Returns: { answer: str, trace: list[dict] }
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    trace = []
    iteration = 0
    max_iterations = 10  # safety limit

    while iteration < max_iterations:
        iteration += 1

        # Call Groq
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            max_tokens=1024,
            tools=TOOLS,
            messages=messages,
        )

        choice = response.choices[0]
        finish_reason = choice.finish_reason
        message = choice.message

        # Add assistant message to history
        messages.append(message)

        if finish_reason == "stop":
            # Final answer — no more tool calls
            return {"answer": message.content or "", "trace": trace}

        elif finish_reason == "tool_calls":
            # Process all tool calls
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_input = json.loads(tool_call.function.arguments)

                # Execute the tool
                result = execute_tool(tool_name, tool_input)

                # Record trace
                trace.append({
                    "tool": tool_name,
                    "input": tool_input,
                    "result_summary": _summarize_result(result),
                    "success": "error" not in result,
                })

                # Send tool result back (trimmed to stay under token limits)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": _trim_result(result),
                })

        else:
            # Unexpected finish reason
            break

    return {
        "answer": "Agent reached iteration limit without completing. Please try a more specific question.",
        "trace": trace,
    }


def _trim_result(result: dict, max_items: int = 30, max_chars: int = 2000) -> str:
    """
    Trim tool result before sending to model to stay under token limits.
    Caps item lists at max_items rows and the JSON string at max_chars chars.
    """
    if "items" in result and len(result["items"]) > max_items:
        trimmed = dict(result)
        trimmed["items"] = result["items"][:max_items]
        trimmed["note"] = f"Truncated to {max_items} of {result.get('count', len(result['items']))} items to fit context limit."
        text = json.dumps(trimmed, default=str)
    else:
        text = json.dumps(result, default=str)

    if len(text) > max_chars:
        text = text[:max_chars] + '... [truncated]"}'

    return text


def _summarize_result(result: dict) -> str:
    """Create a short human-readable summary of a tool result for the trace."""
    if "error" in result:
        return f"❌ Error: {result['error']}"

    if "items" in result:
        count = result.get("count", len(result["items"]))
        has_more = result.get("has_more", False)
        suffix = " (more available)" if has_more else ""
        return f"✅ {count} items returned{suffix}"

    if "columns" in result:
        cols = [c["title"] for c in result["columns"]]
        return f"✅ {len(cols)} columns: {', '.join(cols[:8])}{'...' if len(cols) > 8 else ''}"

    if "id" in result and "name" in result:
        return f"✅ Item: {result['name']}"

    return "✅ Success"

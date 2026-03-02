from src.config import DEALS_BOARD_ID, WORK_ORDERS_BOARD_ID

# Tool definitions in Groq/OpenAI-compatible format
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_board_columns",
            "description": (
                "Get all column definitions (schema) for a Monday.com board. "
                "Use this first when you need to understand what fields/columns exist "
                "before querying data. Returns column names and types."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "board": {
                        "type": "string",
                        "enum": ["deals", "work_orders"],
                        "description": "Which board to inspect: 'deals' or 'work_orders'",
                    }
                },
                "required": ["board"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_board_items",
            "description": (
                "Fetch items (rows) from a Monday.com board. "
                "Use this to get actual data for analysis. "
                "Returns flattened items with all column values as text. "
                "Use limit wisely — 100 for overview, 500 for full dataset analysis."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "board": {
                        "type": "string",
                        "enum": ["deals", "work_orders"],
                        "description": "Which board to fetch: 'deals' or 'work_orders'",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max items to fetch (default 100, max 500)",
                        "default": 100,
                    },
                },
                "required": ["board"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_board_items",
            "description": (
                "Search for specific items on a board by keyword. "
                "Use this when the user asks about a specific account, deal, company, or term. "
                "More targeted than get_board_items."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "board": {
                        "type": "string",
                        "enum": ["deals", "work_orders"],
                        "description": "Which board to search",
                    },
                    "query": {
                        "type": "string",
                        "description": "Search keyword or phrase",
                    },
                },
                "required": ["board", "query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_item_details",
            "description": (
                "Get full details of a single Monday.com item by its ID, "
                "including recent updates/comments. "
                "Use when the user wants deep info on a specific record."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "item_id": {
                        "type": "string",
                        "description": "The Monday.com item ID (numeric string)",
                    }
                },
                "required": ["item_id"],
            },
        },
    },
]


def resolve_board_id(board: str) -> str:
    """Map board name to actual board ID."""
    mapping = {
        "deals": DEALS_BOARD_ID,
        "work_orders": WORK_ORDERS_BOARD_ID,
    }
    board_id = mapping.get(board)
    if not board_id:
        raise ValueError(
            f"Unknown board '{board}'. "
            f"Set DEALS_BOARD_ID and WORK_ORDERS_BOARD_ID in your .env file."
        )
    return board_id
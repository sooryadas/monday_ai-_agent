import httpx
from src.config import MONDAY_API_TOKEN, MONDAY_API_URL


HEADERS = {
    "Authorization": MONDAY_API_TOKEN,
    "Content-Type": "application/json",
    "API-Version": "2024-01",
}


def _run_query(query: str, variables: dict = None) -> dict:
    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    with httpx.Client(timeout=30) as client:
        response = client.post(MONDAY_API_URL, json=payload, headers=HEADERS)
        response.raise_for_status()
        data = response.json()

    if "errors" in data:
        raise ValueError(f"Monday.com API error: {data['errors']}")

    return data.get("data", {})


def _build_col_map(columns: list) -> dict:
    """Build an id->title mapping from board columns."""
    return {col["id"]: col["title"] for col in columns}


def _flatten_items(items: list, col_map: dict) -> list:
    """Flatten column_values using the id->title map."""
    flat_items = []
    for item in items:
        flat = {"id": item["id"], "name": item["name"]}
        for col in item.get("column_values", []):
            label = col_map.get(col["id"], col["id"])
            flat[label] = col.get("text") or ""
        flat_items.append(flat)
    return flat_items


def get_board_columns(board_id: str) -> dict:
    """Get all column definitions for a board."""
    query = """
    query ($boardId: ID!) {
        boards(ids: [$boardId]) {
            name
            columns {
                id
                title
                type
            }
        }
    }
    """
    data = _run_query(query, {"boardId": board_id})
    boards = data.get("boards", [])
    if not boards:
        return {"error": f"Board {board_id} not found"}
    board = boards[0]
    return {
        "board_name": board["name"],
        "columns": board["columns"],
    }


def get_board_items(board_id: str, limit: int = 100, cursor: str = None) -> dict:
    """Fetch items from a board with pagination."""
    if cursor:
        # Need boardId to get column schema even on paginated calls
        query = """
        query ($boardId: ID!, $limit: Int!, $cursor: String!) {
            boards(ids: [$boardId]) {
                columns { id title }
            }
            next_items_page(limit: $limit, cursor: $cursor) {
                cursor
                items {
                    id
                    name
                    column_values {
                        id
                        text
                        value
                    }
                }
            }
        }
        """
        variables = {"boardId": board_id, "limit": limit, "cursor": cursor}
        data = _run_query(query, variables)
        boards = data.get("boards", [])
        col_map = _build_col_map(boards[0]["columns"]) if boards else {}
        page = data.get("next_items_page", {})
    else:
        query = """
        query ($boardId: ID!, $limit: Int!) {
            boards(ids: [$boardId]) {
                name
                columns { id title }
                items_page(limit: $limit) {
                    cursor
                    items {
                        id
                        name
                        column_values {
                            id
                            text
                            value
                        }
                    }
                }
            }
        }
        """
        variables = {"boardId": board_id, "limit": limit}
        data = _run_query(query, variables)
        boards = data.get("boards", [])
        if not boards:
            return {"error": f"Board {board_id} not found", "items": []}
        col_map = _build_col_map(boards[0].get("columns", []))
        page = boards[0].get("items_page", {})

    items = page.get("items", [])
    next_cursor = page.get("cursor")

    return {
        "items": _flatten_items(items, col_map),
        "count": len(items),
        "next_cursor": next_cursor,
        "has_more": next_cursor is not None,
    }


def search_board_items(board_id: str, query_str: str) -> dict:
    """Search items on a board by keyword — fetches all and filters in Python."""
    result = get_board_items(board_id, limit=200)
    if "error" in result:
        return result
    items = result.get("items", [])
    q = query_str.lower()
    matched = [
        item for item in items
        if q in item.get("name", "").lower()
        or any(q in str(v).lower() for v in item.values())
    ]
    return {"items": matched, "count": len(matched)}


def get_item_details(item_id: str) -> dict:
    """Get full details of a single item."""
    query = """
    query ($itemId: ID!) {
        items(ids: [$itemId]) {
            id
            name
            board { name id columns { id title } }
            column_values {
                id
                text
                value
                type
            }
            updates(limit: 5) {
                body
                created_at
                creator { name }
            }
        }
    }
    """
    data = _run_query(query, {"itemId": item_id})
    items = data.get("items", [])
    if not items:
        return {"error": f"Item {item_id} not found"}
    item = items[0]
    col_map = _build_col_map(item.get("board", {}).get("columns", []))
    flat = {"id": item["id"], "name": item["name"], "board": item["board"]["name"]}
    for col in item.get("column_values", []):
        label = col_map.get(col["id"], col["id"])
        flat[label] = col.get("text") or col.get("value") or ""
    flat["updates"] = item.get("updates", [])
    return flat
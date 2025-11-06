"""
Helpers for consistent API responses.
"""

from typing import Any, Dict, Optional


def ok(payload: Any, message: str = "success") -> Dict[str, Any]:
    return {"status": "ok", "message": message, "data": payload}


def created(payload: Any, message: str = "created") -> Dict[str, Any]:
    return {"status": "created", "message": message, "data": payload}


def error(message: str = "error", details: Optional[Any] = None) -> Dict[str, Any]:
    response = {"status": "error", "message": message}
    if details is not None:
        response["details"] = details
    return response


def forbidden(message: str = "forbidden") -> Dict[str, Any]:
    return {"status": "forbidden", "message": message}


def paginated(items: list, total: int, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
    """Format paginated API responses."""
    return {
        "status": "ok",
        "message": "paginated",
        "data": {"items": items, "total": total, "page": page, "per_page": per_page},
    }

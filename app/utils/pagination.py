"""Consistent pagination for every list endpoint."""

from dataclasses import dataclass

from flask import request

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


@dataclass
class Page:
    items: list
    page: int
    page_size: int
    total: int

    def to_dict(self, serialiser=None) -> dict:
        rows = [serialiser(item) for item in self.items] if serialiser else self.items
        total_pages = (self.total + self.page_size - 1) // self.page_size if self.page_size else 0
        return {
            "items": rows,
            "page": self.page,
            "page_size": self.page_size,
            "total": self.total,
            "total_pages": total_pages,
            "has_next": self.page < total_pages,
        }


def get_pagination_args() -> tuple[int, int]:
    """Read page/page_size from the query string, clamped to sane bounds."""
    try:
        page = max(int(request.args.get("page", 1)), 1)
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = int(request.args.get("page_size", DEFAULT_PAGE_SIZE))
    except (TypeError, ValueError):
        page_size = DEFAULT_PAGE_SIZE
    page_size = min(max(page_size, 1), MAX_PAGE_SIZE)
    return page, page_size

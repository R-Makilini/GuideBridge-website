from typing import Generic, List, TypeVar

from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Query

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PageMeta(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    meta: PageMeta


def paginate_query(query: Query, params: PaginationParams) -> tuple[list, PageMeta]:
    total_items = query.order_by(None).with_entities(func.count()).scalar() or 0
    items = query.offset(params.offset).limit(params.page_size).all()
    total_pages = (total_items + params.page_size - 1) // params.page_size if total_items else 0
    meta = PageMeta(
        page=params.page,
        page_size=params.page_size,
        total_items=total_items,
        total_pages=total_pages,
    )
    return items, meta

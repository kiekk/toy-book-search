from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class Book(BaseModel):
    """OpenSearch 색인 대상 공통 도서 스키마.

    모든 소스(알라딘, 카카오, 증식)가 이 스키마로 정규화된다.
    id는 `isbn:{isbn13}` 형식으로 중복 제거의 기준이 된다.
    """

    id: str = Field(..., description="isbn13 기준 unique id, e.g. isbn:9788960777330")
    title: str
    subtitle: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    translators: List[str] = Field(default_factory=list)
    publisher: Optional[str] = None
    published_at: Optional[date] = None
    isbn13: Optional[str] = None
    isbn10: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    page_count: Optional[int] = None
    language: str = "ko"
    cover_url: Optional[str] = None
    price: Optional[int] = None
    source: str = Field(..., description="aladin, kakao, generated")

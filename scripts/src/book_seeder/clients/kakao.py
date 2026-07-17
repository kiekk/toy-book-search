"""카카오 도서 검색 API 클라이언트.

Docs: https://developers.kakao.com/docs/latest/ko/daum-search/dev-guide#search-book
Limit: 일 300,000회, 페이지당 최대 50건, 최대 50페이지 (2500건/쿼리)
"""
from datetime import datetime
from typing import Iterator, Optional

import httpx

from ..schema import Book


class KakaoBookClient:
    BASE_URL = "https://dapi.kakao.com/v3/search/book"
    PAGE_SIZE = 50
    MAX_PAGE = 50

    def __init__(self, rest_api_key: str, timeout: float = 10.0):
        if not rest_api_key:
            raise ValueError("Kakao REST API key is required")
        self.client = httpx.Client(
            headers={"Authorization": f"KakaoAK {rest_api_key}"},
            timeout=timeout,
        )

    def search(self, query: str, target: Optional[str] = None) -> Iterator[Book]:
        """쿼리로 도서 검색. target: title, isbn, publisher, person."""
        for page in range(1, self.MAX_PAGE + 1):
            params: dict = {
                "query": query,
                "size": self.PAGE_SIZE,
                "page": page,
            }
            if target:
                params["target"] = target

            resp = self.client.get(self.BASE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

            for doc in data.get("documents", []):
                book = self._to_book(doc)
                if book is not None:
                    yield book

            if data.get("meta", {}).get("is_end", True):
                break

    @staticmethod
    def _to_book(doc: dict) -> Optional[Book]:
        # isbn: "10digit 13digit" 공백 구분 또는 하나만
        isbn_parts = (doc.get("isbn") or "").split()
        isbn13 = next((s for s in isbn_parts if len(s) == 13 and s.isdigit()), None)
        isbn10 = next((s for s in isbn_parts if len(s) == 10), None)
        if isbn13 is None:
            return None  # dedup 불가능한 레코드는 skip

        published_at = None
        if doc.get("datetime"):
            try:
                published_at = datetime.fromisoformat(
                    doc["datetime"].replace("Z", "+00:00")
                ).date()
            except ValueError:
                pass

        return Book(
            id=f"isbn:{isbn13}",
            title=(doc.get("title") or "").strip(),
            authors=[a for a in (doc.get("authors") or []) if a],
            translators=[t for t in (doc.get("translators") or []) if t],
            publisher=doc.get("publisher"),
            published_at=published_at,
            isbn13=isbn13,
            isbn10=isbn10,
            description=doc.get("contents"),
            language="ko",
            cover_url=doc.get("thumbnail"),
            price=doc.get("sale_price") or doc.get("price"),
            source="kakao",
        )

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> "KakaoBookClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()

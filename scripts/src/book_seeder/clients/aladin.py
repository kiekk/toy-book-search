"""알라딘 상품 API 클라이언트.

Docs: https://blog.aladin.co.kr/openapi
Limit: 일 5,000회, 페이지당 최대 50건, 최대 20페이지 (1000건/카테고리·타입)
"""
import json
import re
from datetime import date
from typing import Iterator, Optional

import httpx

from ..schema import Book


# 알라딘 CategoryId 일부 (국내도서 하위). 필요시 확장
CATEGORY_IDS: dict[str, int] = {
    "전체": 0,
    "소설시희곡": 1,
    "경제경영": 170,
    "자기계발": 336,
    "인문학": 656,
    "역사": 74,
    "과학": 987,
    "컴퓨터모바일": 351,
    "예술대중문화": 517,
    "에세이": 55889,
}

QUERY_TYPES: list[str] = [
    "Bestseller",       # 베스트셀러
    "ItemNewAll",       # 신간
    "ItemNewSpecial",   # 주목할 만한 신간
    "BlogBest",         # 블로거 베스트셀러
]


class AladinClient:
    LIST_URL = "https://www.aladin.co.kr/ttb/api/ItemList.aspx"
    SEARCH_URL = "https://www.aladin.co.kr/ttb/api/ItemSearch.aspx"
    PAGE_SIZE = 50
    MAX_PAGE = 20

    def __init__(self, ttb_key: str, timeout: float = 15.0):
        if not ttb_key:
            raise ValueError("Aladin TTB key is required")
        self.ttb_key = ttb_key
        self.client = httpx.Client(timeout=timeout, follow_redirects=True)

    def list_by_category(
        self,
        category_id: int,
        query_type: str = "Bestseller",
    ) -> Iterator[Book]:
        for start in range(1, self.MAX_PAGE + 1):
            params = {
                "ttbkey": self.ttb_key,
                "QueryType": query_type,
                "MaxResults": self.PAGE_SIZE,
                "start": start,
                "SearchTarget": "Book",
                "output": "js",
                "Version": "20131101",
                "CategoryId": category_id,
                "Cover": "Big",
                "OptResult": "authors,fulldescription",
            }
            resp = self.client.get(self.LIST_URL, params=params)
            resp.raise_for_status()

            # 알라딘은 content-type이 text/plain으로 오는 경우가 있어 수동 파싱
            try:
                data = resp.json()
            except ValueError:
                data = json.loads(resp.text.strip().rstrip(";"))

            items = data.get("item") or []
            if not items:
                break

            for item in items:
                book = self._to_book(item)
                if book is not None:
                    yield book

    @staticmethod
    def _to_book(item: dict) -> Optional[Book]:
        isbn13 = item.get("isbn13") or ""
        if not (isbn13 and len(isbn13) == 13 and isbn13.isdigit()):
            return None

        authors, translators = AladinClient._parse_authors(item.get("author") or "")
        category_name = item.get("categoryName") or ""
        categories = [c.strip() for c in category_name.split(">") if c.strip()]

        published_at = None
        if item.get("pubDate"):
            try:
                published_at = date.fromisoformat(item["pubDate"])
            except ValueError:
                pass

        description = (
            item.get("fullDescription")
            or item.get("description")
            or ""
        ).strip() or None

        return Book(
            id=f"isbn:{isbn13}",
            title=(item.get("title") or "").strip(),
            authors=authors,
            translators=translators,
            publisher=item.get("publisher"),
            published_at=published_at,
            isbn13=isbn13,
            isbn10=item.get("isbn"),
            categories=categories,
            description=description,
            language="ko",
            cover_url=item.get("cover"),
            price=item.get("priceSales") or item.get("priceStandard"),
            source="aladin",
        )

    @staticmethod
    def _parse_authors(text: str) -> tuple[list[str], list[str]]:
        """알라딘 저자 문자열을 저자/역자로 분리.

        예: "로버트 C. 마틴 (지은이), 박재호, 이해영 (옮긴이)"
        """
        authors: list[str] = []
        translators: list[str] = []
        if not text:
            return authors, translators

        # 역할 태그 앞뒤로 자름 (여러 역자를 한 그룹으로)
        pattern = re.compile(r"([^(]+)\(([^)]+)\)")
        matches = pattern.findall(text)

        if matches:
            for names_text, role in matches:
                names = [n.strip() for n in names_text.split(",") if n.strip()]
                if "옮긴이" in role or "역자" in role or "번역" in role:
                    translators.extend(names)
                else:
                    authors.extend(names)
        else:
            # 역할 태그가 없으면 전부 저자로
            authors.extend(n.strip() for n in text.split(",") if n.strip())

        return authors, translators

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> "AladinClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()

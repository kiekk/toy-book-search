"""알라딘 + 카카오에서 실데이터 수집 → NDJSON 저장.

ISBN13 기준으로 중복 제거하며 순차 스트리밍 저장한다.
"""
from pathlib import Path

from tqdm import tqdm

from ..clients.aladin import CATEGORY_IDS, QUERY_TYPES, AladinClient
from ..clients.kakao import KakaoBookClient
from ..config import ALADIN_TTB_KEY, KAKAO_REST_API_KEY


# 카카오는 광범위 키워드 검색을 반복해 롱테일 확보
KAKAO_QUERIES: list[str] = [
    # 개발/IT
    "프로그래밍", "인공지능", "머신러닝", "딥러닝", "자바", "파이썬", "코틀린",
    "타입스크립트", "리액트", "스프링", "쿠버네티스", "데이터베이스", "알고리즘",
    # 경제/경영
    "경제", "투자", "부동산", "주식", "재테크", "마케팅", "브랜드", "창업",
    # 인문/역사
    "심리학", "철학", "역사", "고전", "동양철학", "서양철학",
    # 과학
    "과학", "물리학", "천문학", "생물학", "화학", "수학", "우주",
    # 문학
    "소설", "에세이", "시", "판타지", "추리", "SF", "로맨스",
    # 라이프스타일
    "요리", "여행", "육아", "건강", "운동", "다이어트",
    # 자기계발
    "자기계발", "습관", "생산성", "인간관계", "리더십", "커뮤니케이션",
    # 예술/디자인
    "디자인", "예술", "음악", "영화", "사진",
]


def collect_all(output: Path) -> int:
    """알라딘 + 카카오 실데이터를 NDJSON으로 저장하고 총 건수를 반환."""
    output.parent.mkdir(parents=True, exist_ok=True)

    seen_ids: set[str] = set()
    total_written = 0

    with output.open("w", encoding="utf-8") as f:
        # 1) 알라딘 (카테고리 × 쿼리타입)
        if ALADIN_TTB_KEY:
            with AladinClient(ttb_key=ALADIN_TTB_KEY) as aladin:
                for cat_name, cat_id in CATEGORY_IDS.items():
                    for qt in QUERY_TYPES:
                        try:
                            iterator = aladin.list_by_category(cat_id, qt)
                            for book in tqdm(iterator, desc=f"[Aladin] {cat_name}/{qt}", unit="book"):
                                if book.id in seen_ids:
                                    continue
                                seen_ids.add(book.id)
                                f.write(book.model_dump_json() + "\n")
                                total_written += 1
                        except Exception as e:
                            print(f"  ! Aladin {cat_name}/{qt} error: {e}")
        else:
            print("[skip] ALADIN_TTB_KEY 미설정")

        # 2) 카카오 (광범위 키워드)
        if KAKAO_REST_API_KEY:
            with KakaoBookClient(rest_api_key=KAKAO_REST_API_KEY) as kakao:
                for query in KAKAO_QUERIES:
                    try:
                        iterator = kakao.search(query)
                        for book in tqdm(iterator, desc=f"[Kakao] {query}", unit="book"):
                            if book.id in seen_ids:
                                continue
                            seen_ids.add(book.id)
                            f.write(book.model_dump_json() + "\n")
                            total_written += 1
                    except Exception as e:
                        print(f"  ! Kakao '{query}' error: {e}")
        else:
            print("[skip] KAKAO_REST_API_KEY 미설정")

    return total_written

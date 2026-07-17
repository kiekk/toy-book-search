"""카테고리 매칭 방식으로 도서 데이터를 증식한다.

- 시드 데이터가 있으면 실제 출판사·저자 pool을 재사용해 자연스러움을 높인다
- 카테고리별 topic 사전과 제목 템플릿을 조합해 검색 학습 재료로 활용
"""
import json
import random
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from faker import Faker
from tqdm import tqdm

from ..schema import Book


TITLE_TEMPLATES: list[str] = [
    "{adj} {topic}의 세계",
    "{topic}, {adj} 시작",
    "다시 쓰는 {topic}",
    "{topic}의 모든 것",
    "실전 {topic}: {adj} 접근",
    "완벽한 {topic}",
    "{noun}과 함께 배우는 {topic}",
    "{topic} 완벽 가이드",
    "쉽게 배우는 {topic}",
    "한 번에 정리하는 {topic}",
    "{noun}을 위한 {topic}",
    "{adj} {topic} 프로젝트",
]


CATEGORY_TOPICS: dict[str, list[str]] = {
    "컴퓨터/모바일": [
        "파이썬", "코틀린", "자바", "타입스크립트", "러스트", "고랭",
        "리액트", "스프링", "MSA", "쿠버네티스", "도커", "데이터베이스",
        "알고리즘", "머신러닝", "딥러닝", "인공지능", "웹개발",
    ],
    "경제경영": [
        "재테크", "투자", "부동산", "주식", "마케팅",
        "브랜드 전략", "조직 문화", "리더십", "창업", "경영전략",
    ],
    "인문학": [
        "철학", "역사", "심리학", "인류학", "고전", "동양 사상", "언어학",
    ],
    "소설시희곡": [
        "미스터리", "판타지", "SF", "로맨스", "역사 소설", "성장 소설", "청춘 소설",
    ],
    "에세이": [
        "일상", "여행", "위로", "관계", "회고", "산문",
    ],
    "과학": [
        "물리학", "천문학", "생물학", "화학", "수학", "지구과학", "뇌과학",
    ],
    "자기계발": [
        "습관", "생산성", "시간 관리", "마음챙김", "커뮤니케이션", "학습법",
    ],
    "역사": [
        "한국사", "세계사", "동양사", "서양사", "고대사", "근현대사",
    ],
    "예술/대중문화": [
        "미술", "음악", "영화", "사진", "디자인", "건축", "공예",
    ],
}


ADJECTIVES: list[str] = [
    "새로운", "완벽한", "쉬운", "빠른", "깊은", "실전",
    "차세대", "기본", "핵심", "친절한", "본격", "재미있는",
]

NOUNS: list[str] = [
    "개발자", "학생", "초보자", "실무자", "전문가",
    "리더", "팀장", "연구자", "기획자", "디자이너",
]


# 한글 description 템플릿. Faker(ko_KR)의 paragraph()는 라틴어로 fallback되므로 직접 조합.
DESCRIPTION_TEMPLATES: list[str] = [
    "{topic}에 대한 깊이 있는 이해를 돕는 책이다. 초보자부터 실무자까지 참고할 수 있도록 구성했다.",
    "{topic}의 핵심 개념을 실제 사례와 함께 정리한다. 이론과 실전을 균형 있게 다룬다.",
    "{topic}을(를) 처음 접하는 독자를 위한 친절한 안내서. 기초부터 심화까지 단계적으로 설명한다.",
    "{topic} 관련 실전 노하우와 풍부한 예제를 담았다. 현장에서 바로 활용 가능한 팁이 가득하다.",
    "{topic}의 역사부터 최신 트렌드까지 폭넓게 다룬다. 통찰력 있는 관점을 제시한다.",
    "{topic}을(를) 다양한 각도에서 조명한다. 새로운 시각과 사고의 지평을 넓혀 준다.",
    "복잡한 {topic} 개념을 쉬운 언어로 풀어낸다. 도표와 그림을 활용해 이해를 돕는다.",
    "{topic}에 관한 오랜 연구 결과를 집대성했다. 학술적 깊이와 대중적 접근성을 모두 갖췄다.",
    "{topic} 분야의 최전선에서 활동하는 저자가 자신의 경험을 아낌없이 공유한다.",
    "{topic}을(를) 배우려는 이들에게 든든한 길잡이가 되어 줄 책이다.",
]


def _extract_pools(seed_file: Path) -> tuple[list[str], list[str]]:
    """시드 NDJSON에서 출판사·저자 빈도 상위를 pool로 추출."""
    publisher_ctr: Counter[str] = Counter()
    author_ctr: Counter[str] = Counter()

    with seed_file.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                doc = json.loads(line)
            except json.JSONDecodeError:
                continue
            if doc.get("publisher"):
                publisher_ctr[doc["publisher"]] += 1
            for a in doc.get("authors", []) or []:
                if a:
                    author_ctr[a] += 1

    publishers = [p for p, _ in publisher_ctr.most_common(200)]
    authors = [a for a, _ in author_ctr.most_common(500)]
    return publishers, authors


def generate(
    count: int,
    output: Path,
    seed_file: Optional[Path] = None,
    random_seed: Optional[int] = 42,
) -> int:
    """count건의 도서를 생성해 NDJSON으로 저장. 생성된 건수 반환."""
    if random_seed is not None:
        random.seed(random_seed)
        Faker.seed(random_seed)
    fake = Faker("ko_KR")

    publishers: list[str] = []
    authors_pool: list[str] = []
    if seed_file and seed_file.exists():
        publishers, authors_pool = _extract_pools(seed_file)

    if not publishers:
        publishers = [f"{fake.company()} 출판사" for _ in range(200)]
    if not authors_pool:
        authors_pool = [fake.name() for _ in range(500)]

    output.parent.mkdir(parents=True, exist_ok=True)

    used_isbns: set[str] = set()
    categories_list = list(CATEGORY_TOPICS.keys())

    with output.open("w", encoding="utf-8") as f:
        for _ in tqdm(range(count), desc="[Generate]", unit="book"):
            category = random.choice(categories_list)
            topic = random.choice(CATEGORY_TOPICS[category])
            template = random.choice(TITLE_TEMPLATES)
            title = template.format(
                adj=random.choice(ADJECTIVES),
                noun=random.choice(NOUNS),
                topic=topic,
            )

            # 유효 checksum이 아닌 dummy ISBN13 (979 prefix로 실제 도서와 구분)
            while True:
                isbn13 = f"979{random.randint(10**9, 10**10 - 1)}"
                if isbn13 not in used_isbns:
                    used_isbns.add(isbn13)
                    break

            days_ago = random.randint(0, 20 * 365)
            published_at = date.today() - timedelta(days=days_ago)

            num_authors = random.choices([1, 2, 3], weights=[70, 25, 5])[0]
            authors = random.sample(authors_pool, k=min(num_authors, len(authors_pool)))

            description_sentences = random.sample(DESCRIPTION_TEMPLATES, k=3)
            description = " ".join(s.format(topic=topic) for s in description_sentences)

            book = Book(
                id=f"isbn:{isbn13}",
                title=title,
                authors=authors,
                publisher=random.choice(publishers),
                published_at=published_at,
                isbn13=isbn13,
                categories=["국내도서", category, topic],
                description=description,
                page_count=random.randint(100, 800),
                language="ko",
                price=random.randint(10, 40) * 1000,
                source="generated",
            )
            f.write(book.model_dump_json() + "\n")

    return count

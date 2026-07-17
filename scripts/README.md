# book-seeder

toy-book-search Phase 2: 실데이터 수집 + 증식 데이터 생성.

## 스택

- Python 3.11 + `uv`
- httpx (HTTP), pydantic v2 (스키마), faker (증식), typer (CLI)

## 설치

```bash
cd scripts
uv sync
```

## API 키 세팅

`.env.example` 복사 후 값 채워넣기:

```bash
cp .env.example .env
```

- **알라딘 TTB Key**: <https://blog.aladin.co.kr/openapi>
- **카카오 REST API Key**: <https://developers.kakao.com/> 앱 생성 후 REST API 키

## 사용법

### 1. 실데이터 수집 (알라딘 + 카카오)

```bash
uv run book-seeder seed
```

- 기본 저장 경로: `../data/seeds/books-seed.ndjson`
- ISBN13 기준 중복 제거
- 알라딘: 카테고리(10개) × 쿼리타입(4개) 조합
- 카카오: 40여 개 광범위 키워드
- 예상 수집량: **1~2만 건** (중복 제외)
- 예상 소요: **30분 ~ 2시간** (rate limit 의존)

### 2. 증식 데이터 생성 (100만 건)

```bash
uv run book-seeder generate --count 1000000
```

- 기본 저장 경로: `../data/generated/books-generated.ndjson`
- 시드 데이터에서 출판사·저자 pool 재사용 (자연스러움 ↑)
- 카테고리별 topic 사전 + 제목 템플릿 조합
- ISBN13은 `979` prefix + 랜덤 (실 checksum 아님, 실도서와 구분 목적)
- 예상 소요: **5~15분**

### 3. 옵션 조정

```bash
uv run book-seeder seed --output custom/path.ndjson
uv run book-seeder generate --count 100000 --seed 123
```

## 출력 스키마

```json
{
  "id": "isbn:9788960777330",
  "title": "클린 코드",
  "authors": ["로버트 C. 마틴"],
  "translators": ["박재호", "이해영"],
  "publisher": "인사이트",
  "published_at": "2013-12-24",
  "isbn13": "9788960777330",
  "categories": ["국내도서", "컴퓨터/모바일", "프로그래밍"],
  "description": "...",
  "language": "ko",
  "cover_url": "https://...",
  "price": 33000,
  "source": "aladin"
}
```

전체 스키마는 [`src/book_seeder/schema.py`](src/book_seeder/schema.py) 참고.

## 데이터 파일 위치

프로젝트 루트의 `data/` 하위에 저장되며 `.gitignore` 대상이다.

```
toy-book-search/
├── scripts/                    (이 폴더)
└── data/
    ├── seeds/books-seed.ndjson         실데이터
    └── generated/books-generated.ndjson 증식데이터
```

## 참고

- 카카오: 일 300,000회, 페이지당 50건, 최대 50페이지
- 알라딘: 일 5,000회, 페이지당 50건, 최대 20페이지
- 두 API 모두 초당 제한은 명시 없음 (요청 실패 시 재시도 로직 추가 고려)

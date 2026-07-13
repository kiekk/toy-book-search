# Roadmap

9-Phase 상세. 각 Phase는 독립 커밋 단위이자 학습 결과물이다.

---

## Phase 1 · 세팅

**목표**: Docker Compose로 OpenSearch + Dashboards + Nori 플러그인이 정상 기동되는 상태.

**할 일**:
- `docker/opensearch/Dockerfile` — Nori pre-install
- `compose.yml` — OpenSearch 2.15, Dashboards 2.15, network, volume
- Spring Boot 4.0 스켈레톤 (Kotlin, Gradle KTS)
- `docker compose up -d --build` 후 `curl localhost:9200`, `localhost:5601` 접속 확인

**완료 기준**: OpenSearch 헬스체크 green, Dashboards 접속, Nori 플러그인 목록 노출

---

## Phase 2 · 데이터 확보

**목표**: 실데이터 1~2만 + 증식 데이터 100만 건이 준비된 JSON/NDJSON 파일.

**할 일**:
- 국립중앙도서관 오픈 API로 서지 데이터 수집 스크립트 (Kotlin 또는 Python)
- 알라딘 상품 검색 API로 카테고리·베스트셀러 데이터 보완
- Faker + 카테고리 pool로 100만 건 증식 (Kotlin 스크립트)
- 데이터 스키마 정의: `id`, `title`, `subtitle`, `authors[]`, `publisher`, `publishedAt`, `isbn`, `categories[]`, `description`, `pageCount`, `language`

**결과물**: `data/seeds/books-seed.ndjson`, `data/generated/books-generated.ndjson` (gitignore)

---

## Phase 3 · 색인 설계

**목표**: 색인 매핑 확정 + bulk API로 100만 건 색인.

**할 일**:
- OpenSearch 매핑 JSON (`docs/mappings/books-v1.json`) — text/keyword 분리, analyzer 매핑
- Bulk API 색인 스크립트 (`_bulk` endpoint 활용)
- 색인 성능 측정 (레코드/초, 인덱스 크기)
- Force merge, refresh interval 튜닝 실험

**학습 포인트**: text vs keyword, `multi-fields`, dynamic mapping의 함정, `_source` 최적화

---

## Phase 4 · 기본 검색

**목표**: `/api/search?q=...` REST API로 검색 결과 반환.

**할 일**:
- `opensearch-java` 클라이언트 세팅 + Spring Boot 4.0 통합
- Controller/Service 레이어 (jwt-auth-toy와 동일 구조)
- 쿼리 3종 비교: `match`, `multi_match`, `bool` 조합
- 하이라이트 (`highlight`) 응답

**학습 포인트**: Query DSL 기본, `should/must/filter` 차이, 점수 계산 원리

---

## Phase 5 · 한글 심화

**목표**: 한글 검색 품질을 눈에 띄게 개선.

**할 일**:
- Nori analyzer 매핑 적용 (`nori_tokenizer`, `nori_readingform`, `nori_part_of_speech`)
- 사용자 사전 (`user_dictionary`) — 브랜드·인명 등 미등록 어휘 추가
- 동의어 사전 (`synonym_graph`) — "AI ⇔ 인공지능", "JS ⇔ JavaScript" 등
- 오타 교정 (`fuzzy`, `_search_analyzer` 조정)
- Before/After 검색 품질 비교 문서화

**학습 포인트**: 형태소 분석기 파이프라인, 색인/검색 분석기 분리, 사전 hot-reload

---

## Phase 6 · 자동완성

**목표**: 3가지 방식 비교 후 프로젝트에 맞는 것 선택.

**할 일**:
- **A. Edge n-gram** — `edge_ngram` tokenizer 기반. 색인 커짐, 다양한 매칭 가능
- **B. Completion Suggester** — 전용 자료구조 FST. 극도로 빠름, 유연성 낮음
- **C. Search-as-you-type** — 필드 타입 자체. edge n-gram 자동 생성 + shingling
- 각각 latency, 색인 크기, 유연성 벤치 → 표로 정리
- Nori와의 조합 방법

**학습 포인트**: FST 자료구조, prefix vs infix 매칭, `context` 기반 조건 필터링

---

## Phase 7 · Facet

**목표**: 검색 결과에 카테고리/저자/발행연도 facet aggregation.

**할 일**:
- `terms`, `date_histogram`, `range` aggregation 조합
- Sub-aggregation (카테고리 별 인기 저자)
- `post_filter` vs `filter` in aggregation — facet count 왜곡 방지
- `composite` aggregation으로 페이지네이션

**학습 포인트**: aggregation 실행 시점, cardinality 근사치 (HyperLogLog), memory 압박 관리

---

## Phase 8 · React UI

**목표**: Next.js 14 (App Router) 로 검색 UX 완성.

**할 일**:
- Next.js 14 프로젝트 (`web/`) 초기화
- 검색창 + debounce + 자동완성 드롭다운
- 결과 리스트 (하이라이트 렌더링)
- Facet 사이드바 (카테고리 · 저자 · 연도)
- Server Components + Route Handlers로 SSR 검색
- Cursor pagination (`search_after`)

**학습 포인트**: App Router의 데이터 fetching, SSR vs CSR 트레이드오프, 스트리밍

---

## Phase 9 · 랭킹 튜닝 (심화)

**목표**: 검색 결과의 관련도를 실제로 개선.

**할 일**:
- BM25 `k1`, `b` 파라미터 실험
- `function_score` — 최근 발행 도서 boost, 인기도 boost
- `rescore` — 2단계 정렬 (fast query → 정밀 rescore)
- Explain API (`?explain=true`) 로 점수 근거 분석

**학습 포인트**: TF-IDF vs BM25, script_score 안전한 사용, 랭킹 지표 (nDCG, MRR)

---

## Phase별 산출물 문서

각 Phase 완료 시 다음 문서를 `docs/` 에 추가:

- `docs/phase-1-setup.md` — Docker Compose 구성 결정 근거, 트러블슈팅
- `docs/phase-2-data.md` — 데이터 소스, 스키마, 증식 알고리즘
- `docs/phase-3-indexing.md` — 매핑 설계 근거, 성능 측정
- ... (이하 동일)

문서 스타일은 `jwt-auth-toy/docs/` 와 동일하게 유지 (Mermaid 활용, 실제 코드 근거).

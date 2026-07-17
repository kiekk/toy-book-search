# Phase 3 · 색인 설계와 Bulk 색인

## 목표

- OpenSearch에 `books` 인덱스 매핑을 설계·적용
- 실데이터 60K + 증식 데이터 1M을 bulk API로 색인
- 성능 측정과 초기 검색 검증
- Phase 5(Nori)에서 개선할 지점을 데이터로 확인

## 매핑 (books-v1)

전체 정의: [`docs/mappings/books-v1.json`](mappings/books-v1.json)

주요 결정 사항:

| 항목 | 값 | 근거 |
|---|---|---|
| `number_of_shards` | 1 | 단일 노드 · 100만 건은 프라이머리 1샤드로 충분 (권장 30~50 GB/샤드 대비 훨씬 작음) |
| `number_of_replicas` | 0 | single-node에선 replica가 unassigned 됨 |
| `refresh_interval` | `30s` (색인 시 `-1`, 완료 후 `1s`) | 대량 색인 중 refresh 오버헤드 제거 |
| `dynamic` | `strict` | 스키마 표류 조기 감지 |
| Analyzer | 기본 (`standard`) | Phase 5에서 Nori로 교체 — 개선 폭 관찰용 |

### 필드 전략

- **text + keyword (multi-fields)**: `title`, `authors`, `translators`, `publisher` — 검색과 정렬·facet 둘 다 지원
- **keyword only**: `id`, `isbn13/10`, `categories`, `language`, `source` — facet/필터 용도
- **date**: `published_at` — `yyyy-MM-dd || ISO 8601 || epoch_millis` 다중 포맷
- **integer**: `page_count`, `price`
- **저장만 (`index:false, doc_values:false`)**: `cover_url` — 검색·정렬 대상 아님, 인덱스 크기 절감

## Bulk 색인 스크립트

`book-seeder index --input <file> --index books` 명령 추가 (`scripts/src/book_seeder/indexer.py`).

핵심 최적화:

1. **`refresh_interval = -1`** 로 색인 중 refresh 완전 억제 → 완료 후 `1s` 로 복구 + `_refresh` 강제 호출
2. **`helpers.streaming_bulk`** with `chunk_size=1000` — 메모리 폭증 방지하며 스트리밍
3. `http_compress=True` — 네트워크 페이로드 압축
4. `max_retries=3, initial_backoff=2` — 일시적 실패 재시도

## 성능 측정 결과

| 데이터셋 | 문서 수 | 소요 시간 | 처리량 | 실패 |
|---|---:|---:|---:|---:|
| Seed (실데이터) | 60,239 | 11.4s | **5,297 doc/sec** | 0 |
| Generated (증식) | 1,000,000 | 98.2s | **10,182 doc/sec** | 0 |

- 총 1,060,238 문서 (dedup 1건: seed 내 같은 ISBN)
- **인덱스 크기: 340.7 MB** (문서당 약 336 bytes)
- 세그먼트 7개 — force merge 시 검색 latency 개선 여지 (학습용이라 미실행)

### 처리량이 seed vs generated 다른 이유

- Seed는 실제 도서 데이터로 필드 길이가 다양(description 짧거나 없음)
- Generated는 항상 3~5문장의 description 포함, 다만 지연 없이 미리 준비된 상태라 파일 I/O 병목이 적음
- 실제로는 두 번째 색인에서 세그먼트가 커지면서 힙 · flush 부담이 늘 수 있음. 여기선 refresh 억제로 flush 지연을 줄여 오히려 두 번째가 더 빨랐음

## 검색 검증

### Query 1 — `match` 한글 완전 단어

```json
{ "query": { "match": { "title": "코틀린" } } }
```

- **총 5,619건 매칭 · 80ms**
- Top 결과: "코틀린 아카데미: 이펙티브 코틀린", "아토믹 코틀린" 등 자연스러운 관련 도서
- ✅ 완전 단어(공백 구분)면 standard analyzer로도 잘 동작

### Query 2 — `multi_match` 명사구

```json
{ "query": { "multi_match": {
    "query": "인공지능",
    "fields": ["title^3", "description", "authors^2"]
} } }
```

- 총 7,595건 매칭 · 37ms
- **문제 발견**: 결과 top이 전부 "인공지능"이라는 정확 title. Standard analyzer는 `인공지능`을 하나의 토큰으로 취급하고, `인공`이나 `지능` 단독으로는 매칭 못 함. **부분 매칭 불가**.
- → **Phase 5 Nori 도입 시 이 쿼리로 개선폭 측정** 예정

### Query 3 — Terms aggregation (source별)

```json
{ "size": 0, "aggs": {
    "by_source": { "terms": { "field": "source" } }
} }
```

| source | count |
|---|---:|
| generated | 1,000,000 |
| kakao | 47,174 |
| aladin | 13,064 |

### Query 4 — 카테고리 facet 상위 10

- 국내도서 (1,013,064), 역사 (127K), 인문학 (113K), 컴퓨터/모바일 (113K), 에세이 (113K), 예술 (113K), 자기계발 (112K), 경제경영 (112K), 과학 (111K), 소설시희곡 (110K)
- 증식 데이터가 균등 분포되어 통계적으로 안정적

### Query 5 — Date range

```json
{ "query": { "range": { "published_at": { "gte": "2025-01-01" } } } }
```

- 2025년 이후 발행: **92,650건**

## 학습 포인트 요약

| 영역 | 관찰 | 다음 액션 |
|---|---|---|
| Standard analyzer | 한글 부분 매칭 불가 (`인공지능` 검색은 되지만 `인공` 검색은 안 됨) | **Phase 5**: Nori 형태소 분석기 적용 후 `books-v2` 매핑 + 재색인, before/after 비교 |
| Multi-fields 오버헤드 | 대부분 필드에 `.keyword` 추가 → 인덱스 크기 340 MB (문서당 336 B) | 필요 없는 keyword field 정리 후 크기 재측정 |
| Refresh 튜닝 효과 | `refresh_interval=-1` 로 처리량 극대화 | Sliding window 색인이 필요한 상황에서는 다른 값 필요 (예: 검색이 병행되는 경우) |
| 세그먼트 병합 | 색인 후 7개 세그먼트 → force merge로 검색 latency 개선 여지 | `_forcemerge?max_num_segments=1` 실행 전후 latency 비교 예정 |
| 인덱스 재구성 | v1 → v2 매핑 변경 시 alias 활용 필요 | Phase 5 진입 시 alias `books` → `books-v1`, `books-v2` 무중단 전환 실습 |

## 트러블슈팅 기록

- **`?` 파라미터의 zsh glob 이슈**: `curl http://.../_cat/plugins?v` 가 `zsh: no matches found` 오류. URL 전체를 single quote 로 감싸야 함. (예: `curl 'http://.../_cat/plugins?v'`)
- **Docker daemon 대기**: `open -a Docker` 후 `until docker ps &>/dev/null; do sleep 2; done` 로 조건 대기
- **첫 이미지 빌드 시간**: `analysis-nori` 플러그인 다운로드·설치에 약 90초 (opensearch 2.15 base + Nori 2.15.0)

## 인프라 상태

- OpenSearch: `http://localhost:9200`
- Dashboards: `http://localhost:5601`
- 이미지: `book-search-opensearch` (Nori 사전 설치)
- 볼륨: `book-search_opensearch-data` (docker compose down -v 로 삭제)

# Mappings

OpenSearch 인덱스 매핑 정의. 파일명 `books-v{N}.json` 은 인덱스 버전을 의미하며, 새 매핑이 필요할 때마다 새 버전 파일을 만들고 alias로 무중단 전환한다.

## books-v1.json (Phase 3)

### 설계 근거

**settings**
- `number_of_shards: 1` — 단일 노드, 100만 건은 프라이머리 1샤드로 충분 (권장 30~50GB/샤드 대비 훨씬 작음)
- `number_of_replicas: 0` — single-node라 replica 만들어도 unassigned 상태
- `refresh_interval: 30s` — 대량 bulk 색인 중 refresh 오버헤드 최소화. 색인 완료 후 `1s` (기본값) 로 변경

**mappings**
- `dynamic: strict` — 스키마 외 필드는 색인 거부 → 오타·스키마 표류 조기 감지
- `text + keyword` 이중 필드 — 검색(text)과 정렬·facet(keyword) 양쪽 지원
  - `title.keyword`, `authors.keyword`, `publisher.keyword` 등
  - `ignore_above` 로 지나치게 긴 값(광고 문구 등)의 keyword 색인 skip
- **keyword만** 사용한 필드: `categories`, `language`, `source`, `isbn13`, `isbn10` — 검색보다는 필터/facet 용도
- `cover_url`: `index: false, doc_values: false` — 검색·정렬 대상이 아니라 저장만 하는 필드. 인덱스 크기 절감
- `published_at`: 다중 포맷 허용 (`yyyy-MM-dd`, ISO 8601, epoch)

### 학습 포인트

- **왜 이 Phase에서는 Nori를 안 쓰나?** 한국어에 대해 default `standard` analyzer가 얼마나 부족한지 눈으로 확인하기 위함. Phase 5에서 Nori를 적용한 `books-v2` 를 만들어 개선 정도를 비교한다.
- `dynamic: strict` vs `dynamic: false` vs `dynamic: true` — 새 필드가 들어왔을 때 각각 어떻게 동작하는지 실습 필요.
- Multi-fields (`fields`) 는 저장 공간을 소비한다 (같은 값을 두 방식으로 인덱스). 필드별 필요성을 판단해 최소한만 정의.

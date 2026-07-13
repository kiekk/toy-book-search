# toy-book-search

OpenSearch 기반 도서 검색 학습용 프로젝트. 한글 형태소 분석(Nori), 자동완성, Faceted search를 파고들며 색인 설계 · 랭킹 · 대규모 색인의 감각을 익힌다.

## 학습 목표

| Phase | 초점 |
|---|---|
| **A. 색인 매핑 설계** | text vs keyword, analyzer 조합, dynamic mapping |
| **B. 한글 형태소 분석** | Nori analyzer, 사용자 사전, 동의어 사전 |
| **D. 자동완성** | edge n-gram vs completion suggester vs search-as-you-type — 3종 비교 |
| **C. 랭킹 튜닝 (심화)** | BM25 파라미터, function_score, boost |

상세 로드맵은 [`docs/roadmap.md`](docs/roadmap.md).

## 기술 스택

| 항목 | 선택 |
|---|---|
| 언어/프레임워크 | Kotlin 2.1 + **Spring Boot 4.0** |
| 검색 엔진 | OpenSearch 2.15 (+ Nori 플러그인) |
| 클라이언트 | `opensearch-java` 2.x (Phase 3에 도입) |
| 테스트 | Kotest + MockK + TestContainers (`opensearch-testcontainers`) |
| Frontend | Next.js 14 (App Router) — Phase 8 |
| 인프라 | Docker Compose (OpenSearch + Dashboards) |

## 실행 방법

### 사전 요구사항

- Java 21
- Docker Desktop / Colima
- Node.js 20+ (Frontend 시작 시)

### OpenSearch 클러스터 기동

```bash
docker compose up -d --build
```

- OpenSearch: http://localhost:9200
- Dashboards: http://localhost:5601

Nori 플러그인이 사전 설치된 커스텀 이미지가 빌드된다.

### 앱 실행 (Phase 4 이후)

```bash
./gradlew bootRun
```

### 종료 & 데이터 초기화

```bash
docker compose down          # 컨테이너만 종료 (데이터 유지)
docker compose down -v       # 볼륨까지 삭제 (색인 초기화)
```

## 데이터 전략

- **시드**: 국립중앙도서관 오픈 API + 알라딘 상품 검색 API 로 실제 한글 도서 1~2만 건
- **증식**: Faker + 카테고리·저자 pool 조합으로 100만 건 이상 확장
- 실데이터는 한글 형태소 학습에, 증식 데이터는 규모 학습(bulk 색인, latency 벤치)에 사용

## 로드맵 (9-Phase)

```
Phase 1 · 세팅           Docker Compose (OpenSearch + Dashboards + Nori)
Phase 2 · 데이터 확보    실데이터 시드 + Faker 증식 → 100만 건 준비
Phase 3 · 색인 설계      매핑 (analyzer 조합), bulk API 색인
Phase 4 · 기본 검색      match / multi_match / bool
Phase 5 · 한글 심화      Nori + 사용자 사전 + 동의어 사전
Phase 6 · 자동완성       edge n-gram vs completion suggester vs search-as-you-type
Phase 7 · Facet          카테고리/저자/발행연도 aggregation
Phase 8 · React UI       Next.js 14 (App Router) + 검색창/자동완성/facet
Phase 9 · 랭킹 (심화)    BM25 · function_score · boost 튜닝
```

각 Phase 완료 시 `docs/` 에 학습 기록을 남긴다.

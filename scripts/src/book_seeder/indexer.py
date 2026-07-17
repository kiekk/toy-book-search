"""OpenSearch bulk 색인 유틸.

NDJSON 파일을 스트리밍하며 opensearch-py의 helpers.streaming_bulk로 색인한다.
- 색인 시작 시 refresh_interval을 -1로 억제해 처리량을 극대화
- 완료 시 refresh_interval을 1s로 복구하고 강제 refresh
"""
import json
import time
from pathlib import Path
from typing import Iterator

from opensearchpy import OpenSearch, helpers
from tqdm import tqdm


def _iter_actions(ndjson: Path, index_name: str) -> Iterator[dict]:
    with ndjson.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                doc = json.loads(line)
            except json.JSONDecodeError:
                continue
            book_id = doc.get("id")
            if not book_id:
                continue
            yield {
                "_op_type": "index",
                "_index": index_name,
                "_id": book_id,
                "_source": doc,
            }


def _count_lines(path: Path) -> int:
    total = 0
    with path.open("rb") as f:
        for _ in f:
            total += 1
    return total


def bulk_index(
    ndjson: Path,
    index_name: str = "books",
    host: str = "localhost",
    port: int = 9200,
    chunk_size: int = 1000,
    request_timeout: int = 120,
) -> tuple[int, int, float]:
    """NDJSON을 OpenSearch에 bulk 색인. (success, failed, elapsed_sec) 반환."""
    client = OpenSearch(
        hosts=[{"host": host, "port": port}],
        use_ssl=False,
        verify_certs=False,
        http_compress=True,
        timeout=request_timeout,
    )

    total = _count_lines(ndjson)

    # 색인 처리량 극대화: refresh 억제 (매핑 default 30s → 색인 중 -1)
    client.indices.put_settings(
        index=index_name,
        body={"index": {"refresh_interval": "-1"}},
    )

    success = 0
    failed = 0
    start = time.time()

    pbar = tqdm(total=total, desc=f"[Index → {index_name}]", unit="doc")
    try:
        for ok, item in helpers.streaming_bulk(
            client,
            _iter_actions(ndjson, index_name),
            chunk_size=chunk_size,
            request_timeout=request_timeout,
            raise_on_error=False,
            raise_on_exception=False,
            max_retries=3,
            initial_backoff=2,
        ):
            if ok:
                success += 1
            else:
                failed += 1
            pbar.update(1)
    finally:
        pbar.close()
        # 색인 완료: refresh_interval 원복 + 강제 refresh
        client.indices.put_settings(
            index=index_name,
            body={"index": {"refresh_interval": "1s"}},
        )
        client.indices.refresh(index=index_name)

    elapsed = time.time() - start
    return success, failed, elapsed

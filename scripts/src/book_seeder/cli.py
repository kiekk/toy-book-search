"""book-seeder CLI entry point."""
from pathlib import Path

import typer
from typing_extensions import Annotated


app = typer.Typer(
    help="toy-book-search 데이터 수집·증식 스크립트",
    no_args_is_help=True,
)


@app.command()
def seed(
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="저장 경로"),
    ] = Path("data/seeds/books-seed.ndjson"),
) -> None:
    """알라딘 + 카카오에서 실데이터 수집 → NDJSON 저장."""
    from .collectors.seed import collect_all

    total = collect_all(output)
    typer.secho(f"[OK] {total:,} 건 수집 → {output}", fg=typer.colors.GREEN)


@app.command()
def generate(
    count: Annotated[
        int,
        typer.Option("--count", "-n", help="생성할 도서 수"),
    ] = 1_000_000,
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="저장 경로"),
    ] = Path("data/generated/books-generated.ndjson"),
    seed_file: Annotated[
        Path,
        typer.Option("--seed-file", help="출판사·저자 pool 추출용 시드 NDJSON"),
    ] = Path("data/seeds/books-seed.ndjson"),
    random_seed: Annotated[
        int,
        typer.Option("--seed", help="난수 시드 (재현성)"),
    ] = 42,
) -> None:
    """카테고리 매칭 방식으로 증식 데이터 생성."""
    from .generators.faker import generate as gen

    written = gen(count=count, output=output, seed_file=seed_file, random_seed=random_seed)
    typer.secho(f"[OK] {written:,} 건 생성 → {output}", fg=typer.colors.GREEN)


@app.command()
def index(
    input_file: Annotated[
        Path,
        typer.Option("--input", "-i", help="색인할 NDJSON 파일"),
    ],
    index_name: Annotated[
        str,
        typer.Option("--index", help="OpenSearch 인덱스 이름"),
    ] = "books",
    host: Annotated[
        str,
        typer.Option("--host", help="OpenSearch 호스트"),
    ] = "localhost",
    port: Annotated[
        int,
        typer.Option("--port", help="OpenSearch 포트"),
    ] = 9200,
    chunk_size: Annotated[
        int,
        typer.Option("--chunk-size", help="bulk 청크 크기"),
    ] = 1000,
) -> None:
    """NDJSON 파일을 OpenSearch에 bulk 색인."""
    from .indexer import bulk_index

    success, failed, elapsed = bulk_index(
        ndjson=input_file,
        index_name=index_name,
        host=host,
        port=port,
        chunk_size=chunk_size,
    )
    color = typer.colors.GREEN if failed == 0 else typer.colors.YELLOW
    typer.secho(
        f"[OK] {success:,} 건 성공 · {failed:,} 건 실패 · {elapsed:.1f}s",
        fg=color,
    )
    if elapsed > 0:
        typer.echo(f"     평균 처리량: {success / elapsed:,.0f} doc/sec")


if __name__ == "__main__":
    app()

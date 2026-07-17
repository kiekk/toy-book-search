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


if __name__ == "__main__":
    app()

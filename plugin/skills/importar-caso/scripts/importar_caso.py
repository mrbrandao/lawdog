#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""Apply confirmed case ingestion manifest to lawdog-cases structure.

Creates NN-tipo/ dirs, copies/moves files, generates caso.md.
Idempotent: safe to run twice.

Usage:
    uv run importar_caso.py --slug SLUG --cases-dir DIR --manifest JSON
"""
import argparse
import json
import shutil
import sys
from datetime import date
from pathlib import Path


def resolve_conflict(dest: Path) -> Path:
    if not dest.exists():
        return dest
    stem, suffix, parent = dest.stem, dest.suffix, dest.parent
    n = 1
    while True:
        c = parent / f"{stem}-{n}{suffix}"
        if not c.exists():
            return c
        n += 1


def copy_or_move(src: Path, dest_dir: Path, cases_dir: Path) -> Path:
    dest = resolve_conflict(dest_dir / src.name)
    try:
        if src.is_relative_to(cases_dir):
            shutil.move(str(src), str(dest))
            action = "moved"
        else:
            shutil.copy2(str(src), str(dest))
            action = "copied"
    except OSError as e:
        print(f"  ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"  {action}: {src.name} -> {dest.name}")
    return dest


def create_movement_dirs(base: Path, seq: str, mov_type: str) -> Path:
    mov_dir = base / f"{seq}-{mov_type}"
    docs_dir = mov_dir / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    if "peticao" in mov_type:
        (mov_dir / "anexos").mkdir(exist_ok=True)
        (mov_dir / "juntada").mkdir(exist_ok=True)
    return docs_dir


def generate_caso_md(slug: str, movements: list[dict]) -> str:
    today = date.today().strftime("%Y-%m-%d")
    last = movements[-1] if movements else None
    last_dir = f"{last['seq']}-{last['type']}/" if last else "—"
    rows = "\n".join(
        f"| {m['seq']} | {m['seq']}-{m['type']}/ | {today} | "
        f"{m['type'].replace('-', ' ').title()} | — | — |"
        for m in movements
    ) or "| — | — | — | — | — | — |"
    return f"""# Caso: {slug}

- **Aberto em:** {today}
- **Estado-Comarca:** — / —
- **Vara/Juizado:** a definir

## Partes

**Requerente:** — (preencher)

**Requerido:** — (preencher)

## Resumo

(Caso importado — preencher com o resumo do problema)

## Fundamento jurídico

(A preencher após análise)

## Timeline

| Data | Evento |
|------|--------|
| {today} | Caso importado para o lawdog |

## Evidências disponíveis

- (A preencher)

## Pontos fracos identificados

- (A analisar após revisão dos documentos)

## Estado atual

- **Fase:** judicial
- **Última movimentação:** {last_dir} — {today}
- **Prazo em curso:** nenhum (verificar documentos importados)
- **Ação pendente:** Revisar documentos e atualizar caso.md

## Movimentações

| Seq | Diretório | Data | Tipo | Ator | Prazo |
|-----|-----------|------|------|------|-------|
{rows}

## Petições

| # | Arquivo | Data | Status |
|---|---------|------|--------|
| — | — | {today} | importado |
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--cases-dir", required=True)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    cases_dir = Path(args.cases_dir)
    case_dir = cases_dir / args.slug
    manifest_path = Path(args.manifest)

    if not manifest_path.exists():
        print(f"ERROR: Manifest not found: {manifest_path}", file=sys.stderr)
        sys.exit(1)

    with open(manifest_path) as f:
        manifest = json.load(f)

    movements: list[dict] = manifest.get("movements", [])
    print(f"Applying: {len(movements)} movement(s) for '{args.slug}'")
    case_dir.mkdir(parents=True, exist_ok=True)

    for mov in movements:
        seq, mov_type = mov["seq"], mov["type"]
        files = [Path(f) for f in mov.get("files", [])]
        docs_dir = create_movement_dirs(case_dir, seq, mov_type)
        print(f"[{seq}-{mov_type}]")
        for src in files:
            if not src.exists():
                print(f"  WARN: not found: {src}", file=sys.stderr)
                continue
            copy_or_move(src, docs_dir, cases_dir)

    caso_md = case_dir / "caso.md"
    if not caso_md.exists():
        caso_md.write_text(generate_caso_md(args.slug, movements))
        print("Generated: caso.md")
    else:
        print("Skipped: caso.md already exists")

    print(f"\nDone: {case_dir}")


if __name__ == "__main__":
    main()

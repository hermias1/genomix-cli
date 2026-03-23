"""Built-in file tools for the agent."""
import gzip
import json
import os
from pathlib import Path

MAX_PREVIEW_LINES = 200
MAX_PREVIEW_CHARS = 50_000


def _open_text_file(path: Path):
    if path.suffix in {".gz", ".bgz"}:
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("rt", encoding="utf-8", errors="replace")


def _read_preview(path: Path) -> str:
    lines: list[str] = []
    chars = 0
    truncated_by_chars = False
    truncated_by_lines = False

    with _open_text_file(path) as handle:
        for raw_line in handle:
            if len(lines) >= MAX_PREVIEW_LINES:
                truncated_by_lines = True
                break

            remaining = MAX_PREVIEW_CHARS - chars
            if remaining <= 0:
                truncated_by_chars = True
                break

            if len(raw_line) > remaining:
                lines.append(raw_line[:remaining])
                chars += remaining
                truncated_by_chars = True
                break

            lines.append(raw_line)
            chars += len(raw_line)

    preview = "".join(lines)
    if not (truncated_by_lines or truncated_by_chars):
        return preview

    header = f"(showing first {len(lines)} lines"
    if truncated_by_chars:
        header += f", truncated at {MAX_PREVIEW_CHARS} chars"
    header += ")\n"
    return header + preview


def _is_vcf(path: Path) -> bool:
    """Check if a file is a VCF by extension or first line."""
    return path.name.endswith((".vcf", ".vcf.gz"))


def _annotate_vcf(text: str) -> str:
    """Add gene annotations to raw VCF lines that lack them."""
    from genomix.gene_db import get_gene_db

    db = get_gene_db()
    if not db.ensure_loaded():
        return text  # Can't annotate without DB, return raw

    lines = text.split("\n")
    result = []
    for line in lines:
        if line.startswith("#") or not line.strip():
            result.append(line)
            continue
        fields = line.split("\t")
        if len(fields) < 5:
            result.append(line)
            continue

        chrom, pos = fields[0], fields[1]
        info = fields[7] if len(fields) > 7 else "."

        # Only annotate if no GENEINFO already present
        if "GENEINFO=" not in info and "GENE=" not in info:
            try:
                genes = db.lookup(chrom, int(pos))
                if genes:
                    gene_tag = f"[GENE:{','.join(genes)}]"
                    # Append gene tag to the line
                    result.append(f"{line}\t{gene_tag}")
                    continue
            except (ValueError, IndexError):
                pass

        result.append(line)
    return "\n".join(result)


def read_file(args):
    try:
        path = Path(args["path"]).expanduser()
        text = _read_preview(path)

        # Auto-annotate raw VCF files with gene names
        if _is_vcf(path):
            text = _annotate_vcf(text)

        return text
    except Exception as e:
        return json.dumps({"error": str(e)})


def list_dir(args):
    try:
        return json.dumps(sorted(os.listdir(args.get("path", "."))))
    except Exception as e:
        return json.dumps({"error": str(e)})


def register_file_tools(registry):
    registry.register(
        name="read_file",
        description="Read a file's contents",
        parameters={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
        handler=read_file,
    )
    registry.register(
        name="list_dir",
        description="List directory contents",
        parameters={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
        handler=list_dir,
    )

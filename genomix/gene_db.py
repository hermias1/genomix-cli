"""Local gene coordinate database for instant coordinate → gene resolution.

Downloads GENCODE GRCh38 protein-coding gene coordinates once (~600KB),
caches locally, and provides fast lookup using bisect.
Covers all ~20,000 human protein-coding genes.
"""
from __future__ import annotations

import bisect
import gzip
import os
import re
from pathlib import Path
from typing import Any

GENCODE_URL = (
    "https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/"
    "release_46/gencode.v46.basic.annotation.gtf.gz"
)
CACHE_DIR = Path(os.environ.get("GENOMIX_HOME", Path.home() / ".genomix")) / "cache"
GENE_DB_PATH = CACHE_DIR / "genes_grch38.tsv"


class GeneDB:
    """Fast local gene coordinate lookup."""

    def __init__(self):
        self._genes: dict[str, list[tuple[int, int, str]]] = {}  # chr -> sorted [(start, end, name)]
        self._loaded = False

    def ensure_loaded(self) -> bool:
        """Load gene database, downloading if needed. Returns True if loaded."""
        if self._loaded:
            return True
        if not GENE_DB_PATH.exists():
            if not self._download():
                return False
        return self._load_from_file()

    def _download(self) -> bool:
        """Download and parse GENCODE annotation into a compact TSV."""
        try:
            import httpx
            CACHE_DIR.mkdir(parents=True, exist_ok=True)

            with httpx.Client(timeout=60, follow_redirects=True) as client:
                resp = client.get(GENCODE_URL)
                resp.raise_for_status()
                raw = gzip.decompress(resp.content).decode("utf-8")

            lines = []
            for line in raw.split("\n"):
                if line.startswith("#") or not line.strip():
                    continue
                fields = line.split("\t")
                if len(fields) < 9 or fields[2] != "gene":
                    continue
                if 'gene_type "protein_coding"' not in fields[8]:
                    continue
                m = re.search(r'gene_name "([^"]+)"', fields[8])
                if m:
                    lines.append(f"{fields[0]}\t{fields[3]}\t{fields[4]}\t{m.group(1)}")

            GENE_DB_PATH.write_text("\n".join(lines) + "\n")
            return True
        except Exception:
            return False

    def _load_from_file(self) -> bool:
        """Load TSV into memory for fast lookup."""
        try:
            for line in GENE_DB_PATH.read_text().splitlines():
                parts = line.split("\t")
                if len(parts) != 4:
                    continue
                chrom, start, end, name = parts
                chrom = chrom.replace("chr", "")
                if chrom not in self._genes:
                    self._genes[chrom] = []
                self._genes[chrom].append((int(start), int(end), name))

            # Sort by start position for binary search
            for chrom in self._genes:
                self._genes[chrom].sort()

            self._loaded = True
            return True
        except Exception:
            return False

    def lookup(self, chromosome: str, position: int) -> list[str]:
        """Find gene(s) at a given position. Returns list of gene symbols."""
        if not self.ensure_loaded():
            return []
        chrom = chromosome.replace("chr", "")
        genes = self._genes.get(chrom, [])
        if not genes:
            return []

        # Binary search: find genes whose range contains position
        # Find the rightmost gene that starts <= position
        starts = [g[0] for g in genes]
        idx = bisect.bisect_right(starts, position) - 1

        results = []
        # Check nearby genes (some overlap)
        for i in range(max(0, idx - 5), min(len(genes), idx + 6)):
            start, end, name = genes[i]
            if start <= position <= end:
                results.append(name)

        return results

    def gene_count(self) -> int:
        """Number of genes loaded."""
        return sum(len(v) for v in self._genes.values())


# Singleton instance
_db = GeneDB()


def get_gene_db() -> GeneDB:
    """Get the singleton gene database instance."""
    return _db


def annotate_vcf_line(chrom: str, pos: int) -> str:
    """Quick lookup: returns gene name(s) or empty string."""
    genes = _db.lookup(chrom, pos)
    return ", ".join(genes) if genes else ""

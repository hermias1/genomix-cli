"""Schema-aware response extractors for each database.

Instead of blindly truncating JSON at 2KB, each database extracts
only the clinically relevant fields. This preserves critical information
while keeping responses compact for the LLM context window.
"""
from __future__ import annotations

import json
from typing import Any


def extract_clinvar_summary(data: Any) -> str:
    """Extract key clinical fields from ClinVar esummary response."""
    if not isinstance(data, dict):
        return _fallback(data)
    result = data.get("result", data)
    uids = result.get("uids", [])
    entries = []
    for uid in uids[:5]:
        entry = result.get(str(uid), {})
        if not isinstance(entry, dict):
            continue
        entries.append({
            "uid": uid,
            "title": entry.get("title", ""),
            "clinical_significance": entry.get("clinical_significance", {}).get("description", ""),
            "review_status": entry.get("clinical_significance", {}).get("review_status", ""),
            "gene": entry.get("gene_sort", ""),
            "conditions": [t.get("trait_name", "") for t in entry.get("trait_set", [])[:3]],
            "variant_type": entry.get("variation_set", [{}])[0].get("variation", {}).get("variant_type", "") if entry.get("variation_set") else "",
        })
    return json.dumps({"variants": entries}, ensure_ascii=False)


def extract_ncbi_gene_summary(data: Any) -> str:
    """Extract key fields from NCBI gene esummary response."""
    if not isinstance(data, dict):
        return _fallback(data)
    result = data.get("result", data)
    uids = result.get("uids", [])
    entries = []
    for uid in uids[:3]:
        entry = result.get(str(uid), {})
        if not isinstance(entry, dict):
            continue
        entries.append({
            "gene_id": uid,
            "name": entry.get("name", ""),
            "symbol": entry.get("nomenclaturesymbol", entry.get("name", "")),
            "description": entry.get("description", ""),
            "chromosome": entry.get("chromosome", ""),
            "location": entry.get("maplocation", ""),
            "summary": (entry.get("summary", "") or "")[:300],
            "organism": entry.get("organism", {}).get("commonname", ""),
        })
    return json.dumps({"genes": entries}, ensure_ascii=False)


def extract_ensembl_variant(data: Any) -> str:
    """Extract key fields from Ensembl variation response."""
    if not isinstance(data, dict):
        return _fallback(data)
    return json.dumps({
        "name": data.get("name", ""),
        "var_class": data.get("var_class", ""),
        "clinical_significance": data.get("clinical_significance", []),
        "most_severe_consequence": data.get("most_severe_consequence", ""),
        "ancestral_allele": data.get("ancestral_allele", ""),
        "minor_allele": data.get("minor_allele", ""),
        "maf": data.get("MAF", ""),
        "synonyms": data.get("synonyms", [])[:5],
        "mappings": [
            {"chr": m.get("seq_region_name", ""), "start": m.get("start"), "end": m.get("end"),
             "allele_string": m.get("allele_string", "")}
            for m in data.get("mappings", [])[:3]
        ],
    }, ensure_ascii=False)


def extract_pubmed_summary(data: Any) -> str:
    """Extract key fields from PubMed esummary response."""
    if not isinstance(data, dict):
        return _fallback(data)
    result = data.get("result", data)
    uids = result.get("uids", [])
    articles = []
    for uid in uids[:5]:
        entry = result.get(str(uid), {})
        if not isinstance(entry, dict):
            continue
        authors = entry.get("authors", [])
        author_str = authors[0].get("name", "") if authors else ""
        if len(authors) > 1:
            author_str += f" et al. ({len(authors)} authors)"
        articles.append({
            "pmid": uid,
            "title": entry.get("title", ""),
            "authors": author_str,
            "journal": entry.get("fulljournalname", entry.get("source", "")),
            "year": entry.get("pubdate", "")[:4],
        })
    return json.dumps({"articles": articles}, ensure_ascii=False)


def extract_gnomad_variant(data: Any) -> str:
    """Extract key fields from gnomAD GraphQL response."""
    if not isinstance(data, dict):
        return _fallback(data)
    variant = data.get("data", {}).get("variant", {})
    if not variant:
        return _fallback(data)

    def pop_freqs(section):
        if not section:
            return {}
        pops = {}
        for p in section.get("populations", [])[:10]:
            pid = p.get("id", "")
            af = p.get("af")
            if af is not None and pid:
                pops[pid] = round(af, 6)
        return pops

    return json.dumps({
        "variant_id": variant.get("variant_id", ""),
        "rsids": variant.get("rsids", []),
        "genome_af": variant.get("genome", {}).get("af") if variant.get("genome") else None,
        "genome_populations": pop_freqs(variant.get("genome")),
        "exome_af": variant.get("exome", {}).get("af") if variant.get("exome") else None,
        "exome_populations": pop_freqs(variant.get("exome")),
    }, ensure_ascii=False)


def extract_uniprot_search(data: Any) -> str:
    """Extract key fields from UniProt search response."""
    if not isinstance(data, dict):
        return _fallback(data)
    results = data.get("results", [])
    entries = []
    for entry in results[:3]:
        genes = entry.get("genes", [{}])
        gene_name = genes[0].get("geneName", {}).get("value", "") if genes else ""
        protein = entry.get("proteinDescription", {})
        rec_name = protein.get("recommendedName", {}).get("fullName", {}).get("value", "")

        # Extract function
        function = ""
        for comment in entry.get("comments", []):
            if comment.get("commentType") == "FUNCTION":
                texts = comment.get("texts", [])
                if texts:
                    function = texts[0].get("value", "")[:200]
                break

        entries.append({
            "accession": entry.get("primaryAccession", ""),
            "gene": gene_name,
            "protein_name": rec_name,
            "function": function,
            "length": entry.get("sequence", {}).get("length", 0),
        })
    return json.dumps({"proteins": entries}, ensure_ascii=False)


def _fallback(data: Any, max_chars: int = 2000) -> str:
    """Fallback: just truncate."""
    text = json.dumps(data) if not isinstance(data, str) else data
    if len(text) > max_chars:
        return text[:max_chars] + "... [truncated]"
    return text

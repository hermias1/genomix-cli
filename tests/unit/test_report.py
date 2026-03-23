import pytest

from genomix.report import (
    _sanitize_html,
    _significance_badge,
    extract_variants_from_response,
    generate_report,
)


def test_generate_report_basic():
    variants = [
        {"gene": "BRCA1", "variant": "chr17:43094464 G>A", "type": "missense", "zygosity": "Het", "significance": "Pathogenic"},
    ]
    html = generate_report("test.vcf", variants, "<p>Test interpretation</p>", "<p>Test recs</p>")
    assert "BRCA1" in html
    assert "Pathogenic" in html
    assert "test.vcf" in html
    assert "<!DOCTYPE html>" in html


def test_significance_badge():
    assert "badge-pathogenic" in _significance_badge("Pathogenic")
    assert "badge-benign" in _significance_badge("Benign")
    assert "badge-risk" in _significance_badge("Risk_factor")


def test_significance_badge_escapes_html():
    badge = _significance_badge('<img src=x onerror="alert(1)">')
    assert "<img" not in badge
    assert "&lt;img" in badge


def test_sanitize_html_removes_dangerous_tags_and_attrs():
    sanitized = _sanitize_html(
        '<div class="recommendation" onclick="alert(1)">Safe</div>'
        '<script>alert(1)</script>'
        '<a href="javascript:alert(1)">bad</a>'
    )

    assert 'class="recommendation"' in sanitized
    assert "onclick" not in sanitized
    assert "<script" not in sanitized
    assert "alert(1)" not in sanitized
    assert "<a" not in sanitized


def test_extract_variants_from_response_accepts_wrapped_json():
    response = """Here are the variants:

```json
[
  {"gene":"BRCA1","variant":"chr17:1 A>G","type":"missense","zygosity":"Het","significance":"Pathogenic"}
]
```
"""

    variants = extract_variants_from_response(response)

    assert variants == [
        {
            "gene": "BRCA1",
            "variant": "chr17:1 A>G",
            "type": "missense",
            "zygosity": "Het",
            "significance": "Pathogenic",
        }
    ]


def test_extract_variants_from_response_rejects_non_list_payload():
    with pytest.raises(ValueError, match="No JSON array"):
        extract_variants_from_response('{"gene":"BRCA1"}')

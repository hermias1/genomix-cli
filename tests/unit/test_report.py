from genomix.report import generate_report, _significance_badge


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

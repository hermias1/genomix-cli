from genomix.runtime import iteration_budget_for


def test_iteration_budget_defaults_to_interactive_baseline():
    assert iteration_budget_for("hello") == 12


def test_iteration_budget_raises_for_vcf_interpretation():
    budget = iteration_budget_for(
        "Read raw_variants.vcf and identify the genes and clinical significance of each variant"
    )
    assert budget == 24


def test_iteration_budget_raises_for_research_skill():
    assert iteration_budget_for("/search BRCA1 pathogenic", skill_path="exploration/database-search") == 24

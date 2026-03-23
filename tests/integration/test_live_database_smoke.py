import os

import pytest

from mcp_servers.base_database import BaseDatabaseServer


def _live_smoke_enabled() -> bool:
    return os.environ.get("GENOMIX_RUN_LIVE_SMOKE") == "1"


@pytest.mark.skipif(
    not _live_smoke_enabled(),
    reason="set GENOMIX_RUN_LIVE_SMOKE=1 to run live database smoke tests",
)
def test_ncbi_live_smoke():
    server = BaseDatabaseServer(
        name="ncbi",
        base_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
    )

    result = server.get(
        "esearch.fcgi",
        {
            "db": "gene",
            "term": "BRCA1[gene] AND human[orgn]",
            "retmax": 1,
            "retmode": "json",
        },
        use_cache=False,
    )

    assert isinstance(result, dict)
    assert result["esearchresult"]["idlist"]


@pytest.mark.skipif(
    not _live_smoke_enabled(),
    reason="set GENOMIX_RUN_LIVE_SMOKE=1 to run live database smoke tests",
)
def test_ensembl_live_smoke():
    server = BaseDatabaseServer(
        name="ensembl",
        base_url="https://rest.ensembl.org",
    )

    result = server.get(
        "xrefs/symbol/homo_sapiens/TP53",
        {"content-type": "application/json"},
        use_cache=False,
    )

    assert isinstance(result, list)
    assert result

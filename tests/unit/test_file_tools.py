import gzip

from genomix.tools.file_tools import read_file


def test_read_file_truncates_large_plain_text_file(tmp_path):
    path = tmp_path / "sample.vcf"
    path.write_text("".join(f"line-{i}\n" for i in range(250)), encoding="utf-8")

    result = read_file({"path": str(path)})

    assert "(showing first 200 lines)" in result
    assert "line-0" in result
    assert "line-199" in result
    assert "line-200" not in result


def test_read_file_supports_gzip_preview(tmp_path):
    path = tmp_path / "sample.fastq.gz"
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        handle.write("@read1\nACGT\n+\n!!!!\n")

    result = read_file({"path": str(path)})

    assert "@read1" in result
    assert "ACGT" in result


def test_read_file_truncates_very_long_line(tmp_path):
    path = tmp_path / "huge.fasta"
    path.write_text("A" * 60000, encoding="utf-8")

    result = read_file({"path": str(path)})

    assert "(showing first 1 lines, truncated at 50000 chars)" in result
    assert len(result) < 52000

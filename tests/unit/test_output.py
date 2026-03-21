from genomix.output import output_path_for

def test_output_path_align():
    path = output_path_for("/align", "data/raw/sample1_R1.fastq.gz", "/proj")
    assert "sample1_R1.sorted.bam" in path
    assert "data/processed" in path

def test_output_path_override():
    path = output_path_for("/align", "x.fastq", "/proj", override="/custom/out.bam")
    assert path == "/custom/out.bam"

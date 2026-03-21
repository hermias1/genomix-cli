from genomix.errors import classify_error, GenomixErrorClass

def test_classify_missing_tool():
    err = classify_error("FileNotFoundError: No such file or directory: 'bwa'")
    assert err.error_class == GenomixErrorClass.MISSING_TOOL

def test_classify_bad_input():
    err = classify_error("truncated file: data/corrupt.fastq")
    assert err.error_class == GenomixErrorClass.BAD_INPUT

def test_classify_resource():
    err = classify_error("java.lang.OutOfMemoryError: Java heap space")
    assert err.error_class == GenomixErrorClass.RESOURCE_EXHAUSTION

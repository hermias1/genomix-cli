"""Error classification for bioinformatics tool failures."""
import re
from dataclasses import dataclass
from enum import Enum


class GenomixErrorClass(str, Enum):
    BAD_INPUT = "bad_input"
    MISSING_TOOL = "missing_tool"
    MISSING_INDEX = "missing_index"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    TOOL_CRASH = "tool_crash"
    API_FAILURE = "api_failure"
    UNKNOWN = "unknown"


@dataclass
class ClassifiedError:
    error_class: GenomixErrorClass
    message: str
    suggestion: str


PATTERNS = [
    (r"No such file or directory.*(?:bwa|samtools|gatk|blastn|fastqc)", GenomixErrorClass.MISSING_TOOL, "Run 'genomix setup' to install missing tools."),
    (r"(?:truncated|corrupt|invalid|malformed).*(?:fastq|fasta|bam|vcf)", GenomixErrorClass.BAD_INPUT, "Check the input file — it may be corrupted or in the wrong format."),
    (r"(?:No index|\.bai|\.fai|\.idx).*not found", GenomixErrorClass.MISSING_INDEX, "Generating the missing index automatically..."),
    (r"(?:OutOfMemory|oom|Cannot allocate|disk full|No space left)", GenomixErrorClass.RESOURCE_EXHAUSTION, "Try a smaller region or increase available memory."),
    (r"(?:Segmentation fault|core dumped|SIGKILL|SIGSEGV)", GenomixErrorClass.TOOL_CRASH, "The tool crashed. Try updating it or use an alternative."),
    (r"(?:rate limit|429|timeout|ConnectionError|HTTPError)", GenomixErrorClass.API_FAILURE, "API request failed. Retrying with backoff..."),
]

def classify_error(error_text):
    for pattern, cls, suggestion in PATTERNS:
        if re.search(pattern, error_text, re.IGNORECASE):
            return ClassifiedError(error_class=cls, message=error_text, suggestion=suggestion)
    return ClassifiedError(error_class=GenomixErrorClass.UNKNOWN, message=error_text, suggestion="Check the error message above.")

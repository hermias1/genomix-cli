---
name: quality-control
description: Interpret FastQC reports, apply trimming decisions, and enforce Q30 thresholds for sequencing data
version: 1.0.0
author: genomix-cli
license: Apache-2.0
metadata:
  genomix:
    tags: [sequencing, qc, fastqc, trimming, quality]
    tools_used: [run_command, read_file]
---

# Quality Control for Sequencing Data

## FastQC Interpretation

FastQC produces per-base quality scores, GC content distribution, adapter content, and duplication rates. Each module is flagged pass/warn/fail.

Key modules to check:
- **Per Base Sequence Quality**: Boxes should stay above Q28. Warn if median drops below Q28 in last 5 bases; fail if below Q20.
- **Per Sequence Quality Scores**: The peak should sit at Q30 or higher. A broad distribution or peak below Q28 indicates a poor run.
- **Per Base GC Content**: Should follow a smooth bell curve matching the expected GC of the organism. Spikes or bimodal shapes suggest contamination or adapter read-through.
- **Sequence Duplication Levels**: >30% duplication is expected for amplicon or low-input libraries; for whole-genome it warrants investigation.
- **Adapter Content**: Any adapter signal above 1% at the 3' end means trimming is required.

## Q30 Thresholds

Q30 means a 1-in-1000 error probability. Standard thresholds:
- **Whole-genome sequencing (WGS)**: >80% bases at Q30 is acceptable; >85% is good.
- **Clinical / diagnostic**: >90% Q30 required.
- **RNA-seq**: >75% Q30 acceptable; adapter content is typically more concerning than base quality.

If Q30 falls below threshold, flag the sample and check: flow cell tile failures, low cluster density, or chemistry issues.

## When to Trim

Trim when:
1. Adapter content exceeds 1% at any position (use Trimmomatic or fastp with the correct adapter sequences).
2. Per-base quality drops below Q20 in the last 10 bases (quality trimming with a sliding window).
3. Leading or trailing bases are below Q3 (leading/trailing trim).

Do NOT trim when:
- All FastQC modules pass and adapter content is <0.1%.
- The aligner handles soft-clipping (e.g., BWA-MEM); aggressive trimming can reduce sensitivity.

## Recommended Command (fastp)

```bash
fastp \
  --in1 sample_R1.fastq.gz --in2 sample_R2.fastq.gz \
  --out1 sample_R1_trimmed.fastq.gz --out2 sample_R2_trimmed.fastq.gz \
  --qualified_quality_phred 20 \
  --unqualified_percent_limit 40 \
  --detect_adapter_for_pe \
  --thread 8 \
  --json sample_fastp.json \
  --html sample_fastp.html
```

Always retain the HTML/JSON reports for audit trail. After trimming, re-run FastQC to confirm improvement.

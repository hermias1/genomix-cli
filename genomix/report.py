"""Clinical report generator — renders variant analysis as HTML."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from html.parser import HTMLParser
from html import escape as html_escape
from pathlib import Path
from typing import Any

VARIANT_FIELDS = ("gene", "variant", "type", "zygosity", "significance")
ALLOWED_HTML_TAGS = {
    "p", "strong", "em", "ul", "ol", "li", "div", "br", "span",
    "h1", "h2", "h3", "h4", "h5", "h6",
}
VOID_HTML_TAGS = {"br"}
BLOCKED_HTML_TAGS = {"script", "style"}
ALLOWED_HTML_CLASSES = {"div": {"recommendation"}}


def _safe(text: str) -> str:
    """Escape HTML to prevent XSS from LLM output."""
    return html_escape(str(text), quote=True)


class _SafeHTMLSanitizer(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.parts: list[str] = []
        self._blocked_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in BLOCKED_HTML_TAGS:
            self._blocked_depth += 1
            return
        if self._blocked_depth or tag not in ALLOWED_HTML_TAGS:
            return

        rendered_attrs = self._render_attrs(tag, attrs)
        self.parts.append(f"<{tag}{rendered_attrs}>")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in BLOCKED_HTML_TAGS or self._blocked_depth or tag not in ALLOWED_HTML_TAGS:
            return

        rendered_attrs = self._render_attrs(tag, attrs)
        if tag in VOID_HTML_TAGS:
            self.parts.append(f"<{tag}{rendered_attrs}>")
        else:
            self.parts.append(f"<{tag}{rendered_attrs}></{tag}>")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in BLOCKED_HTML_TAGS:
            self._blocked_depth = max(0, self._blocked_depth - 1)
            return
        if self._blocked_depth or tag not in ALLOWED_HTML_TAGS or tag in VOID_HTML_TAGS:
            return
        self.parts.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        if not self._blocked_depth:
            self.parts.append(_safe(data))

    def handle_entityref(self, name: str) -> None:
        if not self._blocked_depth:
            self.parts.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        if not self._blocked_depth:
            self.parts.append(f"&#{name};")

    def handle_comment(self, data: str) -> None:
        return

    def _render_attrs(self, tag: str, attrs: list[tuple[str, str | None]]) -> str:
        allowed_classes = ALLOWED_HTML_CLASSES.get(tag, set())
        if not allowed_classes:
            return ""

        classes: list[str] = []
        for name, value in attrs:
            if name.lower() != "class" or not value:
                continue
            classes = [item for item in value.split() if item in allowed_classes]
            break

        if not classes:
            return ""
        return f' class="{_safe(" ".join(classes))}"'

    def get_html(self) -> str:
        return "".join(self.parts)


def _sanitize_html(text: str) -> str:
    """Allow only safe HTML tags in interpretation/recommendation text."""
    parser = _SafeHTMLSanitizer()
    parser.feed(text)
    parser.close()
    return parser.get_html()


def _normalize_variant_record(value: Any) -> dict[str, str] | None:
    if not isinstance(value, dict):
        return None

    normalized: dict[str, str] = {}
    for field in VARIANT_FIELDS:
        default = "Unknown" if field in {"gene", "significance"} else ""
        raw = value.get(field, default)
        if raw is None:
            raw = default
        elif isinstance(raw, (dict, list)):
            raw = json.dumps(raw, ensure_ascii=False)
        else:
            raw = str(raw)
        normalized[field] = raw.strip() or default

    if not (normalized["gene"] != "Unknown" or normalized["variant"]):
        return None
    return normalized


def extract_variants_from_response(response: str) -> list[dict[str, str]]:
    """Extract and validate the first JSON array of variant records from model output."""
    decoder = json.JSONDecoder()
    for index, char in enumerate(response):
        if char != "[":
            continue
        try:
            payload, _ = decoder.raw_decode(response[index:])
        except json.JSONDecodeError:
            continue

        if not isinstance(payload, list):
            continue

        variants = [
            normalized
            for item in payload
            if (normalized := _normalize_variant_record(item)) is not None
        ]
        if not variants:
            raise ValueError("JSON array did not contain any valid variant records")
        return variants

    raise ValueError("No JSON array found in response")


REPORT_HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Genomix Clinical Report — {title}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #1a1a2e; background: #f8f9fa; padding: 2rem; max-width: 900px; margin: 0 auto; }}
  .header {{ background: linear-gradient(135deg, #0d7377, #14919b); color: white; padding: 2rem; border-radius: 12px; margin-bottom: 2rem; }}
  .header h1 {{ font-size: 1.8rem; margin-bottom: 0.5rem; }}
  .header .subtitle {{ opacity: 0.85; font-size: 0.95rem; }}
  .meta {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 2rem; }}
  .meta-card {{ background: white; padding: 1.2rem; border-radius: 8px; border: 1px solid #e0e0e0; }}
  .meta-card h3 {{ color: #0d7377; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem; }}
  .section {{ background: white; padding: 1.5rem; border-radius: 8px; border: 1px solid #e0e0e0; margin-bottom: 1.5rem; }}
  .section h2 {{ color: #0d7377; font-size: 1.2rem; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 2px solid #e8f4f4; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
  th {{ background: #f0f7f7; color: #0d7377; text-align: left; padding: 0.7rem; font-weight: 600; }}
  td {{ padding: 0.7rem; border-bottom: 1px solid #eee; }}
  tr:hover {{ background: #f8fffe; }}
  .pathogenic {{ color: #d32f2f; font-weight: 600; }}
  .likely-pathogenic {{ color: #e64a19; font-weight: 600; }}
  .vus {{ color: #f57c00; }}
  .benign {{ color: #388e3c; }}
  .risk-factor {{ color: #7b1fa2; font-weight: 600; }}
  .badge {{ display: inline-block; padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.8rem; font-weight: 600; }}
  .badge-pathogenic {{ background: #ffebee; color: #c62828; }}
  .badge-likely {{ background: #fff3e0; color: #e65100; }}
  .badge-vus {{ background: #fff8e1; color: #f57f17; }}
  .badge-benign {{ background: #e8f5e9; color: #2e7d32; }}
  .badge-risk {{ background: #f3e5f5; color: #6a1b9a; }}
  .recommendation {{ background: #e8f4f4; padding: 1rem; border-radius: 6px; border-left: 4px solid #0d7377; margin-top: 0.5rem; }}
  .footer {{ text-align: center; color: #999; font-size: 0.8rem; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #eee; }}
  .gene-name {{ font-weight: 700; color: #1565c0; }}
</style>
</head>
<body>
<div class="header">
  <h1>Genomix Clinical Variant Report</h1>
  <div class="subtitle">{title}</div>
</div>

<div class="meta">
  <div class="meta-card">
    <h3>Sample Information</h3>
    <p><strong>File:</strong> {filename}</p>
    <p><strong>Reference:</strong> {reference}</p>
    <p><strong>Total variants:</strong> {total_variants}</p>
  </div>
  <div class="meta-card">
    <h3>Report Details</h3>
    <p><strong>Generated:</strong> {date}</p>
    <p><strong>Tool:</strong> Genomix CLI v{version}</p>
    <p><strong>Analysis:</strong> AI-assisted variant interpretation</p>
  </div>
</div>

<div class="section">
  <h2>Variant Summary</h2>
  <table>
    <thead>
      <tr><th>Gene</th><th>Variant</th><th>Type</th><th>Zygosity</th><th>Significance</th></tr>
    </thead>
    <tbody>
      {variant_rows}
    </tbody>
  </table>
</div>

<div class="section">
  <h2>Clinical Interpretation</h2>
  {interpretation}
</div>

<div class="section">
  <h2>Recommendations</h2>
  {recommendations}
</div>

<div class="footer">
  <p>Generated by Genomix CLI — AI-powered genome analysis</p>
  <p>This report is for research purposes only. Clinical decisions should involve qualified genetic counselors.</p>
</div>
</body>
</html>'''


def _significance_badge(sig: str) -> str:
    """Convert significance to styled HTML badge."""
    sig_lower = sig.lower().replace("_", " ").replace("-", " ")
    safe_sig = _safe(sig)
    if "pathogenic" == sig_lower:
        return f'<span class="badge badge-pathogenic">{safe_sig}</span>'
    elif "likely pathogenic" in sig_lower:
        return f'<span class="badge badge-likely">{safe_sig}</span>'
    elif "vus" in sig_lower or "uncertain" in sig_lower:
        return f'<span class="badge badge-vus">{safe_sig}</span>'
    elif "benign" in sig_lower:
        return f'<span class="badge badge-benign">{safe_sig}</span>'
    elif "risk" in sig_lower:
        return f'<span class="badge badge-risk">{safe_sig}</span>'
    return f'<span class="badge">{safe_sig}</span>'


def generate_report(
    filename: str,
    variants: list[dict[str, str]],
    interpretation: str,
    recommendations: str,
    reference: str = "GRCh38",
    title: str = "",
) -> str:
    """Generate an HTML clinical report from structured variant data.

    Args:
        filename: Source VCF filename
        variants: List of dicts with keys: gene, variant, type, zygosity, significance
        interpretation: HTML string of clinical interpretation
        recommendations: HTML string of recommendations
        reference: Reference genome
        title: Report title

    Returns:
        Complete HTML string
    """
    from genomix import __version__

    if not title:
        title = f"Variant Analysis — {Path(filename).stem}"

    variant_rows = ""
    for v in variants:
        sig_badge = _significance_badge(v.get("significance", "Unknown"))
        variant_rows += f"""      <tr>
        <td class="gene-name">{_safe(v.get('gene', 'Unknown'))}</td>
        <td>{_safe(v.get('variant', ''))}</td>
        <td>{_safe(v.get('type', ''))}</td>
        <td>{_safe(v.get('zygosity', ''))}</td>
        <td>{sig_badge}</td>
      </tr>\n"""

    interpretation = _sanitize_html(interpretation)
    recommendations = _sanitize_html(recommendations)

    html = REPORT_HTML_TEMPLATE.format(
        title=_safe(title),
        filename=_safe(filename),
        reference=_safe(reference),
        total_variants=len(variants),
        date=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        version=__version__,
        variant_rows=variant_rows,
        interpretation=interpretation,
        recommendations=recommendations,
    )
    return html


def save_report(html: str, output_path: Path) -> Path:
    """Save HTML report to file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path

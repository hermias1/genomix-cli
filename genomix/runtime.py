"""Runtime helpers shared across CLI and TUI."""

from __future__ import annotations

from pathlib import Path

from genomix.tools.file_tools import register_file_tools
from genomix.tools.registry import ToolRegistry


LOCAL_PROVIDER_NAMES = {"ollama", "opencode"}
RESEARCH_SKILLS = {
    "exploration/database-search",
    "exploration/variant-explain",
    "comparative/blast-analysis",
}
RESEARCH_HINTS = {
    ".vcf",
    ".bam",
    ".sam",
    ".cram",
    ".fasta",
    ".fastq",
    "clinical significance",
    "pathogenic",
    "genes",
    "variants",
    "variant",
    "annotate",
    "interpret",
    "identify",
    "explain",
}


def is_local_provider(name: str) -> bool:
    return name in LOCAL_PROVIDER_NAMES


def get_skill_dirs() -> list[Path]:
    package_root = Path(__file__).resolve().parent
    candidates = [
        package_root / "builtin_skills",
        package_root.parent / "skills",
    ]
    return [path for path in candidates if path.exists()]


def iteration_budget_for(message: str, skill_path: str | None = None) -> int:
    """Choose a higher tool-use budget for research-heavy prompts."""
    baseline = 12
    high_budget = 24

    if skill_path in RESEARCH_SKILLS:
        return high_budget

    text = message.lower()
    if any(hint in text for hint in RESEARCH_HINTS):
        return high_budget

    return baseline


def build_tool_registry(auto_connect_mcp: bool = False) -> tuple[ToolRegistry, object | None]:
    registry = ToolRegistry()
    register_file_tools(registry)

    if not auto_connect_mcp:
        return registry, None

    from genomix.tools.mcp_manager import MCPManager

    manager = MCPManager()
    manager.connect_all_available(registry)
    return registry, manager

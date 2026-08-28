"""Install /learn skills and the learn protocol. Does not init gobs."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from gobs_learn.constants import (
    AGENTS_NAME,
    DOMAIN_SKILL,
    LEARN_DIR,
    LEARN_SKILL,
    PROTOCOL_BEGIN,
    PROTOCOL_END,
)


def _template_file(*parts: str) -> str:
    try:
        return files("gobs_learn.templates").joinpath(*parts).read_text(encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError, TypeError):
        root = Path(__file__).resolve().parent / "templates"
        return root.joinpath(*parts).read_text(encoding="utf-8")


def upsert_protocol_block(existing: str, block: str) -> str:
    block = block.strip() + "\n"
    start = existing.find(PROTOCOL_BEGIN)
    end = existing.find(PROTOCOL_END)
    if start != -1 and end != -1 and end > start:
        end += len(PROTOCOL_END)
        return existing[:start].rstrip() + "\n\n" + block + existing[end:].lstrip("\n")
    if existing.strip():
        return existing.rstrip() + "\n\n" + block
    return block


def _install_skill(vault: Path, name: str) -> str:
    dest_dir = vault / ".grok" / "skills" / name
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "SKILL.md"
    text = _template_file("skills", name, "SKILL.md")
    existed = dest.exists()
    dest.write_text(text, encoding="utf-8")
    return "updated" if existed else "created"


def init_learn(vault: Path) -> dict[str, str]:
    """Add learn skills and protocol. Never deletes notes or gobs files."""
    vault = vault.expanduser().resolve()
    vault.mkdir(parents=True, exist_ok=True)
    actions: dict[str, str] = {}

    protocol = _template_file("learn_protocol.md")
    agents = vault / AGENTS_NAME
    if agents.exists():
        before = agents.read_text(encoding="utf-8")
        after = upsert_protocol_block(before, protocol)
        if after != before:
            agents.write_text(after, encoding="utf-8")
            actions[AGENTS_NAME] = "updated"
        else:
            actions[AGENTS_NAME] = "skipped"
    else:
        agents.write_text(protocol.strip() + "\n", encoding="utf-8")
        actions[AGENTS_NAME] = "created"

    actions[f".grok/skills/{LEARN_SKILL}/SKILL.md"] = _install_skill(vault, LEARN_SKILL)
    actions[f".grok/skills/{DOMAIN_SKILL}/SKILL.md"] = _install_skill(vault, DOMAIN_SKILL)

    folder = vault / LEARN_DIR
    if not folder.exists():
        folder.mkdir(parents=True, exist_ok=True)
        keep = folder / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")
        actions[LEARN_DIR] = "created"
    else:
        actions[LEARN_DIR] = "skipped"

    return actions

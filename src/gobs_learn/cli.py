"""gobs-learn CLI: start / save / status / init. Launch goes through gobs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from gobs.launch import LaunchError, launch
from gobs.save import SaveError
from gobs.sessions import listed_gobs_sessions, new_or_updated, pick_session, snapshot

from gobs_learn import __version__
from gobs_learn.init_cmd import init_learn
from gobs_learn.learn import (
    LearnError,
    bind_session,
    boot_prompt,
    create_domain,
    format_status,
    list_domains,
    parse_card,
    resolve_learn_vault,
    save_learn,
)


COMMANDS = {"init", "start", "save", "status"}


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gobs-learn",
        description="L0→L1 coaching for a gobs Obsidian vault.",
    )
    p.add_argument("-V", "--version", action="version", version=f"gobs-learn {__version__}")
    sub = p.add_subparsers(dest="command")

    init_p = sub.add_parser("init", help="Install /learn skills into a vault")
    init_p.add_argument("vault", nargs="?", help="Vault path (default: current directory)")

    start_p = sub.add_parser("start", help="Open or create a domain card, then launch via gobs")
    start_p.add_argument("name", help="Domain name, e.g. Transformer")
    start_p.add_argument("--vault", help="Vault path")
    start_p.add_argument("--cli", help="CLI to spawn")
    start_p.add_argument("--no-open", action="store_true")
    start_p.add_argument("--no-launch", action="store_true", help="Only create/print the card")
    start_p.add_argument("--new", action="store_true", help="Force a new chat session")
    start_p.add_argument("-r", "--resume", metavar="ID", help="Resume this session")

    stat_p = sub.add_parser("status", help="List domain cards")
    stat_p.add_argument("--vault", help="Vault path")

    save_p = sub.add_parser("save", help="Archive a lecture and write the domain card")
    save_p.add_argument("--note", required=True, help="Vault-relative domain card path")
    save_p.add_argument("--body-file", required=True, help="Full updated domain card")
    save_p.add_argument("--chat-file", required=True, help="Readable lecture markdown")
    save_p.add_argument("--title", help="Short title used in the lecture filename")
    save_p.add_argument("--vault", help="Vault path")
    return p


def _pick_session(
    vault: Path,
    *,
    card_session: str,
    resume_id: str | None,
    force_new: bool,
    cli_name: str,
) -> tuple[str | None, bool]:
    if force_new:
        return None, False
    if resume_id:
        return resume_id, True
    if card_session:
        print(f"gobs-learn: card bound to session {card_session}")
        return card_session, True
    if cli_name != "grok":
        return None, False
    rows = listed_gobs_sessions(vault)
    interactive = sys.stdin.isatty() and sys.stdout.isatty()
    if not interactive or not rows:
        return None, False
    print("gobs-learn: pick a prior session to continue under coach mode, or n for new")
    picked = pick_session(rows)
    if picked:
        return picked, True
    return None, False


def _cmd_save(ns: argparse.Namespace) -> int:
    body = Path(ns.body_file).read_text(encoding="utf-8")
    chat = Path(ns.chat_file).read_text(encoding="utf-8")
    result = save_learn(
        note=ns.note,
        body=body,
        chat=chat,
        vault=Path(ns.vault) if ns.vault else None,
        title=ns.title,
    )
    print(f"gobs-learn: wrote {result.note}")
    if result.transcript:
        print(f"gobs-learn: lecture {result.transcript} ({result.cites} paragraph links)")
    return 0


def _cmd_start(ns: argparse.Namespace) -> int:
    vault = resolve_learn_vault(Path(ns.vault) if ns.vault else None)
    rel, action = create_domain(vault, ns.name)
    print(f"gobs-learn: {action:8} {rel}")
    card = parse_card(vault / rel, vault)
    title = card.title if card else ns.name
    level = card.level if card else "L0"
    card_session = (card.session_id if card else "") or ""
    if ns.no_launch:
        return 0

    from gobs.config import load_user_config, load_vault_config

    user = load_user_config()
    cfg = load_vault_config(vault, user)
    cli_name = ns.cli or cfg.cli
    resume_id, is_resume = _pick_session(
        vault,
        card_session=card_session,
        resume_id=ns.resume,
        force_new=ns.new,
        cli_name=cli_name,
    )
    if resume_id:
        bind_session(vault, rel, resume_id)
        print(f"gobs-learn: bound session {resume_id} → {rel}")

    before = snapshot(vault) if cli_name == "grok" else {}
    note = rel.as_posix()
    code = launch(
        vault,
        cli=ns.cli,
        open_obsidian=False if ns.no_open else None,
        new_session=not is_resume,
        resume_id=resume_id,
        extra_env={"GOBS_LEARN": "1", "GOBS_LEARN_NOTE": note},
        extra_args=[boot_prompt(note, title, resume=is_resume, level=level)],
    )
    if cli_name == "grok":
        for sid in new_or_updated(vault, before):
            bind_session(vault, rel, sid)
            print(f"gobs-learn: bound session {sid} → {rel}")
        if resume_id:
            bind_session(vault, rel, resume_id)
    return code


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        parser.print_help()
        return 2
    ns = parser.parse_args(args)
    try:
        if ns.command == "init":
            target = Path(ns.vault) if ns.vault else Path.cwd()
            actions = init_learn(target)
            print(f"gobs-learn init {target.resolve()}")
            for rel, action in actions.items():
                print(f"  {action:8} {rel}")
            return 0
        if ns.command == "status":
            vault = resolve_learn_vault(Path(ns.vault) if ns.vault else None)
            print(format_status(list_domains(vault)))
            return 0
        if ns.command == "save":
            return _cmd_save(ns)
        if ns.command == "start":
            return _cmd_start(ns)
        parser.print_help()
        return 2
    except (LaunchError, FileNotFoundError, SaveError, LearnError) as exc:
        print(f"gobs-learn: {exc}", file=sys.stderr)
        return 1

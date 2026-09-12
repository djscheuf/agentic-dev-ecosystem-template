#!/usr/bin/env python3
"""Restore Cascade-style audit logging from Devin's ATIF transcript files."""

import datetime
import json
import os
import shutil
import sqlite3
import sys
from pathlib import Path


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def get_devin_data_dir() -> Path:
    home = Path.home()
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if not appdata:
            raise RuntimeError("APPDATA not set on Windows")
        return Path(appdata) / "devin" / "cli"
    return home / ".local" / "share" / "devin" / "cli"


def get_workspace_root() -> Path:
    for env in ("DEVIN_PROJECT_DIR", "CLAUDE_PROJECT_DIR"):
        val = os.environ.get(env)
        if val:
            return Path(val).resolve()

    import subprocess
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True, timeout=10,
        )
        return Path(result.stdout.strip()).resolve()
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return Path(os.getcwd()).resolve()


def find_session_id(workspace: Path, db_path: Path) -> str:
    if not db_path.exists():
        raise FileNotFoundError(f"Devin sessions database not found: {db_path}")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, working_directory
        FROM sessions
        WHERE working_directory = ? AND hidden = 0
        ORDER BY last_activity_at DESC
        LIMIT 1
        """,
        (str(workspace),),
    )
    row = cur.fetchone()
    if row:
        conn.close()
        return row[0]

    # Fallback: most-recent session for this workspace or a parent path
    cur.execute(
        """
        SELECT id, working_directory
        FROM sessions
        WHERE hidden = 0
        ORDER BY last_activity_at DESC
        LIMIT 20
        """,
    )
    ws_str = str(workspace)
    for sid, wd in cur.fetchall():
        if wd and (wd == ws_str or ws_str.startswith(wd + os.sep)):
            conn.close()
            return sid
    conn.close()
    raise RuntimeError(f"No recent Devin session found for workspace: {workspace}")


def format_message(msg):
    if msg is None:
        return ""
    if isinstance(msg, str):
        return msg
    if isinstance(msg, dict):
        content = msg.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for part in content:
                if isinstance(part, dict):
                    t = part.get("type")
                    if t == "text" and "text" in part:
                        parts.append(part["text"])
                    elif t and t in part:
                        parts.append(f"[{t}: {part[t]}]")
                elif isinstance(part, str):
                    parts.append(part)
            return "\n".join(parts)
        return json.dumps(msg, indent=2)
    return json.dumps(msg, indent=2)


def transcript_to_markdown(transcript: dict) -> str:
    session_id = transcript.get("session_id", "unknown")
    agent = transcript.get("agent", {})
    model = agent.get("model_name", "unknown")
    steps = transcript.get("steps", [])

    lines = [
        f"# Session {session_id}",
        "",
        f"- Model: {model}",
        f"- Steps: {len(steps)}",
        "",
    ]

    for step in steps:
        source = step.get("source", "unknown")
        ts = step.get("timestamp", "")
        step_id = step.get("step_id", "")
        content = format_message(step.get("message"))

        header = source.capitalize()
        if step_id:
            header += f" (step {step_id})"

        lines.append(f"## {header}")
        if ts:
            lines.append(f"*{ts}*")
            lines.append("")
        if content:
            lines.append(content)
        lines.append("")

    return "\n".join(lines)


def main():
    try:
        workspace = get_workspace_root()
        data_dir = get_devin_data_dir()
        sessions_db = data_dir / "sessions.db"
        transcripts_dir = data_dir / "transcripts"

        session_id = find_session_id(workspace, sessions_db)
        transcript_path = transcripts_dir / f"{session_id}.json"

        if not transcript_path.exists():
            raise FileNotFoundError(f"Transcript not found: {transcript_path}")

        with open(transcript_path, "r", encoding="utf-8") as f:
            transcript = json.load(f)

        # Build audit tree in project
        audit_root = workspace / ".audit"
        turns_dir = audit_root / "turns"
        conversations_dir = audit_root / "conversations"
        logs_dir = audit_root / "logs"
        turns_dir.mkdir(parents=True, exist_ok=True)
        conversations_dir.mkdir(parents=True, exist_ok=True)
        logs_dir.mkdir(parents=True, exist_ok=True)

        # Persist raw transcript as the "turn" artifact
        turn_dest = turns_dir / f"{session_id}.json"
        shutil.copy2(transcript_path, turn_dest)

        # Generate markdown conversation
        markdown = transcript_to_markdown(transcript)
        conversation_path = conversations_dir / f"{session_id}.md"
        with open(conversation_path, "w", encoding="utf-8") as f:
            f.write(markdown)

        # Append to rolling log
        log_path = logs_dir / "audit-logger.log"
        now = datetime.datetime.now().isoformat()
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{now}] Processed session {session_id} -> {conversation_path}\n")

        eprint(f"[audit-logger] Saved {conversation_path}")
    except Exception as exc:
        eprint(f"[audit-logger] WARNING: {exc}")

    sys.exit(0)


if __name__ == "__main__":
    main()

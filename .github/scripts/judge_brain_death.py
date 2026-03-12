import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from typing import List


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _git_output(args: List[str]) -> str:
    return subprocess.check_output(
        ["git", *args],
        text=True,
        encoding="utf-8",
        errors="replace",
    ).strip()


def _set_output(name: str, value: str) -> None:
    value = "" if value is None else str(value)
    github_output = os.getenv("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as f:
            f.write(f"{name}={value}\n")
    else:
        print(f"{name}={value}")


def _iso_utc(epoch_s: int) -> str:
    return datetime.fromtimestamp(epoch_s, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _get_last_commit_timestamp() -> int:
    raw = _git_output(["log", "-1", "--pretty=format:%ct"])
    return int(raw)


def _get_contributor_emails(*, max_emails: int) -> str:
    try:
        raw = _git_output(["log", "--pretty=format:%ae"])
    except subprocess.CalledProcessError:
        return ""

    seen = set()
    emails: List[str] = []
    for line in raw.splitlines():
        email = line.strip()
        if not email or "@" not in email:
            continue
        lowered = email.lower()
        if "noreply" in lowered:
            continue
        if lowered in seen:
            continue
        seen.add(lowered)
        emails.append(email)
        if len(emails) >= max_emails:
            break

    return ",".join(emails)


def main() -> int:
    warn_days = _env_int("WARN_DAYS", 60)
    kill_days = _env_int("KILL_DAYS", 90)
    max_emails = _env_int("MAX_EMAILS", 200)

    try:
        last_commit_ts = _get_last_commit_timestamp()
    except Exception as e:
        print(f"Failed to read last commit timestamp: {e}", file=sys.stderr)
        return 2

    now_ts = int(time.time())
    inactive_days = max(0, (now_ts - last_commit_ts) // 86400)

    should_warn = inactive_days == warn_days and inactive_days < kill_days
    should_kill = inactive_days >= kill_days

    contributor_emails = (
        _get_contributor_emails(max_emails=max_emails) if (should_warn or should_kill) else ""
    )

    _set_output("inactive_days", str(inactive_days))
    _set_output("last_commit_iso", _iso_utc(last_commit_ts))
    _set_output("should_warn", str(should_warn).lower())
    _set_output("should_kill", str(should_kill).lower())
    _set_output("dead", str(should_kill).lower())
    _set_output("contributor_emails", contributor_emails)

    print(
        "CodeWill inactivity check:",
        f"inactive_days={inactive_days}, warn_days={warn_days}, kill_days={kill_days},",
        f"should_warn={should_warn}, should_kill={should_kill}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
